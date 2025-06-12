use core::arch::asm;

pub enum DrawImageType {
    Block,
    Unit,
    Item,
    Liquid,
}

pub const DISPLAY_WIDTH_TILES: u32 = 16;
pub const DISPLAY_HEIGHT_TILES: u32 = 16;

pub const DISPLAY_WIDTH: u32 = 32 * DISPLAY_WIDTH_TILES;
pub const DISPLAY_HEIGHT: u32 = 32 * DISPLAY_HEIGHT_TILES;

pub fn draw_clear(red: u8, green: u8, blue: u8) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 0",
            in(reg) red,
            in("a1") green,
            in("a2") blue,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_color(red: u8, green: u8, blue: u8, alpha: u8) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 1",
            in(reg) red,
            in("a1") green,
            in("a2") blue,
            in("a3") alpha,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_col(color: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 2",
            in(reg) color,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_stroke(width: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 3",
            in(reg) width,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_line(x1: u32, y1: u32, x2: u32, y2: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 4",
            in(reg) x1,
            in("a1") y1,
            in("a2") x2,
            in("a3") y2,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_rect(x: u32, y: u32, width: u32, height: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 5",
            in(reg) x,
            in("a1") y,
            in("a2") width,
            in("a3") height,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_line_rect(x: u32, y: u32, width: u32, height: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 6",
            in(reg) x,
            in("a1") y,
            in("a2") width,
            in("a3") height,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_poly(x: u32, y: u32, sides: u32, radius: u32, rotation: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 7",
            in(reg) x,
            in("a1") y,
            in("a2") sides,
            in("a3") radius,
            in("a4") rotation,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_line_poly(x: u32, y: u32, sides: u32, radius: u32, rotation: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 8",
            in(reg) x,
            in("a1") y,
            in("a2") sides,
            in("a3") radius,
            in("a4") rotation,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_triangle(x1: u32, y1: u32, x2: u32, y2: u32, x3: u32, y3: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 9",
            in(reg) x1,
            in("a1") y1,
            in("a2") x2,
            in("a3") y2,
            in("a4") x3,
            in("a5") y3,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_image(x: u32, y: u32, type_: DrawImageType, id: u32, size: u32, rotation: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 10",
            in(reg) x,
            in("a1") y,
            in("a2") type_ as u32,
            in("a3") id,
            in("a4") size,
            in("a5") rotation,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_print(x: u32, y: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 11",
            in(reg) x,
            in("a1") y,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_translate(x: u32, y: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 12",
            in(reg) x,
            in("a1") y,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_scale(x: u32, y: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 13",
            in(reg) x,
            in("a1") y,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_rotate(degrees: u32) {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, {}, 14",
            in(reg) degrees,
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_reset() {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 1, zero, zero, 15",
            options(nomem, preserves_flags, nostack),
        );
    };
}

pub fn draw_flush() {
    unsafe {
        asm!(
            ".insn i CUSTOM_0, 0, zero, zero, 3",
            options(nomem, preserves_flags, nostack),
        );
    };
}
