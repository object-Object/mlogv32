#![no_std]
#![allow(clippy::empty_loop)]
#![feature(riscv_ext_intrinsics)]

mod asm;

pub use riscv::{self, register, result as riscv_result};
pub use riscv_rt::{self, entry};

use core::{arch::riscv32::pause, panic::PanicInfo};

use io::{print_flush, print_str};

pub mod graphics;
pub mod io;
pub mod prelude;

#[cfg(feature = "panic-handler")]
#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    let message = info.message().as_str();
    let location = info.location();

    if message.is_none() && location.is_none() {
        print_str("thread panicked");
    } else {
        print_str("thread panicked:");
        if let Some(message) = message {
            print_str("\n");
            print_str(message);
        }
        if let Some(location) = location {
            print_str("\n");
            print_str(location.file());
        }
    }

    print_flush();

    halt();
}

// functions

const SYSCON: *mut u32 = 0xfffffff0 as *mut u32;

pub fn halt() -> ! {
    unsafe {
        core::ptr::write_volatile(SYSCON, 0);
        unreachable!();
    };
}

pub fn reboot() -> ! {
    unsafe {
        core::ptr::write_volatile(SYSCON, 1);
        unreachable!();
    };
}

pub fn sleep_n(ticks: u32) {
    for _ in 0..ticks {
        sleep();
    }
}

pub fn sleep() {
    pause();
}
