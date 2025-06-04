import sys
from pathlib import Path

from pymsch import Block, Content, ProcessorConfig, ProcessorLink, Schematic, double

BANK_TYPE = Content.MEMORY_BANK
BANK_SIZE = 512  # number of values that can be written to each bank

# physical width/height limits of the memory, in units of memory banks
MEMORY_WIDTH = 8
MEMORY_HEIGHT = 8

MEMORY_WIDTH_BLOCKS = MEMORY_WIDTH * BANK_TYPE.value.size
MEMORY_HEIGHT_BLOCKS = MEMORY_HEIGHT * BANK_TYPE.value.size

GENERATE_PROCESSOR = True
PROCESSOR_TYPE = Content.WORLD_PROCESSOR
PROCESSOR_CODE_PATH = Path(__file__).parent / "../src/main.mlog"


def main(data_path: Path):
    schem = Schematic()
    schem.set_tag("name", data_path.as_posix())

    if GENERATE_PROCESSOR:
        base_x = PROCESSOR_TYPE.value.size
        base_y = 0
    else:
        base_x = 0
        base_y = 0

    processor_links = list[ProcessorLink]()

    def add_and_link_block(block: Block, name: str):
        schem.add_block(block)
        processor_links.append(ProcessorLink(block.x, block.y, name))

    data = data_path.read_bytes()
    for bank_index, bank_data in enumerate(iter_chunks(data)):
        bank_x = bank_index % MEMORY_WIDTH
        bank_y = bank_index // MEMORY_HEIGHT
        if bank_y >= MEMORY_HEIGHT:
            raise ValueError("Data is too large, ran out of space for memory banks!")

        # oops! this doesn't actually work
        add_and_link_block(
            Block(
                block=BANK_TYPE,
                x=base_x + bank_x * BANK_TYPE.value.size,
                y=base_y + bank_x * BANK_TYPE.value.size,
                config=bank_data,
                rotation=0,
            ),
            f"bank{bank_index + 1}",
        )

    if GENERATE_PROCESSOR:
        schem.add_block(
            Block(
                block=PROCESSOR_TYPE,
                x=0,
                y=0,
                config=ProcessorConfig(
                    code=PROCESSOR_CODE_PATH.read_text("utf-8"),
                    links=processor_links,
                ),
                rotation=0,
            )
        )

    output_path = data_path.with_suffix(".msch")
    schem.write_file(str(output_path))


def iter_chunks(data: bytes):
    chunk = list[double]()

    for i in range(0, len(data), 4):
        word = data[i : i + 4]
        number = int.from_bytes(word, byteorder="big")
        chunk.append(double(number))

        if len(chunk) == BANK_SIZE:
            yield chunk
            chunk = []

    if chunk:
        yield chunk


if __name__ == "__main__":
    main(Path(sys.argv[1]))
