.global _start
_start:
    la t0, trap
    csrw mtvec, t0

    ecall

    .insn i CUSTOM_0, 0, zero, zero, 0 # halt

trap:
    csrr t0, mepc
    addi t0, t0, 4
    csrw mepc, t0
    mret
