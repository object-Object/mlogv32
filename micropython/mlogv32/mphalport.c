#include "py/mpconfig.h"
#include "uart.h"

#ifndef UART_FIFO_CAPACITY
#define UART_FIFO_CAPACITY 253
#endif

static unsigned int uart0_fifo_size = 0;

static void send_char(char c) {
    if (uart0_fifo_size >= UART_FIFO_CAPACITY) {
        while ((*UART0_LSR & 0b1100000) != 0b1100000) {}
        uart0_fifo_size = 0;
    }

    *UART0_THR = c;
    uart0_fifo_size += 1;
}

// Receive single character, blocking until one is available.
int mp_hal_stdin_rx_chr(void) {
    while (!(*UART0_LSR & 1)) {}
    return *UART0_RHR;
}

// Send the string of given length.
void mp_hal_stdout_tx_strn(const char *str, mp_uint_t len) {
    for (mp_uint_t i = 0; i < len; i++) {
        send_char(str[i]);
    }
}
