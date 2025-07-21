#define UART_STATUS_RX_DATA  (1 << 0)
#define UART_STATUS_RX_FULL  (1 << 1)
#define UART_STATUS_TX_EMPTY (1 << 2)
#define UART_STATUS_TX_FULL  (1 << 3)
#define UART_STATUS_IRQ_ON   (1 << 4)

#define UART_CONTROL_TX_RESET (1 << 0)
#define UART_CONTROL_RX_RESET (1 << 1)
#define UART_CONTROL_IRQ_ON   (1 << 4)

#define MMIO8(Addr) ((volatile uint8_t*)(Addr))

#define UART0_BASE    0xf0000010
#define UART0_RX      MMIO8(UART0_BASE + 0x0)
#define UART0_TX      MMIO8(UART0_BASE + 0x4)
#define UART0_STATUS  MMIO8(UART0_BASE + 0x8)
#define UART0_CONTROL MMIO8(UART0_BASE + 0xc)
