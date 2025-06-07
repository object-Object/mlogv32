# mlogv32

RISC-V processor in Mindustry logic. Requires Mindustry build 149+.

![image](https://github.com/user-attachments/assets/3951b4b7-cc56-494a-85f8-54bd9f2ee7d5)

## Architecture

Extensions: `rv32ima_Zicsr_Zicntr_Zihintpause`

Memory consists of three sections. Two are directly accessible by code: ROM (rx) and RAM (rw). The third section is an instruction cache, which takes up 4x as much space as the executable portion of memory. The instruction cache is updated at reset and whenever an instruction writes to RAM.

Code begins executing at address `0x4`. Address `0x0` must contain the size of the `.text` section (ie. `__etext`) to tell the processor how much data to decode from ROM; alternatively, it can be `0` to decode the entire ROM.

## Extensions

`RV32IMAZicntr_Zicsr_Zifencei_Zihintpause`

| Extension   | Version |
| ----------- | ------- |
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
| funct12         | `00000`     | `001`          | rd        | `0001011`    | MLOGDRAW |

The MLOG instructions are encoded with an I-type instruction format using the _custom-0_ opcode. The zero-extended immediate is used as a minor opcode (funct12) for implementation reasons.

The MLOGSYS instruction is used for simple system controls, including halt, `printchar`, `printflush`, `drawflush`, and sortKB/kbconv integration.

| funct12 | rd                      | rs1     | name                       |
| ------- | ----------------------- | ------- | -------------------------- |
| 0       | `00000`                 | `00000` | Halt                       |
| 1       | `00000`                 | char    | `printchar`                |
| 2       | `00000`                 | `00000` | `printflush`               |
| 3       | `00000`                 | `00000` | `drawflush`                |
| 4       | char (0 if no new data) | `00000` | Read next char from sortKB |

The MLOGDRAW instruction is used for drawing graphics using the Mlog `draw` instruction. Arguments are passed to this instruction using registers a0 to a5 as necessary, and any return value is placed in _rd_. If _rd_ is specified as `00000` in the below table, no value will be written to `rd` in any case.

| funct12 | rd                      | a0      | a1    | a2        | a3     | a4       | a5       | name             |
| ------- | ----------------------- | ------- | ----- | --------- | ------ | -------- | -------- | ---------------- |
| 0       | `00000`                 | red     | green | blue      |        |          |          | `draw clear`     |
| 1       | `00000`                 | red     | green | blue      | alpha  |          |          | `draw color`     |
| 2       | `00000`                 | color   |       |           |        |          |          | `draw col`       |
| 3       | `00000`                 | width   |       |           |        |          |          | `draw stroke`    |
| 4       | `00000`                 | x1      | y1    | x2        | y2     |          |          | `draw line`      |
| 5       | `00000`                 | x       | y     | width     | height |          |          | `draw rect`      |
| 6       | `00000`                 | x       | y     | width     | height |          |          | `draw lineRect`  |
| 7       | `00000`                 | x       | y     | sides     | radius | rotation |          | `draw poly`      |
| 8       | `00000`                 | x       | y     | sides     | radius | rotation |          | `draw linePoly`  |
| 9       | `00000`                 | x1      | y1    | x2        | y2     | x3       | y3       | `draw triangle`  |
| 10      | lookup success (1 or 0) | x       | y     | type      | id     | size     | rotation | `draw image`     |
| 11      | `00000`                 | x       | y     | alignment |        |          |          | `draw print`     |
| 12      | `00000`                 | x       | y     |           |        |          |          | `draw translate` |
| 13      | `00000`                 | x       | y     |           |        |          |          | `draw scale`     |
| 14      | `00000`                 | degrees |       |           |        |          |          | `draw rotate`    |
| 15      | `00000`                 |         |       |           |        |          |          | `draw reset`     |

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

## Attribution

- SortKB: https://github.com/BasedUser/mPC

## riscv-arch-test

mlogv32 currently passes all compliance tests for the `RV32IMA` ISA.

```
TEST NAME                                                                                     : COMMIT ID   : STATUS
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoadd.w-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoand.w-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomax.w-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomaxu.w-01.S      : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomin.w-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amominu.w-01.S      : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoor.w-01.S        : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoswap.w-01.S      : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoxor.w-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/add-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/addi-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/and-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/andi-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/auipc-01.S          : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/beq-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bge-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bgeu-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/blt-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bltu-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bne-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/fence-01.S          : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/jal-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/jalr-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lb-align-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lbu-align-01.S      : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lh-align-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lhu-align-01.S      : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lui-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lw-align-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/misalign1-jalr-01.S : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/or-01.S             : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/ori-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sb-align-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sh-align-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sll-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slli-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slt-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slti-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sltiu-01.S          : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sltu-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sra-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srai-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srl-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srli-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sub-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sw-align-01.S       : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/xor-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/I/src/xori-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/div-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/divu-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mul-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulh-01.S           : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulhsu-01.S         : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulhu-01.S          : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/rem-01.S            : -           : Passed
/workspaces/mlogv32/riscof/riscv-arch-test/riscv-test-suite/rv32i_m/M/src/remu-01.S           : -           : Passed
```
