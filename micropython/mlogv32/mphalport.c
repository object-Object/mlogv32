#include "py/mpconfig.h"
#include "uart.h"

static void send_char(char c) {
    while (*UART0_STATUS & UART_STATUS_TX_FULL) {}
    *UART0_TX = c;
}

// Receive single character, blocking until one is available.
int mp_hal_stdin_rx_chr(void) {
    while (!(*UART0_STATUS & UART_STATUS_RX_DATA)) {}
    return *UART0_RX;
}

// Send the string of given length.
void mp_hal_stdout_tx_strn(const char *str, mp_uint_t len) {
    for (mp_uint_t i = 0; i < len; i++) {
        send_char(str[i]);
    }
}
