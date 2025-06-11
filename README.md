# mlogv32

RISC-V processor in Mindustry logic. Requires Mindustry build 149+.

![image](https://github.com/user-attachments/assets/3951b4b7-cc56-494a-85f8-54bd9f2ee7d5)

## Architecture

Physical memory consists of three sections. Two are directly accessible by code: ROM (rx) and RAM (rwx). The third section is an instruction cache which is 4x less dense than main memory.

For maximum performance, the instruction cache for ROM can be initialized at boot using the MLOGSYS instruction. It is also updated whenever an instruction writes to RAM that is covered by the icache. If executing from memory not covered by the icache, the processor manually fetches and decodes the instruction from main memory.

The main CPU code is generated from `src/main.mlog.jinja` using a custom Jinja-based preprocessor (`python/src/mlogv32/preprocessor`).

## Memory

| Address      | Size         | Access Type | Name        |
| ------------ | ------------ | ----------- | ----------- |
| `0x00000000` | Configurable | R/X         | ROM         |
| `0x80000000` | Configurable | R/W/X/A\*   | RAM         |
| `0xf0000000` | `0x4`        | R/W         | `mtime`     |
| `0xf0000004` | `0x4`        | R/W         | `mtimeh`    |
| `0xf0000008` | `0x4`        | R/W         | `mtimecmp`  |
| `0xf000000c` | `0x4`        | R/W         | `mtimecmph` |
| `0xf0000010` | `0x20`       | R/W         | UART0       |
| `0xf0000030` | `0x20`       | R/W         | UART1       |
| `0xfffffff0` | `0x4`        | W           | Syscon      |

\* Atomic instructions are only supported in RAM.

Code begins executing at address `0x00000000` (ie. the start of ROM).

Addresses `0xf0000000` - `0xffffffff` are reserved for system purposes such as MMIO.

### UART

Addresses `0xf0000010` and `0xf0000030` contain emulated UART 16550 peripherals based on [this datasheet](https://caro.su/msx/ocm_de1/16550.pdf). The UARTs support the following features:

- Configurable FIFO capacity (up to 254 bytes) for TX and RX, stored as a variable in the CONFIG processor.
- Theoretical maximum transfer rate of 121920 bits/sec (254 bytes/tick).
- Line Status Register flags: Transmitter Empty, THR Empty, Overrun Error, Data Ready.

The UART registers have a stride of 4 bytes to simplify some internal logic.

| Offset | Access Type | Register                     |
| ------ | ----------- | ---------------------------- |
| `0x00` | R           | Receiver Holding Register    |
| `0x00` | W           | Transmitter Holding Register |
| `0x04` | R/W         | Interrupt Enable Register    |
| `0x08` | R           | Interrupt Status Register    |
| `0x08` | W           | FIFO Control Register        |
| `0x0c` | R/W         | Line Control Register        |
| `0x10` | R/W         | Modem Control Register       |
| `0x14` | R           | Line Status Register         |
| `0x18` | R           | Modem Status Register        |
| `0x1c` | R/W         | Scratch Pad Register         |

Each UART is implemented as two circular buffers in a memory bank with the following layout. Note that RX refers to data sent to / read by the processor, and TX refers to data sent from / written by the processor.

| Index | Name                    |
| ----- | ----------------------- |
| 0     | RX buffer start         |
| 254   | RX buffer read pointer  |
| 255   | RX buffer write pointer |
| 256   | TX buffer start         |
| 510   | TX buffer read pointer  |
| 511   | TX buffer write pointer |

Read/write pointers are stored modulo `2 * capacity` ([ref 1](https://github.com/hathach/tinyusb/blob/b203d9eaf7d76fd9fec71b4ee327805a80594574/src/common/tusb_fifo.h), [ref 2](https://gist.github.com/mcejp/719d3485b04cfcf82e8a8734957da06a)) to allow using the entire buffer capacity without introducing race conditions.

If the RX buffer is full and more data arrives, producers should discard the new data rather than overwriting old data in the buffer. An overflow may optionally be indicated by advancing the RX write pointer (without writing a value to the buffer) such that the size of the buffer is `capacity + 1`; this must be done atomically (ie. `wait` first) to avoid race conditions.

Note that the processor itself does not prevent code from overflowing the TX buffer. Users are expected to check the Line Status Register and avoid writing too much data at once.

### Syscon

Address `0xfffffff0` contains a simple write-only peripheral which can be used to control the system by writing values from the following table. Unsupported values will have no effect if written.

| Value        | Effect    |
| ------------ | --------- |
| `0x00000000` | Power off |
| `0x00000001` | Reboot    |

Additionally, the machine trap vector CSR `mtvec` is initialized to `0xfffffff0` at reset. To help catch issues with uninitialized `mtvec`, the processor will halt and output an error message if code jumps to this address.

## ISA

`RV32IMAZicntr_Zicsr_Zifencei_Zihintpause`

Supported privilege levels: M, U

| Extension   | Version |
| ----------- | ------- |
| M-mode      | 1.13    |
| I           | 2.1     |
| M           | 2.0     |
| A           | 2.1     |
| Zicntr      | 2.0     |
| Zicsr       | 2.0     |
| Zifencei\*  | 2.0     |
| Zihintpause | 2.0     |
| Xmlogsys    | N/A     |

\* Zifencei is currently just a stub - the instruction cache is already updated on every write to memory.

### Xmlogsys

This non-standard extension adds instructions to control the mlogv32 processor's hardware and access certain Mlog features.

| funct12 (31:20) | rs1 (19:15) | funct3 (14:12) | rd (11:7) | opcode (6:0) | name     |
| --------------- | ----------- | -------------- | --------- | ------------ | -------- |
| funct12         | rs1         | `000`          | `00000`   | `0001011`    | MLOGSYS  |
| funct12         | rs1         | `001`          | `00000`   | `0001011`    | MLOGDRAW |

The MLOG instructions are encoded with an I-type instruction format using the _custom-0_ opcode. The zero-extended immediate is used as a minor opcode (funct12) for implementation reasons.

The MLOGSYS instruction is used for simple system controls, including `printchar`, `printflush`, `drawflush`, and icache initialization.

The `mlogsys.icache` instruction uses register _rs1_ as the number of bytes to decode. This can be generated by using a linker script to find the end address of the `.text` section and load it using `li`. The actual number of bytes decoded will be the smallest of _rs1_, the size of the icache, and the size of ROM.

| funct12 | rs1     | name                  |
| ------- | ------- | --------------------- |
| 0       | length  | Initialize ROM icache |
| 1       | char    | `printchar`           |
| 2       | `00000` | `printflush`          |
| 3       | `00000` | `drawflush`           |

The MLOGDRAW instruction is used for drawing graphics using the Mlog `draw` instruction. Arguments are passed to this instruction using registers _rs1_, a1, a2, a3, a4, and a5 as necessary.

| funct12 | rs1     | a1    | a2    | a3     | a4       | a5       | name             |
| ------- | ------- | ----- | ----- | ------ | -------- | -------- | ---------------- |
| 0       | red     | green | blue  |        |          |          | `draw clear`     |
| 1       | red     | green | blue  | alpha  |          |          | `draw color`     |
| 2       | color   |       |       |        |          |          | `draw col`       |
| 3       | width   |       |       |        |          |          | `draw stroke`    |
| 4       | x1      | y1    | x2    | y2     |          |          | `draw line`      |
| 5       | x       | y     | width | height |          |          | `draw rect`      |
| 6       | x       | y     | width | height |          |          | `draw lineRect`  |
| 7       | x       | y     | sides | radius | rotation |          | `draw poly`      |
| 8       | x       | y     | sides | radius | rotation |          | `draw linePoly`  |
| 9       | x1      | y1    | x2    | y2     | x3       | y3       | `draw triangle`  |
| 10      | x       | y     | type  | id     | size     | rotation | `draw image`     |
| 11      | x       | y     |       |        |          |          | `draw print`     |
| 12      | x       | y     |       |        |          |          | `draw translate` |
| 13      | x       | y     |       |        |          |          | `draw scale`     |
| 14      | degrees |       |       |        |          |          | `draw rotate`    |
| 15      | `00000` |       |       |        |          |          | `draw reset`     |

#### `draw col`

`color` should be in integer format, eg. `0xff0000ff`.

#### `draw image`

`type`: `lookup` type

| Type   | Value |
| ------ | ----- |
| block  | 0     |
| unit   | 1     |
| item   | 2     |
| liquid | 3     |

`id`: `lookup` id (see https://yrueii.github.io/MlogDocs/)

Returns 1 if the id was successfully looked up, or 0 if the lookup returned null.

#### `draw print`

Only alignment `topLeft` is supported.

## riscv-arch-test

mlogv32 currently passes all compliance tests for the `RV32IMAUZicsr_Zifencei` ISA.

| TEST NAME                                                                  | COMMIT ID | STATUS |
| -------------------------------------------------------------------------- | --------- | ------ |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoadd.w-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoand.w-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomax.w-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomaxu.w-01.S              | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomin.w-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amominu.w-01.S              | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoor.w-01.S                | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoswap.w-01.S              | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoxor.w-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/add-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/addi-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/and-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/andi-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/auipc-01.S                  | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/beq-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bge-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bgeu-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/blt-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bltu-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bne-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/fence-01.S                  | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/jal-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/jalr-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lb-align-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lbu-align-01.S              | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lh-align-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lhu-align-01.S              | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lui-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lw-align-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/misalign1-jalr-01.S         | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/or-01.S                     | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/ori-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sb-align-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sh-align-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sll-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slli-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slt-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slti-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sltiu-01.S                  | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sltu-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sra-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srai-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srl-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srli-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sub-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sw-align-01.S               | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/xor-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/xori-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/div-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/divu-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mul-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulh-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulhsu-01.S                 | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulhu-01.S                  | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/rem-01.S                    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/remu-01.S                   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/Zifencei/src/Fencei.S             | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/ebreak.S            | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/ecall.S             | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-beq-01.S   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bge-01.S   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bgeu-01.S  | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-blt-01.S   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bltu-01.S  | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bne-01.S   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-jal-01.S   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-lh-01.S    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-lhu-01.S   | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-lw-01.S    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-sh-01.S    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-sw-01.S    | -         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign2-jalr-01.S | -         | Passed |

## Building

### Dev containers

- Open this folder with Dev Containers in VSCode.
- Activate the Python environment: `source .venv/bin/activate`
- Build everything: `make`

### Assembly

Assumes Ubuntu WSL on Windows.

- Install `uv`, `gcc-riscv64-unknown-elf`, and `binutils-riscv64-unknown-elf`.
- Set up the Python environment:
  - `uv venv .venv-wsl`
  - `source .venv-wsl/bin/activate`
  - `uv sync --active`
- Build all source files in `asm/`: `make asm`

### Rust

Assumes Powershell on Windows.

- Install `uv`, Rust, and `cargo-binutils`.
- Set up the Python environment:
  - `uv sync`
  - `.venv\Scripts\activate.ps1`
- Build all Rust projects in `rust/`: `make rust`

## Attribution

- SortKB: https://github.com/BasedUser/mPC
