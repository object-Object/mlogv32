/*
 * SPDX-License-Identifier: BSD-2-Clause
 *
 * Copyright (c) 2019 Western Digital Corporation or its affiliates.
 *
 * Authors:
 *   Anup Patel <anup.patel@wdc.com>
 */

#include "uart16550.h"

#include <sbi/riscv_asm.h>
#include <sbi/riscv_io.h>
#include <sbi/sbi_console.h>
#include <sbi/sbi_domain.h>

/* clang-format off */

#define UART_RBR_OFFSET		0	/* In:  Recieve Buffer Register */
#define UART_THR_OFFSET		0	/* Out: Transmitter Holding Register */
#define UART_DLL_OFFSET		0	/* Out: Divisor Latch Low */
#define UART_IER_OFFSET		1	/* I/O: Interrupt Enable Register */
#define UART_DLM_OFFSET		1	/* Out: Divisor Latch High */
#define UART_FCR_OFFSET		2	/* Out: FIFO Control Register */
#define UART_IIR_OFFSET		2	/* I/O: Interrupt Identification Register */
#define UART_LCR_OFFSET		3	/* Out: Line Control Register */
#define UART_MCR_OFFSET		4	/* Out: Modem Control Register */
#define UART_LSR_OFFSET		5	/* In:  Line Status Register */
#define UART_MSR_OFFSET		6	/* In:  Modem Status Register */
#define UART_SCR_OFFSET		7	/* I/O: Scratch Register */
#define UART_MDR1_OFFSET	8	/* I/O:  Mode Register */

#define UART_LSR_FIFOE		0x80	/* Fifo error */
#define UART_LSR_TEMT		0x40	/* Transmitter empty */
#define UART_LSR_THRE		0x20	/* Transmit-hold-register empty */
#define UART_LSR_BI		0x10	/* Break interrupt indicator */
#define UART_LSR_FE		0x08	/* Frame error indicator */
#define UART_LSR_PE		0x04	/* Parity error indicator */
#define UART_LSR_OE		0x02	/* Overrun error indicator */
#define UART_LSR_DR		0x01	/* Receiver data ready */
#define UART_LSR_BRK_ERROR_BITS	0x1E	/* BI, FE, PE, OE bits */

/* The XScale PXA UARTs define these bits */
#define UART_IER_DMAE		0x80	/* DMA Requests Enable */
#define UART_IER_UUE		0x40	/* UART Unit Enable */
#define UART_IER_NRZE		0x20	/* NRZ coding Enable */
#define UART_IER_RTOIE		0x10	/* Receiver Time Out Interrupt Enable */

/* clang-format on */

static volatile char *uart16550_base;
static u32 uart16550_in_freq;
static u32 uart16550_baudrate;
static u32 uart16550_reg_width;
static u32 uart16550_reg_shift;
static u32 uart16550_fifo_capacity;
static u32 uart16550_fifo_size;

static u32 get_reg(u32 num)
{
	u32 offset = num << uart16550_reg_shift;

	if (uart16550_reg_width == 1)
		return readb(uart16550_base + offset);
	else if (uart16550_reg_width == 2)
		return readw(uart16550_base + offset);
	else
		return readl(uart16550_base + offset);
}

static void set_reg(u32 num, u32 val)
{
	u32 offset = num << uart16550_reg_shift;

	if (uart16550_reg_width == 1)
		writeb(val, uart16550_base + offset);
	else if (uart16550_reg_width == 2)
		writew(val, uart16550_base + offset);
	else
		writel(val, uart16550_base + offset);
}

static void uart16550_putc(char ch)
{
	if (uart16550_fifo_size >= uart16550_fifo_capacity) {
		while ((get_reg(UART_LSR_OFFSET) & UART_LSR_THRE) == 0) {
			asm volatile ("pause");
		}
		uart16550_fifo_size = 0;
	}

	uart16550_fifo_size++;
	set_reg(UART_THR_OFFSET, ch);
}

static int uart16550_getc(void)
{
	if (get_reg(UART_LSR_OFFSET) & UART_LSR_DR)
		return get_reg(UART_RBR_OFFSET);
	return -1;
}

static struct sbi_console_device uart16550_console = {
	.name = "uart16550",
	.console_putc = uart16550_putc,
	.console_getc = uart16550_getc
};

int uart16550_init(unsigned long base, u32 in_freq, u32 baudrate, u32 reg_shift,
		  u32 reg_width, u32 reg_offset, u32 caps, u32 fifo_capacity)
{
	u16 bdiv = 0;

	uart16550_base      = (volatile char *)base + reg_offset;
	uart16550_reg_shift = reg_shift;
	uart16550_reg_width = reg_width;
	uart16550_in_freq   = in_freq;
	uart16550_baudrate  = baudrate;

	uart16550_fifo_capacity = fifo_capacity;
	uart16550_fifo_size 	= 0;

	if (uart16550_baudrate) {
		bdiv = (uart16550_in_freq + 8 * uart16550_baudrate) /
		       (16 * uart16550_baudrate);
	}

	/* Disable all interrupts */
	set_reg(UART_IER_OFFSET, (caps & UART_CAP_UUE) ?
				 UART_IER_UUE : 0x00);
	/* Enable DLAB */
	set_reg(UART_LCR_OFFSET, 0x80);

	if (bdiv) {
		/* Set divisor low byte */
		set_reg(UART_DLL_OFFSET, bdiv & 0xff);
		/* Set divisor high byte */
		set_reg(UART_DLM_OFFSET, (bdiv >> 8) & 0xff);
	}

	/* 8 bits, no parity, one stop bit */
	set_reg(UART_LCR_OFFSET, 0x03);
	/* Enable FIFO */
	set_reg(UART_FCR_OFFSET, 0x01);
	/* No modem control DTR RTS */
	set_reg(UART_MCR_OFFSET, 0x00);
	/* Clear line status */
	get_reg(UART_LSR_OFFSET);
	/* Read receive buffer */
	get_reg(UART_RBR_OFFSET);
	/* Set scratchpad */
	set_reg(UART_SCR_OFFSET, 0x00);

	sbi_console_set_device(&uart16550_console);

	return sbi_domain_root_add_memrange(base, PAGE_SIZE, PAGE_SIZE,
					    (SBI_DOMAIN_MEMREGION_MMIO |
					    SBI_DOMAIN_MEMREGION_SHARED_SURW_MRW));
}
