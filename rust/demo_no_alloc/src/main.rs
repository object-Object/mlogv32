#![no_std]
#![no_main]

use mlogv32::graphics::*;
use mlogv32::prelude::*;

entry!(main);

fn main() -> ! {
    print_str("hello rust!");
    print_flush();

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

    halt(0)
}
