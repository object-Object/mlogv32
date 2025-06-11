use core::arch::asm;

#[cfg(feature = "alloc")]
use alloc::string::ToString;
use uart::{address::MmioAddress, Data, Uart};

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

/// # Safety
///
/// This function is unsafe because the caller must ensure that only one instance exists at a time, as it represents a physical memory-mapped peripheral.
pub unsafe fn get_uart0() -> Uart<MmioAddress, Data> {
    unsafe { Uart::new(MmioAddress::new(UART0_ADDRESS as *mut u8, 4)) }
}

/// # Safety
///
/// This function is unsafe because the caller must ensure that only one instance exists at a time, as it represents a physical memory-mapped peripheral.
pub unsafe fn get_uart1() -> Uart<MmioAddress, Data> {
    unsafe { Uart::new(MmioAddress::new(UART1_ADDRESS as *mut u8, 4)) }
}
