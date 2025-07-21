#include "py/mpconfig.h"
#include "py/mphal.h"
#include "uart.h"

void init(void) {
    *UART0_CONTROL = UART_CONTROL_RX_RESET | UART_CONTROL_TX_RESET;
}

void deinit(void) {
    mp_hal_stdout_tx_str("Halting.");
    while (!(*UART0_STATUS & UART_STATUS_TX_EMPTY)) {}
}
