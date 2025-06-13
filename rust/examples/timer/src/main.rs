#![no_std]
#![no_main]

use core::{cell::RefCell, hint};

use critical_section::Mutex;
use itoa::Buffer;
use mlogv32::io::{print_flush, print_str};
use riscv::{
    interrupt::{self, Interrupt},
    register::mie,
};
use riscv_rt::core_interrupt;

static TIMER: Mutex<RefCell<MmioMachineTimer<'static>>> =
    unsafe { Mutex::new(RefCell::new(MachineTimer::new_mmio_at(0xf0000000))) };

#[mlogv32::entry]
fn main() -> ! {
    critical_section::with(|cs| {
        let mut timer = TIMER.borrow_ref_mut(cs);
        timer.write_mtime(0);
        timer.write_mtimecmp(1000);
    });

    unsafe {
        interrupt::enable();
        mie::set_mtimer();
    };

    loop {
        hint::spin_loop();
    }
}

#[core_interrupt(Interrupt::MachineTimer)]
fn machine_timer() {
    critical_section::with(|cs| {
        let mut timer = TIMER.borrow_ref_mut(cs);
        let mtime = timer.read_mtime();
        timer.write_mtimecmp(mtime + 1000);

        let mut buf = Buffer::new();
        print_str(buf.format(mtime));
        print_flush();
    });
}

#[derive(derive_mmio::Mmio)]
#[repr(C)]
struct MachineTimer {
    mtime: u64,
    mtimecmp: u64,
}
