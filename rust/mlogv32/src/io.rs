use core::arch::asm;

#[cfg(feature = "alloc")]
use alloc::string::ToString;

use crate::constants::Syscall;

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
            "ecall",
            in("a0") c as u32,
            in("a7") Syscall::PrintChar as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn print_flush() {
    unsafe {
        asm!(
            "ecall",
            in("a7") Syscall::PrintFlush as u32,
            options(nomem, preserves_flags, nostack),
        );
    }
}
