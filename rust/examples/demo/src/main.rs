#![no_std]
#![no_main]

use itoa::Buffer;
use mlogv32::graphics::*;
use mlogv32::prelude::*;
use mlogv32::register::{cycle, instret, time};

#[mlogv32::entry]
fn main() -> ! {
    let mut buf = Buffer::new();

    print_str("hello rust!");

    let cycle0 = cycle::read();
    let instret0 = instret::read();
    let time0 = time::read();

    print_str("\n\ncycle 0: ");
    print_str(buf.format(cycle0));
    print_str("\ninstret 0: ");
    print_str(buf.format(instret0));
    print_str("\ntime 0: ");
    print_str(buf.format(time0));

    draw_reset();
    draw_scale(8, 8);

    draw_clear(255, 255, 255);
    draw_col(0x000000ff);
    draw_stroke(1);

    draw_rect(12, 30, 2, 12);
    draw_rect(28, 30, 2, 12);
    draw_rect(34, 30, 2, 8);
    draw_rect(12, 12, 2, 12);
    draw_rect(18, 12, 2, 12);
    draw_rect(28, 12, 2, 12);
    draw_rect(32, 12, 8, 2);

    draw_flush();

    let cycle1 = cycle::read();
    let instret1 = instret::read();
    let time1 = time::read();

    print_str("\n\ncycle 1: ");
    print_str(buf.format(cycle1));
    print_str("\ninstret 1: ");
    print_str(buf.format(instret1));
    print_str("\ntime 1: ");
    print_str(buf.format(time1));

    print_flush();

    halt()
}
