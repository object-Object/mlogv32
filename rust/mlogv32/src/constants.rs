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
