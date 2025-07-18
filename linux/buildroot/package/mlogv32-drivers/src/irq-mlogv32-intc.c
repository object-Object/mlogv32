#define pr_fmt(fmt) "mlogv32-intc: " fmt

#include <asm/bug.h>
#include <asm/errno.h>
#include <asm/irq.h>
#include <linux/compiler.h>
#include <linux/cpumask.h>
#include <linux/init.h>
#include <linux/interrupt.h>
#include <linux/irq.h>
#include <linux/irqchip.h>
#include <linux/irqchip/chained_irq.h>
#include <linux/irqdesc.h>
#include <linux/irqdomain_defs.h>
#include <linux/irqdomain.h>
#include <linux/of_irq.h>
#include <linux/of.h>
#include <linux/printk.h>
#include <linux/stddef.h>
#include <linux/types.h>

static unsigned int mlogv32_intc_parent_irq;
static struct irq_domain* mlogv32_intc_domain;

static void mlogv32_intc_irq_mask(struct irq_data* d) {}

static void mlogv32_intc_irq_unmask(struct irq_data* d) {}

static void mlogv32_intc_irq_eoi(struct irq_data* d) {}

static struct irq_chip mlogv32_intc_chip = {
	.name       = "MLOGV32 INTC",
	.irq_mask   = mlogv32_intc_irq_mask,
	.irq_unmask = mlogv32_intc_irq_unmask,
	.irq_eoi    = mlogv32_intc_irq_eoi,
};

static int mlogv32_intc_domain_alloc(
	struct irq_domain* domain,
	unsigned int virq,
	unsigned int nr_irqs,
	void* arg
) {
	struct irq_fwspec* fwspec = arg;

	irq_hw_number_t hwirq;
	unsigned int type;
	int rc = irq_domain_translate_onecell(domain, fwspec, &hwirq, &type);
	if (rc) {
		return rc;
	}

	for (int i = 0; i < nr_irqs; i++) {
		irq_domain_set_info(
			domain,
			virq + i,
			hwirq + i,
			&mlogv32_intc_chip,
			NULL,
			handle_fasteoi_irq,
			NULL,
			NULL
		);
		irq_set_affinity(virq + i, cpu_possible_mask);
	}

	return 0;
}

static struct irq_domain_ops mlogv32_intc_domain_ops = {
	.translate = irq_domain_translate_onecell,
	.alloc     = mlogv32_intc_domain_alloc,
	.free      = irq_domain_free_irqs_top,
};

static void mlogv32_intc_handle_irq(struct irq_desc* desc) {
	struct irq_chip* chip = irq_desc_get_chip(desc);

	chained_irq_enter(chip, desc);

	irq_hw_number_t hwirq = irq_desc_get_irq_data(desc)->hwirq;
	int irq = irq_find_mapping(mlogv32_intc_domain, hwirq);

	if (unlikely(irq <= 0)) {
		pr_warn_ratelimited("hwirq %lu mapping not found\n", hwirq);
	} else {
		generic_handle_irq(irq);
	}

	chained_irq_exit(chip, desc);
}

static int mlogv32_intc_parse_parent_hwirq(struct device_node* node, u32* parent_hwirq) {
	struct of_phandle_args parent;
	int rc = of_irq_parse_one(node, 0, &parent);
	if (rc) {
		return rc;
	}

	*parent_hwirq = parent.args[0];

	if (!of_irq_parse_one(node, 1, &parent)) {
		pr_err("too many parent interrupts, expected 1\n");
		return -EINVAL;
	}

	return 0;
}

static int __init mlogv32_intc_init(struct device_node* node, struct device_node* parent) {
	u32 hwirq;
	int rc = mlogv32_intc_parse_parent_hwirq(node, &hwirq);
	if (rc) {
		pr_err("failed to parse parent hwirq\n");
		return rc;
	}

	// register chained IRQ handler

	struct irq_domain* parent_domain = irq_find_matching_fwnode(
		riscv_get_intc_hwnode(),
		DOMAIN_BUS_ANY
	);
	if (!parent_domain) {
		pr_err("failed to get parent irq domain\n");
		return -ENODEV;
	}

	mlogv32_intc_parent_irq = irq_create_mapping(parent_domain, hwirq);
	if (!mlogv32_intc_parent_irq) {
		pr_err("failed to create irq mapping for hwirq %d\n", hwirq);
		return -ENODEV;
	}

	irq_set_chained_handler(mlogv32_intc_parent_irq, mlogv32_intc_handle_irq);

	enable_percpu_irq(mlogv32_intc_parent_irq, irq_get_trigger_type(mlogv32_intc_parent_irq));

	// create IRQ domain

	mlogv32_intc_domain = irq_domain_create_linear(of_fwnode_handle(node), 1, &mlogv32_intc_domain_ops, NULL);
	if (!mlogv32_intc_domain) {
		pr_err("failed to create direct irq domain\n");
		return -ENOMEM;
	}

	pr_info("external interrupts connected for hwirq %d\n", hwirq);

	return 0;
}

IRQCHIP_DECLARE(mlogv32, "mlogv32,cpu-intc", mlogv32_intc_init);
