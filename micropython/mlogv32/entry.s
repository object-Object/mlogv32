.section .text.start

.global _start
_start:
    # initialize icache
    la t0, __etext
    .insn i CUSTOM_0, 0, zero, t0, 0

    # set stack pointer and global pointer
    la t1, _stack_start
    andi sp, t1, -16
    add s0, sp, zero

    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop

    # initialize .data
    la t0, __sidata
    la t1, __sdata
    la t2, __edata
load_data:
    bgeu t1, t2, data_done
    lb t3, 0(t0)
    sb t3, 0(t1)
    addi t0, t0, 1
    addi t1, t1, 1
    j load_data
data_done:

    # clear .bss
    la t0, __sbss
    la t1, __ebss
clear_bss:
    bgeu t0, t1, bss_done
    sb zero, 0(t0)
    addi t0, t0, 1
    j clear_bss
bss_done:

    # jump to C code
    call main

    # if main returns, halt the processor
    li t0, 0xfffffff0
    sw zero, 0(t0)
