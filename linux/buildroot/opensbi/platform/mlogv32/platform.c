/*
 * SPDX-License-Identifier: BSD-2-Clause
 *
 * Copyright (c) 2019 Western Digital Corporation or its affiliates.
 */

#include <libfdt.h>

#include <sbi/riscv_asm.h>
#include <sbi/riscv_encoding.h>
#include <sbi/sbi_console.h>
#include <sbi/sbi_const.h>
#include <sbi/sbi_error.h>
#include <sbi/sbi_platform.h>
#include <sbi/sbi_timer.h>

#include <sbi_utils/fdt/fdt_fixup.h>
#include <sbi_utils/fdt/fdt_helper.h>
#include <sbi_utils/serial/xlnx_uartlite.h>
#include <sbi_utils/timer/aclint_mtimer.h>

#define MLOGV32_MTIME_FREQ		1000
#define MLOGV32_MTIME_ADDR		0xf0000000
#define MLOGV32_MTIME_SIZE		0x8
#define MLOGV32_MTIMECMP_ADDR		0xf0000008
#define MLOGV32_MTIMECMP_SIZE		0x8

#define MLOGV32_UART0_ADDR		0xf0000010

static struct aclint_mtimer_data mtimer = {
	.mtime_freq = MLOGV32_MTIME_FREQ,
	.mtime_addr = MLOGV32_MTIME_ADDR,
	.mtime_size = MLOGV32_MTIME_SIZE,
	.mtimecmp_addr = MLOGV32_MTIMECMP_ADDR,
	.mtimecmp_size = MLOGV32_MTIMECMP_SIZE,
	.first_hartid = 0,
	.hart_count = 1,
};

/*
 * Platform early initialization.
 */
static int mlogv32_early_init(bool cold_boot)
{
	if (!cold_boot)
		return 0;

	return xlnx_uartlite_init(MLOGV32_UART0_ADDR);
}

static char mlogv32_bootargs[256];

static void mlogv32_do_fixup(struct fdt_general_fixup* f, void* fdt) {
	if (!mlogv32_bootargs[0])
		return;

	int chosen_offset = fdt_path_offset(fdt, "/chosen");
	if (chosen_offset < 0)
		return;

	int err = fdt_setprop_string(fdt, chosen_offset, "bootargs", mlogv32_bootargs);
	if (err)
		sbi_printf("Failed to set bootargs: %s", fdt_strerror(err));
}

static struct fdt_general_fixup mlogv32_fixup = {
	.name = "mlogv32-fixup",
	.do_fixup = mlogv32_do_fixup,
};

static bool mlogv32_wait_for_input(void* arg) {
	return sbi_getc() >= 0;
}

static bool mlogv32_prompt_interrupt_boot(void) {
	bool retval = false;
	sbi_printf("Press any key to interrupt boot");
	for (int i = 0; i < 3; i++) {
		sbi_printf(".");
		if (sbi_timer_waitms_until(mlogv32_wait_for_input, NULL, 1000)) {
			retval = true;
			break;
		}
	}
	sbi_printf("\n");
	return retval;
}

static const char* mlogv32_get_fdt_bootargs(void* fdt) {
	int chosen_offset = fdt_path_offset(fdt, "/chosen");
	if (chosen_offset < 0)
		return NULL;

	return fdt_getprop(fdt, chosen_offset, "bootargs", NULL);
}

static void mlogv32_prompt_get_bootargs(void* fdt) {
	// drain input buffer
	while (mlogv32_wait_for_input(NULL)) {}

	const char* current_bootargs = mlogv32_get_fdt_bootargs(fdt);
	if (current_bootargs)
		sbi_printf("Bootargs: %s\n", current_bootargs);

	if (!mlogv32_prompt_interrupt_boot())
		return;

	while (mlogv32_wait_for_input(NULL)) {}

	sbi_printf("Enter new bootargs: ");

	char* retval = mlogv32_bootargs;
	int maxwidth = sizeof(mlogv32_bootargs);
	while (maxwidth > 1) {
		int ch = sbi_getc();
		if (ch <= 0)
			continue;

		// backspace
		if (ch == 127) {
			if (retval > mlogv32_bootargs) {
				sbi_puts("\b \b");
				retval--;
				maxwidth++;
			}
			continue;
		}

		sbi_putc(ch);

		if (ch == '\r' || ch == '\n') {
			break;
		}

		*retval = (char)ch;
		retval++;
		maxwidth--;
	}
	*retval = '\0';
}

/*
 * Platform final initialization.
 */
static int mlogv32_final_init(bool cold_boot)
{
	// delegate UART interrupts to S-mode
	csr_set(CSR_MIDELEG, MIP_MEIP);

	if (!cold_boot)
		return 0;

	void* fdt = fdt_get_address_rw();

	mlogv32_prompt_get_bootargs(fdt);
	sbi_printf("\n\n");

	int rc = fdt_register_general_fixup(&mlogv32_fixup);
	if (rc && rc != SBI_EALREADY)
		return rc;

	fdt_fixups(fdt);

	return 0;
}

/*
 * Initialize platform timer during cold boot.
 */
static int mlogv32_timer_init(void)
{
	/* Example if the generic ACLINT driver is used */
	return aclint_mtimer_cold_init(&mtimer, NULL);
}

/*
 * Platform descriptor.
 */
const struct sbi_platform_operations platform_ops = {
	.early_init		= mlogv32_early_init,
	.final_init		= mlogv32_final_init,
	.timer_init		= mlogv32_timer_init
};

const struct sbi_platform platform = {
	.opensbi_version	= OPENSBI_VERSION,
	.platform_version	= SBI_PLATFORM_VERSION(0x0, 0x00),
	.name			= "mlogv32",
	.features		= SBI_PLATFORM_DEFAULT_FEATURES,
	.hart_count		= 1,
	.hart_stack_size	= SBI_PLATFORM_DEFAULT_HART_STACK_SIZE,
	.heap_size		= SBI_PLATFORM_DEFAULT_HEAP_SIZE(1),
	.platform_ops_addr	= (unsigned long)&platform_ops
};
