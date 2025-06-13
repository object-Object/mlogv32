#![no_std]

use core::cell::RefCell;

use critical_section::{CriticalSection, Mutex};
use embassy_time_driver::Driver;
use embassy_time_queue_utils::Queue;
use riscv::{interrupt::Interrupt, register::mie};
use riscv_rt::core_interrupt;

use timer::{MachineTimer, MmioMachineTimer};

mod timer;

static TIMER: Mutex<RefCell<MmioMachineTimer<'static>>> =
    unsafe { Mutex::new(RefCell::new(MachineTimer::new_mmio())) };

/// # Safety
///
/// This should only be called once. Also, it enables the mtimer interrupt.
pub unsafe fn init_timer() {
    critical_section::with(|cs| {
        let mut timer = TIMER.borrow_ref_mut(cs);
        timer.write_mtime(0);
        timer.write_mtimecmp(u64::MAX);
    });

    unsafe {
        mie::set_mtimer();
    };
}

embassy_time_driver::time_driver_impl!(static DRIVER: TimeDriver = TimeDriver {
    queue: Mutex::new(RefCell::new(Queue::new())),
});

struct TimeDriver {
    queue: Mutex<RefCell<Queue>>,
}

impl TimeDriver {
    fn dispatch(&self, cs: CriticalSection, now: u64) {
        let mut queue = self.queue.borrow(cs).borrow_mut();
        let mut next = queue.next_expiration(now);
        while !self.set_alarm(cs, now, next) {
            next = queue.next_expiration(now);
        }
    }

    fn set_alarm(&self, cs: CriticalSection, now: u64, at: u64) -> bool {
        if at <= now {
            return false;
        }
        TIMER.borrow_ref_mut(cs).write_mtimecmp(at);
        true
    }
}

impl Driver for TimeDriver {
    fn now(&self) -> u64 {
        critical_section::with(|cs| TIMER.borrow_ref(cs).read_mtime())
    }

    fn schedule_wake(&self, at: u64, waker: &core::task::Waker) {
        critical_section::with(|cs| {
            let should_arm = {
                let mut queue = self.queue.borrow(cs).borrow_mut();
                queue.schedule_wake(at, waker)
            };

            if should_arm {
                self.dispatch(cs, self.now());
            }
        });
    }
}

#[core_interrupt(Interrupt::MachineTimer)]
fn machine_timer() {
    critical_section::with(|cs| {
        DRIVER.dispatch(cs, DRIVER.now());
    })
}
