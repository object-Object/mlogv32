
from pathlib import Path
import sys

OUTPUT_BUILDING = "bank1"
MAX_FILE_SIZE = 1000
MAX_BANK_SIZE = 512


def main():
    path = Path(sys.argv[1])
    data = path.read_bytes()
    output = []
    for i in range(0, len(data), 4):
        word = data[i : i + 4]
        number = int.from_bytes(word, byteorder="big")
        address = i // 4
        if len(output) >= MAX_FILE_SIZE or address >= MAX_BANK_SIZE:
            raise NotImplementedError(f"Address out of range: {address}")
        output.append(f"write {number} {OUTPUT_BUILDING} {address}")
    output.append("stop")
    print("\n".join(output))

if __name__ == "__main__":
    main()