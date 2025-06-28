#include "py/mpconfig.h"
#include "py/mphal.h"
#include "uart.h"

void init(void) {
    *UART0_FCR = 0b111;
}

void deinit(void) {
    mp_hal_stdout_tx_str("Halting.");
}
