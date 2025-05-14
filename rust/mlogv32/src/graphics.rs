use core::arch::asm;

use crate::constants::{DrawImageType, DrawPrintAlignment, Syscall};

pub fn draw_clear(red: u8, green: u8, blue: u8) {
    unsafe {
        asm!(
            "ecall",
            in("a0") red,
            in("a1") green,
            in("a2") blue,
            in("a7") Syscall::DrawClear as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_color(red: u8, green: u8, blue: u8, alpha: u8) {
    unsafe {
        asm!(
            "ecall",
            in("a0") red,
            in("a1") green,
            in("a2") blue,
            in("a3") alpha,
            in("a7") Syscall::DrawColor as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_col(color: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") color,
            in("a7") Syscall::DrawCol as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_stroke(width: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") width,
            in("a7") Syscall::DrawStroke as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_line(x1: u32, y1: u32, x2: u32, y2: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x1,
            in("a1") y1,
            in("a2") x2,
            in("a3") y2,
            in("a7") Syscall::DrawLine as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_rect(x: u32, y: u32, width: u32, height: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x,
            in("a1") y,
            in("a2") width,
            in("a3") height,
            in("a7") Syscall::DrawRect as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_line_rect(x: u32, y: u32, width: u32, height: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x,
            in("a1") y,
            in("a2") width,
            in("a3") height,
            in("a7") Syscall::DrawLineRect as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_poly(x: u32, y: u32, sides: u32, radius: u32, rotation: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x,
            in("a1") y,
            in("a2") sides,
            in("a3") radius,
            in("a4") rotation,
            in("a7") Syscall::DrawPoly as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_line_poly(x: u32, y: u32, sides: u32, radius: u32, rotation: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x,
            in("a1") y,
            in("a2") sides,
            in("a3") radius,
            in("a4") rotation,
            in("a7") Syscall::DrawLinePoly as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_triangle(x1: u32, y1: u32, x2: u32, y2: u32, x3: u32, y3: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x1,
            in("a1") y1,
            in("a2") x2,
            in("a3") y2,
            in("a4") x3,
            in("a5") y3,
            in("a7") Syscall::DrawTriangle as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_image(
    mut x: u32,
    y: u32,
    type_: DrawImageType,
    id: u32,
    size: u32,
    rotation: u32,
) -> bool {
    unsafe {
        asm!(
            "ecall",
            inout("a0") x,
            in("a1") y,
            in("a2") type_ as u32,
            in("a3") id,
            in("a4") size,
            in("a5") rotation,
            in("a7") Syscall::DrawImage as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
    x != 0
}

pub fn draw_print(x: u32, y: u32, alignment: DrawPrintAlignment) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x,
            in("a1") y,
            in("a2") alignment as u32,
            in("a7") Syscall::DrawPrint as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_translate(x: u32, y: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x,
            in("a1") y,
            in("a7") Syscall::DrawTranslate as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_scale(x: u32, y: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") x,
            in("a1") y,
            in("a7") Syscall::DrawScale as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_rotate(degrees: u32) {
    unsafe {
        asm!(
            "ecall",
            in("a0") degrees,
            in("a7") Syscall::DrawRotate as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_reset() {
    unsafe {
        asm!(
            "ecall",
            in("a7") Syscall::DrawReset as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_flush() {
    unsafe {
        asm!(
            "ecall",
            in("a7") Syscall::DrawFlush as u32,
            options(nomem, preserves_flags, nostack),
        );
    };
}
