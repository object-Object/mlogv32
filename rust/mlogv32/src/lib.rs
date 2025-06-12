#![no_std]
#![allow(clippy::empty_loop)]
#![feature(riscv_ext_intrinsics)]

#[cfg(feature = "alloc")]
pub extern crate alloc;

pub use riscv::{register, result as riscv_result};

use core::{
    arch::{global_asm, riscv32::pause},
    panic::PanicInfo,
};
#[cfg(feature = "alloc")]
use embedded_alloc::LlffHeap as Heap;

use io::{print_flush, print_str};

pub mod constants;
pub mod graphics;
pub mod io;
pub mod prelude;

#[cfg(feature = "alloc")]
#[global_allocator]
static HEAP: Heap = Heap::empty();

// init icache and global/stack/frame pointers
#[rustfmt::skip]
global_asm!("
.section .text.start
    la t0, __etext
    .insn i CUSTOM_0, 0, zero, t0, 0

    la gp, __global_pointer$
    
    la t1, _stack_start
    andi sp, t1, -16
    add s0, sp, zero
");

#[unsafe(no_mangle)]
#[unsafe(link_section = ".text.start")]
unsafe extern "C" fn _start() -> ! {
    unsafe extern "C" {
        static mut __sbss: u8;
        static mut __ebss: u8;
        static mut __sdata: u8;
        static mut __edata: u8;
        static __sidata: u8;
    }

    #[cfg(feature = "alloc")]
    unsafe extern "C" {
        static __sheap: u8;
        static _heap_size: u8;
    }

    // zero bss
    let count = &raw const __ebss as usize - &raw const __sbss as usize;
    unsafe { core::ptr::write_bytes(&raw mut __sbss, 0, count) };

    // copy static variables
    let count = &raw const __edata as usize - &raw const __sdata as usize;
    unsafe { core::ptr::copy_nonoverlapping(&__sidata as *const u8, &raw mut __sdata, count) };

    #[cfg(feature = "alloc")]
    unsafe {
        let heap_bottom = &__sheap as *const u8 as usize;
        let heap_size = &_heap_size as *const u8 as usize;
        // not using assert here because the panic handler uses println, which needs alloc
        if heap_size == 0 {
            print_str("heap size must be greater than 0");
            halt();
        }
        HEAP.init(heap_bottom, heap_size);
    }

    unsafe extern "Rust" {
        fn main() -> !;
    }

    unsafe { main() }
}

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    let message = info.message().as_str();
    let location = info.location();

    #[cfg(feature = "alloc")]
    match (message, location) {
        (Some(message), Some(location)) => println!("thread panicked at '{message}', {location}"),
        (Some(message), None) => println!("thread panicked at '{message}'"),
        (None, Some(location)) => println!("thread panicked at {location}"),
        (None, None) => println!("thread panicked"),
    }

    #[cfg(not(feature = "alloc"))]
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

#[cfg(feature = "alloc")]
struct CriticalSection;
#[cfg(feature = "alloc")]
critical_section::set_impl!(CriticalSection);

// mlogv32 is (for now) single-threaded and doesn't support interrupts
#[cfg(feature = "alloc")]
unsafe impl critical_section::Impl for CriticalSection {
    unsafe fn acquire() -> critical_section::RawRestoreState {}
    unsafe fn release(_restore_state: critical_section::RawRestoreState) {}
}

// macros

#[macro_export]
macro_rules! entry {
    ($path:path) => {
        #[unsafe(export_name = "main")]
        pub unsafe fn __main() -> ! {
            // type check the given path
            let f: unsafe fn() -> ! = $path;
            unsafe { f() }
        }
    };
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
