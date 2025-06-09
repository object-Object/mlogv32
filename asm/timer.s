# https://danielmangum.com/posts/risc-v-bytes-timer-interrupts/

.option norvc
.section .data
.section .text.init
.global _start

_start:
    li a0, 0

    # set timer for 1 second in the future
    li t0, 0xf0000008
    li t1, 1000
    sw t1, 0(t0)
    sw zero, 4(t0)

    # set up trap vector
    la t0, mtrap
    csrw mtvec, t0

    # set mstatus.MPP to U
    li t0, 0x1800
    csrc mstatus, t0

    # enable mie.MTIE
    li t0, 0x80
    csrs mie, t0

    # jump to user mode
    la t1, user
    csrw mepc, t1
    mret

mtrap:
    # increment counter
    addi a0, a0, 1

    # reset time to 0
    li t0, 0xf0000000
    sw zero, 0(t0)
    sw zero, 4(t0)

    mret

user:
    j user
