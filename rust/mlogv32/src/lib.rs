#![no_std]
#![allow(clippy::empty_loop)]
#![feature(riscv_ext_intrinsics)]

mod asm;

pub use riscv::{self, register, result as riscv_result};
pub use riscv_rt::{self, entry};

use core::arch::riscv32::pause;

#[cfg(feature = "panic-handler")]
mod panic_handler;

pub mod graphics;
pub mod io;
pub mod prelude;

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
