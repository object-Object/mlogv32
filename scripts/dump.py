from pathlib import Path
import sys

RESET_SWITCH = "switch1"
OUTPUT = "message1"
MAX_FILE_SIZE = 1000
NUM_TAIL_LINES = 3  # number of lines appended to the end of each file
MEMORY_SIZE = 64  # number of banks
BANK_SIZE = 512  # number of values that can be written to each bank


def main():
    data_path = Path(sys.argv[1])
    data = data_path.read_bytes()

    output_dir = data_path.parent
    output_name = data_path.stem

    output_index = 0
    bank_index = 1
    address = 0

    output = [
        f"control enabled {RESET_SWITCH} true",
        f"printflush {OUTPUT}",
    ]

    def flush_output(is_done: bool):
        nonlocal output_index, output

        # see NUM_TAIL_LINES
        if is_done:
            n = output_index + 1
            output.append(f'print "Done! Loaded {n} file{"" if n == 1 else "s"} containing {len(data)} bytes."')
        else:
            output.append(f'print "Done file {output_name}-{output_index}.mlog. Load file {output_name}-{output_index + 1}.mlog to continue."')
        output += [
            f"printflush {OUTPUT}",
            "stop",
        ]

        assert len(output) <= MAX_FILE_SIZE, f"Invalid file size: {len(output)}"

        output_file = output_dir / f"{output_name}-{output_index}.mlog"
        output_file.write_text("\n".join(output), "utf-8")

        output_index += 1
        output.clear()
        output.append(f"printflush {OUTPUT}")
    
    for i in range(0, len(data), 4):
        word = data[i : i + 4]
        number = int.from_bytes(word, byteorder="big")
        output.append(f"write {number} bank{bank_index} {address}")
        
        if len(output) + NUM_TAIL_LINES >= MAX_FILE_SIZE:
            is_done = i + 4 >= len(data)
            flush_output(is_done=is_done)
            if is_done:
                break
        
        address += 1
        if address >= BANK_SIZE:
            address = 0
            bank_index += 1
            if bank_index > MEMORY_SIZE:
                raise ValueError("Data is too large, ran out of memory banks!")

    else:
        # we didn't break the loop, so flush the rest of the output
        flush_output(is_done=True)
    
    print(f"Generated {output_index} mlog file{'' if output_index == 1 else 's'}.")

if __name__ == "__main__":
    main()