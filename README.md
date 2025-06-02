# mlogv32

RISC-V processor in Mindustry logic. Requires Mindustry build 149+.

![image](https://github.com/user-attachments/assets/3951b4b7-cc56-494a-85f8-54bd9f2ee7d5)

## Architecture

Extensions: `rv32ima_Zicsr_Zicntr_Zihintpause`

Memory consists of three sections. Two are directly accessible by code: ROM (rx) and RAM (rw). The third section is an instruction cache, which takes up 4x as much space as the executable portion of memory. The instruction cache is updated at reset and whenever an instruction writes to RAM.

Code begins executing at address `0x4`. Address `0x0` must contain the size of the `.text` section (ie. `__etext`) to tell the processor how much data to decode from ROM; alternatively, it can be `0` to decode the entire ROM.

## System calls

| Index (a7) | Description      | a0      | a1    | a2        | a3     | a4       | a5       | a6  | Return (a0)             |
| ---------- | ---------------- | ------- | ----- | --------- | ------ | -------- | -------- | --- | ----------------------- |
| 0          | Halt             |         |       |           |        |          |          |     |                         |
| 1          | `printchar`      | value   |       |           |        |          |          |     |                         |
| 2          | `printflush`     |         |       |           |        |          |          |     |                         |
| 3          | `draw clear`     | red     | green | blue      |        |          |          |     |                         |
| 4          | `draw color`     | red     | green | blue      | alpha  |          |          |     |                         |
| 5          | `draw col`       | color   |       |           |        |          |          |     |                         |
| 6          | `draw stroke`    | width   |       |           |        |          |          |     |                         |
| 7          | `draw line`      | x1      | y1    | x2        | y2     |          |          |     |                         |
| 8          | `draw rect`      | x       | y     | width     | height |          |          |     |                         |
| 9          | `draw lineRect`  | x       | y     | width     | height |          |          |     |                         |
| 10         | `draw poly`      | x       | y     | sides     | radius | rotation |          |     |                         |
| 11         | `draw linePoly`  | x       | y     | sides     | radius | rotation |          |     |                         |
| 12         | `draw triangle`  | x1      | y1    | x2        | y2     | x3       | y3       |     |                         |
| 13         | `draw image`     | x       | y     | type      | id     | size     | rotation |     | lookup success (1 or 0) |
| 14         | `draw print`     | x       | y     | alignment |        |          |          |     |                         |
| 15         | `draw translate` | x       | y     |           |        |          |          |     |                         |
| 16         | `draw scale`     | x       | y     |           |        |          |          |     |                         |
| 17         | `draw rotate`    | degrees |       |           |        |          |          |     |                         |
| 18         | `draw reset`     |         |       |           |        |          |          |     |                         |
| 19         | `drawflush`      |         |       |           |        |          |          |     |                         |

### `draw col`

`color` should be in integer format, eg. `0xff0000ff`.

### `draw image`

`type`: `lookup` type

| Type   | Value |
| ------ | ----- |
| block  | 0     |
| unit   | 1     |
| item   | 2     |
| liquid | 3     |

`id`: `lookup` id (see https://yrueii.github.io/MlogDocs/)

Returns 1 if the id was successfully looked up, or 0 if the lookup returned null.

### `draw print`

| Alignment   | Value |
| ----------- | ----- |
| bottom      | 0     |
| bottomLeft  | 1     |
| bottomRight | 2     |
| center      | 3     |
| left        | 4     |
| right       | 5     |
| top         | 6     |
| topLeft     | 7     |
| topRight    | 8     |

## Building

### Dev containers

- Open this folder with Dev Containers in VSCode.
- Set up the Python environment: `uv sync`
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
