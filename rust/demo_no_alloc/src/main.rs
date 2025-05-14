#![no_std]
#![no_main]
#![allow(dead_code)]

use mlogv32::prelude::*;

entry!(main);

fn main() -> ! {
    print_str("hello rust!");
    print_flush();
    halt(0)
}
