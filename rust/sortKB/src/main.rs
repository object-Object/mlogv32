#![no_std]
#![no_main]

use mlogv32::constants::DrawPrintAlignment;
use mlogv32::graphics::*;
use mlogv32::io::{print_char, read_char};
use mlogv32::prelude::*;

pub const CHAR_WIDTH: u32 = 7;
pub const CHAR_HEIGHT: u32 = 13;

entry!(main);

fn main() -> ! {
    let mut printer = DisplayPrinter::new();
    printer.clear();

    loop {
        if let Some(Ok(c)) = read_char() {
            printer.print_char(c);
            printer.flush();
            draw_flush();
        }
        sleep();
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
        draw_print(
            self.base_x + self.cur_x,
            self.base_y - self.cur_y,
            DrawPrintAlignment::TopLeft,
        );
        self.cur_x = self.next_x;
        self.cur_y = self.next_y;
    }

    fn handle_line_feed(&mut self) {
        self.next_x = 0;
        self.next_y += CHAR_HEIGHT;
    }
}
