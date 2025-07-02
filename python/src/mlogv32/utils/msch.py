import zlib
from enum import Enum
from typing import override

from pymsch import (
    ContentBlock,
    ProcessorConfig,
    _ByteBuffer,  # pyright: ignore[reportPrivateUsage]
)


class BEContent(Enum):
    TILE_LOGIC_DISPLAY = ContentBlock(415, 1)


class ProcessorConfigUTF8(ProcessorConfig):
    @override
    def compress(self):
        buffer = _ByteBuffer()

        buffer.writeByte(1)

        code = self.code.encode("utf-8")
        buffer.writeInt(len(code))
        buffer.data.extend(code)

        buffer.writeInt(len(self.links))
        for link in self.links:
            buffer.writeUTF(link.name)
            buffer.writeShort(link.x)
            buffer.writeShort(link.y)

        return bytearray(zlib.compress(buffer.data))
