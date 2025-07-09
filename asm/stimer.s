.option norvc
.section .data
.section .text.init
.global _start

_start:
    li a0, 0

    # enable counters for S-mode
    li t0, -1
    csrw mcounteren, t0

    # set mstatus.MPP to S
    li t0, 0b1000000000000
    csrc mstatus, t0
    li t0, 0b0100000000000
    csrs mstatus, t0

    # switch to supervisor mode
    la t0, supervisor
    csrw mepc, t0
    mret

supervisor:
    # set timer for 1 second in the future
    rdtime t0
    addi t0, t0, 1000
    csrw stimecmp, t0
    csrwi stimecmph, 0

    # set up trap vector
    la t0, strap
    csrw stvec, t0

    # set sstatus.SPP to U
    li t0, 0b100000000
    csrc sstatus, t0

    # enable sie.STIE
    li t0, 0b100000
    csrs sie, t0

    # switch to user mode
    la t1, user
    csrw sepc, t1
    sret

user:
    j user

strap:
    # increment counter
    addi a0, a0, 1

    # set timer for 1 second in the future
    rdtime t0
    addi t0, t0, 1000
    csrw stimecmp, t0
    csrwi stimecmph, 0

    sret
