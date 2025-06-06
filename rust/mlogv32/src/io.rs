use core::{arch::asm, error::Error, fmt::Display};

#[cfg(feature = "alloc")]
use alloc::string::ToString;

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
            ".insn i CUSTOM_0, 0, zero, a0, 1",
            in("a0") c as u32,
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

#[derive(Debug)]
pub struct ReadCharError {
    pub value: u32,
}

impl Display for ReadCharError {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        #[cfg(feature = "alloc")]
        {
            write!(f, "received invalid char from kbconv: {}", self.value)
        }
        #[cfg(not(feature = "alloc"))]
        {
            write!(f, "received invalid char from kbconv")
        }
    }
}

impl Error for ReadCharError {}

pub fn read_char() -> Option<Result<char, ReadCharError>> {
    let value: u32;

    unsafe {
        asm!(
            ".insn i CUSTOM_0, 0, {}, zero, 4",
            out(reg) value,
            options(nomem, preserves_flags, nostack),
        );
    };

    if value == 0 {
        None
    } else {
        Some(char::from_u32(value).ok_or(ReadCharError { value }))
    }
}
