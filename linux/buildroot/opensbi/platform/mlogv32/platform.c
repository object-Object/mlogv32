/*
 * SPDX-License-Identifier: BSD-2-Clause
 *
 * Copyright (c) 2019 Western Digital Corporation or its affiliates.
 */

#include "uart16550.h"

#include <sbi/riscv_asm.h>
#include <sbi/riscv_encoding.h>
#include <sbi/sbi_const.h>
#include <sbi/sbi_platform.h>

#include <sbi_utils/serial/uart8250.h>
#include <sbi_utils/timer/aclint_mtimer.h>

#define MLOGV32_MTIME_FREQ		1000
#define MLOGV32_MTIME_ADDR		0xf0000000
#define MLOGV32_MTIME_SIZE		0x8
#define MLOGV32_MTIMECMP_ADDR		0xf0000008
#define MLOGV32_MTIMECMP_SIZE		0x8

#define MLOGV32_UART0_ADDR		0xf0000010
#define MLOGV32_UART_INPUT_FREQ		10000000
#define MLOGV32_UART_BAUDRATE		38400
#define MLOGV32_UART_REG_SHIFT		2 /* stride of 4 bytes */
#define MLOGV32_UART_FIFO_CAPACITY	253

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

	return uart16550_init(
		MLOGV32_UART0_ADDR,
		MLOGV32_UART_INPUT_FREQ,
		MLOGV32_UART_BAUDRATE,
		MLOGV32_UART_REG_SHIFT,
		1,
		0,
		0,
		MLOGV32_UART_FIFO_CAPACITY
	);
}

/*
 * Platform final initialization.
 */
static int mlogv32_final_init(bool cold_boot)
{
	// delegate UART interrupts to S-mode
	csr_set(CSR_MIDELEG, MIP_MEIP);

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
