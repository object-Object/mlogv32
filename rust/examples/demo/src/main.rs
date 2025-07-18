#![no_std]
#![no_main]

use mlogv32::prelude::*;
use mlogv32::register::{mcycle, minstret};
use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};

#[mlogv32::entry]
fn main() -> ! {
    let mut rng = SmallRng::seed_from_u64(0);

    let mut data = [0u8; 512];
    rng.fill(&mut data);

    sleep();
    unsafe {
        core::ptr::write_volatile(0xf0000000 as *mut u64, 0);
        mcycle::write64(0);
        minstret::write64(0);
    };

    data.sort_unstable();

    halt();
}
