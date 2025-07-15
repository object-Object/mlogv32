# mlogv32

RISC-V processor in Mindustry logic that runs Linux. Requires Mindustry build 149+.

<img width="1823" height="1008" alt="linux" src="https://github.com/user-attachments/assets/9b1fd6fa-ba4c-4498-9892-ae87a81d4588" />

## Architecture

Physical memory consists of three sections. Two are directly accessible by code: ROM (rx) and RAM (rwx). The third section is an instruction cache, which sits directly after RAM and uses the same processor layout to store partially decoded instructions.

For maximum performance, the instruction cache for ROM can be initialized at boot using the MLOGSYS instruction. It is also updated whenever an instruction writes to RAM that is covered by the icache. If executing from memory not covered by the icache, the processor manually fetches and decodes the instruction from main memory.

Instructions are cached in the following format, utilizing the full 54 bits of `double` precision ([53 mantissa](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER), 1 sign).

| 53:47             | 46:42 | 41:37 | 36:32 | 31:0 |
| ----------------- | ----- | ----- | ----- | ---- |
| op_id (-64 to 63) | rs2   | rs1   | rd    | imm  |

The CPU is implemented using a variable-size build-order-independent subframe architecture. There is one [controller processor](src/cpu/controller.mlog.jinja) and an arbitrary number of [worker processors](src/cpu/worker.mlog.jinja). Schematics are generated using a [custom preprocessor](python/src/mlogv32/preprocessor) based on Jinja and pymsch.

## Memory

| Address      | Size         | Access Type | Name        |
| ------------ | ------------ | ----------- | ----------- |
| `0x00000000` | Configurable | R/X         | Program ROM |
| Configurable | Configurable | R/X         | Data ROM    |
| `0x80000000` | Configurable | R/W/X/A\*   | RAM         |
| `0xf0000000` | `0x4`        | R/W         | `mtime`     |
| `0xf0000004` | `0x4`        | R/W         | `mtimeh`    |
| `0xf0000008` | `0x4`        | R/W         | `mtimecmp`  |
| `0xf000000c` | `0x4`        | R/W         | `mtimecmph` |
| `0xf0000010` | `0x20`       | R/W         | UART0       |
| `0xf0000030` | `0x20`       | R/W         | UART1       |
| `0xf0000050` | `0x20`       | R/W         | UART2       |
| `0xf0000070` | `0x20`       | R/W         | UART3       |
| `0xfffffff0` | `0x4`        | R/W         | Syscon      |

\* Atomic instructions are only supported in RAM.

Code begins executing at address `0x00000000` (ie. the start of ROM).

ROM may optionally be partitioned into program ROM and data ROM. Data ROM begins immediately after program ROM and is not included in the instruction cache, allowing large amounts of data to be included in ROM while maintaining icache coverage of RAM. Despite being intended for storing data, it is still possible to execute from data ROM (eg. to allow efficiently implementing zero stage bootloaders without wasting icache space). The division between program and data ROM must be aligned to 16K, ie. the size of one memory proc. By default, data ROM has a size of 0.

Addresses `0xf0000000` - `0xffffffff` are reserved for system purposes such as MMIO.

### Machine Timers

The `mtime` and `mtimecmp` registers are mapped to `0xf0000000` and `0xf0000008` respectively, and have a period of 1 ms. The timer registers are not accessible to privilege modes lower than M-mode.

### UART

The processor includes four identical emulated UART 16550 peripherals based on [this datasheet](https://caro.su/msx/ocm_de1/16550.pdf). The UARTs support the following features:

- Configurable FIFO capacity (up to 253 bytes) for TX and RX, stored as a variable in the CONFIG processor.
- Theoretical maximum transfer rate of 121440 bits/sec (253 bytes/tick).
- Line Status Register flags: Transmitter Empty, THR Empty, Overrun Error, Data Ready.
- FIFO Control Register flags: Enable FIFOs (0 is ignored), Reset RX/TX FIFO

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

| Index | Name                                    |
| ----- | --------------------------------------- |
| 0     | RX buffer start                         |
| 254   | RX buffer read pointer                  |
| 255   | RX buffer write pointer / overflow flag |
| 256   | TX buffer start                         |
| 510   | TX buffer read pointer                  |
| 511   | TX buffer write pointer                 |

Read/write pointers are stored modulo `capacity + 1`. A buffer is empty when `rptr == wptr` and full when `rptr == (wptr + 1) % (capacity + 1)`. If the RX buffer is full and more data arrives, producers should discard the new data rather than overwriting old data in the buffer. An overflow may optionally be indicated to the processor by setting bit 8 of `rx_wptr` (ie. `rx_wptr | 0x100`).

Note that the processor itself does not set the TX overflow flag or prevent code from overflowing the TX buffer. Users are expected to check the Line Status Register and avoid writing too much data at once.

### Syscon

Address `0xfffffff0` contains a simple memory-mapped peripheral which can be used to control the system by writing values from the following table. Unsupported values will have no effect if written. Reads will always return `0`.

| Value        | Effect    |
| ------------ | --------- |
| `0x00000000` | Power off |
| `0x00000001` | Reboot    |
| `0x00000002` | Power off |

Additionally, the trap vector CSRs `mtvec` and `stvec` are initialized to `0xfffffff0` at reset. To help catch issues with uninitialized trap vectors, the processor will halt and output an error message if a trap jumps to this address.

## ISA

`RV32IMAZicntr_Zicsr_Zifencei_Zihintpause_Sstc_Svade`

Supported privilege levels: M, S, U

Supported address translation schemes: Bare, Sv32

| Extension   | Version |
| ----------- | ------- |
| M-mode      | 1.13    |
| S-mode      | 1.13    |
| I           | 2.1     |
| M           | 2.0     |
| A           | 2.1     |
| Zicntr      | 2.0     |
| Zicsr       | 2.0     |
| Zifencei\*  | 2.0     |
| Zihintpause | 2.0     |
| Sstc        | 1.0.0   |
| Svade       | 1.0     |
| Xmlogsys    | N/A     |

\* Zifencei is currently just a stub - the instruction cache is already updated on every write to memory.

### Xmlogsys

This non-standard extension adds instructions to control the mlogv32 processor's hardware and access certain Mlog features.

| funct12 (31:20) | rs1 (19:15) | funct3 (14:12) | rd (11:7) | opcode (6:0) | name    |
| --------------- | ----------- | -------------- | --------- | ------------ | ------- |
| funct12         | rs1         | `000`          | `00000`   | `0001011`    | MLOGSYS |

The MLOG instructions are encoded with an I-type instruction format using the _custom-0_ opcode. The zero-extended immediate is used as a minor opcode (funct12) for implementation reasons.

The MLOGSYS instruction is used for simple system controls.

The `mlogsys.icache` M-mode instruction uses register _rs1_ as the number of bytes to decode. This can be generated by using a linker script to find the end address of the `.text` section and load it using `li`. The actual number of bytes decoded will be the smallest of _rs1_, the size of the icache, and the size of ROM.

| funct12 | rs1    | name                  |
| ------- | ------ | --------------------- |
| 0       | length | Initialize ROM icache |

## CSRs

CSR values are stored either in a RAM processor (CSRS), in a variable in the CPU, or as an implicit read-only zero value, depending on the CSR. See [cpu.yaml](src/cpu/cpu.yaml) for the full list of implemented CSRs. Attempts to access a CSR that is not in this list will raise an illegal instruction exception.

### `cycle`

The `[m]cycle[h]` counter is incremented at the start of each worker's tick, just before it jumps back into code execution. The period should be something like `number of workers * 1/60 seconds`, but it will vary based on FPS.

### `time`

The `[m]time[h]` counter is based on the `@time` value in Mindustry. It has a period of 1 ms, and is incremented once per tick by the controller based on the time delta since the previous tick.

## riscv-arch-test

mlogv32 currently passes all compliance tests for the `RV32IMASUZicsr_Zifencei` ISA.

Commit: [riscv-non-isa/riscv-arch-test@6731c039](https://github.com/riscv-non-isa/riscv-arch-test/tree/6731c0393d534f37fdb6768da40b5eb99fd720ad)

| TEST NAME                                                                                | STATUS |
| ---------------------------------------------------------------------------------------- | ------ |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoadd.w-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoand.w-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomax.w-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomaxu.w-01.S                            | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amomin.w-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amominu.w-01.S                            | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoor.w-01.S                              | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoswap.w-01.S                            | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/A/src/amoxor.w-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/add-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/addi-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/and-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/andi-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/auipc-01.S                                | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/beq-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bge-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bgeu-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/blt-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bltu-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/bne-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/fence-01.S                                | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/jal-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/jalr-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lb-align-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lbu-align-01.S                            | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lh-align-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lhu-align-01.S                            | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lui-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/lw-align-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/misalign1-jalr-01.S                       | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/or-01.S                                   | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/ori-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sb-align-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sh-align-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sll-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slli-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slt-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/slti-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sltiu-01.S                                | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sltu-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sra-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srai-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srl-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/srli-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sub-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/sw-align-01.S                             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/xor-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/I/src/xori-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/div-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/divu-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mul-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulh-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulhsu-01.S                               | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/mulhu-01.S                                | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/rem-01.S                                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/M/src/remu-01.S                                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/Zifencei/src/Fencei.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-CSR-ALL-MODES.S                   | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-NA4-M.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-NA4-S.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-NA4-U.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-NAPOT-M.S                         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-NAPOT-S.S                         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-NAPOT-U.S                         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-TOR-M.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-TOR-S.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/pmp/src/pmp32-TOR-U.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/ebreak.S                          | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/ecall.S                           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-beq-01.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bge-01.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bgeu-01.S                | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-blt-01.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bltu-01.S                | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-bne-01.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-jal-01.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-lh-01.S                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-lhu-01.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-lw-01.S                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-sh-01.S                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign-sw-01.S                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/privilege/src/misalign2-jalr-01.S               | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/mstatus_tvm_test.S                  | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/pmp_check_on_pa_S_mode.S            | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/pmp_check_on_pa_U_mode.S            | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/pmp_check_on_pte_S_mode.S           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/pmp_check_on_pte_U_mode.S           | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/satp_access_tests.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_A_and_D_S_mode.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_A_and_D_U_mode.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_U_Bit_set_U_mode.S               | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_U_Bit_unset_S_mode.S             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_U_Bit_unset_U_mode.S             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_VA_all_ones_S_mode.S             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_global_pte_S_mode.S              | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_global_pte_U_mode.S              | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_invalid_pte_S_mode.S             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_invalid_pte_U_mode.S             | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_misaligned_S_mode.S              | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_misaligned_U_mode.S              | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mprv_S_mode.S                    | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mprv_U_mode.S                    | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mprv_U_set_sum_set_S_mode.S      | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mprv_U_set_sum_unset_S_mode.S    | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mprv_bare_mode.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mstatus_sbe_set_S_mode.S         | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mstatus_sbe_set_sum_set_S_mode.S | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mxr_S_mode.S                     | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_mxr_U_mode.S                     | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_nleaf_pte_level0_S_mode.S        | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_nleaf_pte_level0_U_mode.S        | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_reserved_rsw_pte_S_mode.S        | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_reserved_rsw_pte_U_mode.S        | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_reserved_rwx_pte_S_mode.S        | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_reserved_rwx_pte_U_mode.S        | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_sum_set_S_mode.S                 | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_sum_set_U_Bit_unset_S_mode.S     | Passed |
| riscv-arch-test/riscv-test-suite/rv32i_m/vm_sv32/src/vm_sum_unset_S_mode.S               | Passed |

## Building

### Dev containers

- Attach to the dev container.
  - Option 1: Open this repository in VSCode with the [Dev Containers extension](https://code.visualstudio.com/docs/devcontainers/containers).
  - Option 2:
    - Install the [Dev Container CLI](https://code.visualstudio.com/docs/devcontainers/devcontainer-cli).
    - Start the container if not running: `devcontainer up --workspace-folder .`
    - Get a shell in the container: `devcontainer exec --workspace-folder . bash`
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
