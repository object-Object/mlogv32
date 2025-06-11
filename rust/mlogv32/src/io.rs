use core::{arch::asm, hint};

#[cfg(feature = "alloc")]
use alloc::string::ToString;
use uart::{address::MmioAddress, Data, FifoControl, LineStatus, Uart};

pub use uart;

#[cfg(feature = "alloc")]
#[macro_export]
macro_rules! println {
    () => {
        $crate::io::print_str!("")
    };
    ($arg:ident) => {{
        $crate::io::print_str($arg);
    }};
    ($($arg:tt)*) => {{
        $crate::io::_print(format_args!($($arg)*));
    }};
}

/// Internal function.
#[cfg(feature = "alloc")]
pub fn _print(msg: core::fmt::Arguments) {
    print_str(msg.to_string().as_str());
}

pub fn print_str(msg: &str) {
    for c in msg.chars() {
        print_char(c);
    }
}

pub fn print_char(c: char) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 0, zero, {}, 1",
            in(reg) c as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn print_flush() {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 0, zero, zero, 2",
            options(nomem, preserves_flags, nostack),
        );
    }
}

// TODO: create Peripherals struct?

const UART0_ADDRESS: usize = 0xf0000010;
const UART1_ADDRESS: usize = 0xf0000030;

pub enum UartAddress {
    Uart0,
    Uart1,
}

impl UartAddress {
    unsafe fn get_address(&self) -> MmioAddress {
        let base = match self {
            UartAddress::Uart0 => UART0_ADDRESS,
            UartAddress::Uart1 => UART1_ADDRESS,
        };
        MmioAddress::new(base as *mut u8, 4)
    }
}

/// # Safety
///
/// This function is unsafe because the caller must ensure that only one instance exists at a time, as it represents a physical memory-mapped peripheral.
pub unsafe fn get_uart0() -> Uart<MmioAddress, Data> {
    unsafe { Uart::new(UartAddress::Uart0.get_address()) }
}

/// # Safety
///
/// This function is unsafe because the caller must ensure that only one instance exists at a time, as it represents a physical memory-mapped peripheral.
pub unsafe fn get_uart1() -> Uart<MmioAddress, Data> {
    unsafe { Uart::new(UartAddress::Uart0.get_address()) }
}

pub struct UartPort {
    uart: Uart<MmioAddress, Data>,
    fifo_capacity: usize,
    fifo_len: usize,
}

impl UartPort {
    /// # Safety
    ///
    /// This function is unsafe because the caller must ensure that only one instance of each device exists at a time, as it represents a physical memory-mapped peripheral.
    pub unsafe fn new(device: UartAddress) -> Self {
        Self {
            uart: Uart::new(device.get_address()),
            fifo_capacity: 1,
            fifo_len: 0,
        }
    }

    /// # Safety
    ///
    /// This function is unsafe because the caller must ensure that only one instance of each device exists at a time, as it represents a physical memory-mapped peripheral. The caller must also ensure that the fifo capacity is correct.
    pub unsafe fn new_with_fifo(device: UartAddress, fifo_capacity: usize) -> Self {
        Self {
            uart: Uart::new(device.get_address()),
            fifo_capacity,
            fifo_len: 0,
        }
    }

    pub fn init(&mut self) {
        self.uart.write_fifo_control(
            FifoControl::ENABLE | FifoControl::CLEAR_RX | FifoControl::CLEAR_TX,
        );
    }

    pub fn read(&mut self, buf: &mut [u8]) -> usize {
        for (i, item) in buf.iter_mut().enumerate() {
            if let Some(byte) = self.read_byte() {
                *item = byte;
            } else {
                return i;
            }
        }
        buf.len()
    }

    pub fn read_byte(&mut self) -> Option<u8> {
        if self
            .uart
            .read_line_status()
            .contains(LineStatus::DATA_AVAILABLE)
        {
            Some(self.uart.read_byte())
        } else {
            None
        }
    }

    pub fn write(&mut self, buf: &[u8]) {
        for &byte in buf {
            self.write_byte(byte);
        }
    }

    pub fn write_byte(&mut self, byte: u8) {
        while !self.try_write_byte(byte) {
            hint::spin_loop();
        }
    }

    pub fn try_write_byte(&mut self, byte: u8) -> bool {
        if self.uart.read_line_status().contains(LineStatus::THR_EMPTY) {
            self.fifo_len = 0
        }
        if self.fifo_len < self.fifo_capacity {
            self.uart.write_byte(byte);
            self.fifo_len += 1;
            true
        } else {
            false
        }
    }
}
