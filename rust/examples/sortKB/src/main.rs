#![no_std]
#![no_main]

use core::hint::spin_loop;

use mlogv32::graphics::*;
use mlogv32::io::uart::{FifoControl, LineStatus};
use mlogv32::io::{get_uart0, get_uart1, print_char};
use mlogv32::prelude::*;

pub const CHAR_WIDTH: u32 = 7;
pub const CHAR_HEIGHT: u32 = 13;

entry!(main);

fn main() -> ! {
    let mut printer = DisplayPrinter::new();
    printer.clear();

    let mut uart0 = unsafe { get_uart0() };
    let mut uart1 = unsafe { get_uart1() };

    uart0.write_fifo_control(FifoControl::ENABLE | FifoControl::CLEAR_RX | FifoControl::CLEAR_TX);
    uart1.write_fifo_control(FifoControl::ENABLE | FifoControl::CLEAR_RX | FifoControl::CLEAR_TX);

    loop {
        // forward sortKB input from uart0 to uart1
        if uart0
            .read_line_status()
            .contains(LineStatus::DATA_AVAILABLE)
            && uart1.read_line_status().contains(LineStatus::THR_EMPTY)
        {
            uart1.write_byte(uart0.read_byte());
        }

        // print uart1 to display
        while uart1
            .read_line_status()
            .contains(LineStatus::DATA_AVAILABLE)
        {
            printer.print_char(uart1.read_byte() as char);
            printer.flush();
            draw_flush();
        }

        spin_loop();
    }
}

struct DisplayPrinter {
    base_x: u32,
    cur_x: u32,
    next_x: u32,

    base_y: u32,
    cur_y: u32,
    next_y: u32,
}

impl DisplayPrinter {
    pub fn new() -> Self {
        Self {
            base_x: 7,
            cur_x: 0,
            next_x: 0,

            base_y: 508,
            cur_y: 0,
            next_y: 0,
        }
    }

    pub fn clear(&mut self) {
        self.cur_x = 0;
        self.next_x = 0;
        self.cur_y = 0;
        self.next_y = 0;
        draw_reset();
        draw_clear(0, 0, 0);
        draw_col(0xffffffff);
        draw_flush();
    }

    pub fn print_str(&mut self, s: &str) {
        for c in s.chars() {
            self.print_char(c);
        }
    }

    pub fn print_char(&mut self, c: char) {
        match c {
            '\n' => {
                print_char(c);
                self.handle_line_feed();
            }

            '\t' => {
                // tab
                self.print_str("    ");
            }

            '\u{0008}' if self.next_x >= CHAR_WIDTH => {
                // backspace
                self.next_x -= CHAR_WIDTH;
                draw_col(0x000000ff);
                draw_rect(
                    self.base_x + self.next_x,
                    self.base_y - self.next_y - CHAR_HEIGHT - 3,
                    CHAR_WIDTH,
                    CHAR_HEIGHT,
                );
                draw_col(0xffffffff);
            }

            _ if c.is_control() => {}

            _ => {
                // printable character, hopefully
                self.next_x += CHAR_WIDTH;
                if self.next_x > 497 {
                    print_char('\n');
                    self.handle_line_feed();
                }
                print_char(c);
            }
        }
    }

    pub fn flush(&mut self) {
        draw_print(self.base_x + self.cur_x, self.base_y - self.cur_y);
        self.cur_x = self.next_x;
        self.cur_y = self.next_y;
    }

    fn handle_line_feed(&mut self) {
        self.next_x = 0;
        self.next_y += CHAR_HEIGHT;
    }
}
