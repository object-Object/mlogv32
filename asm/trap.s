.global _start
_start:
    la t0, trap
    csrw mtvec, t0

    ecall

    # halt
    li t0, 0xfffffff0
    sw zero, 0(t0)

trap:
    csrr t0, mepc
    addi t0, t0, 4
    csrw mepc, t0
    mret
