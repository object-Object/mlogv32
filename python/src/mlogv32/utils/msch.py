from enum import Enum

from pymsch import ContentBlock


class BEContent(Enum):
    TILE_LOGIC_DISPLAY = ContentBlock(415, 1)
