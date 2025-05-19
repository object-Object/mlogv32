import json
import struct
from pathlib import Path
from typing import Annotated, Any

from typer import Argument, Typer

# https://github.com/Anuken/Mindustry/blob/0a046f8fa5abe4fb1797f802ce5fb7f91c330e85/core/src/mindustry/logic/GlobalVars.java#L26
CONTENT_TYPES = ["block", "unit", "item", "liquid"]

app = Typer()


@app.command()
def main(
    path: Annotated[Path, Argument()] = Path("logicids.dat"),
    out: Path = Path("logicids.json"),
):
    data = bytearray(path.read_bytes())
    output: dict[str, Any] = {ctype: [] for ctype in CONTENT_TYPES}

    # https://github.com/Anuken/Mindustry/blob/0a046f8fa5abe4fb1797f802ce5fb7f91c330e85/core/src/mindustry/logic/GlobalVars.java#L158
    for ctype in CONTENT_TYPES:
        amount = ByteUtils.pop_int(data, 2, True)
        output[f"@{ctype}Count"] = amount

        for i in range(0, amount):
            name = ByteUtils.pop_UTF(data)
            output[ctype].append(name)

    with out.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)


# copied from pymsch to add @staticmethod so typing works
class ByteUtils:
    @staticmethod
    def pop_bytes(data: bytearray, byte_count: int):
        out_bytes = bytearray()
        for i in range(byte_count):
            out_bytes.append(data.pop(0))
        return out_bytes

    @staticmethod
    def pop_int(data: bytearray, byte_count: int, signed=False):
        return int.from_bytes(ByteUtils.pop_bytes(data, byte_count), signed=signed)

    @staticmethod
    def pop_float(data: bytearray):
        return struct.unpack("f", ByteUtils.pop_bytes(data, 4))

    @staticmethod
    def pop_double(data: bytearray):
        return struct.unpack("d", ByteUtils.pop_bytes(data, 8))

    @staticmethod
    def pop_bool(data: bytearray):
        return struct.unpack("?", ByteUtils.pop_bytes(data, 1))

    @staticmethod
    def pop_UTF(data: bytearray):
        char_count = ByteUtils.pop_int(data, 2)
        return str(ByteUtils.pop_bytes(data, char_count), "UTF")


if __name__ == "__main__":
    app()
