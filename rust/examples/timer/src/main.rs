#![no_std]
#![no_main]

use core::{cell::RefCell, hint};

use critical_section::Mutex;
use itoa::Buffer;
use mlogv32::io::UartPort;
use riscv::{
    interrupt::{self, Interrupt},
    register::mie,
};
use riscv_rt::core_interrupt;

static TIMER: Mutex<RefCell<MmioMachineTimer<'static>>> =
    unsafe { Mutex::new(RefCell::new(MachineTimer::new_mmio_at(0xf0000000))) };

static UART0: Mutex<RefCell<Option<UartPort>>> = Mutex::new(RefCell::new(None));

#[mlogv32::entry]
fn main() -> ! {
    critical_section::with(|cs| {
        let mut uart0 = UART0.borrow_ref_mut(cs);
        uart0.replace(unsafe { UartPort::new_uart0(253) });

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

        let mut uart0 = UART0.borrow_ref_mut(cs);
        let uart0 = uart0.as_mut().unwrap();
        let mut buf = Buffer::new();
        uart0.blocking_write(buf.format(mtime).as_bytes());
        uart0.blocking_write(b"\n");
    });
}

#[derive(derive_mmio::Mmio)]
#[repr(C)]
struct MachineTimer {
    mtime: u64,
    mtimecmp: u64,
}
