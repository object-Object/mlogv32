.global _start
_start:
    la s0, msg
    li s1, 0
    la s2, msg_len

    # UART0
    li a0, 0xf0000010

    li t0, 0b11
    sb t0, 0xc(a0) # control

loop:
    lbu t0, 0(s0)
    sb t0, 0x4(a0) # tx

    addi s0, s0, 1
    addi s1, s1, 1
    blt s1, s2, loop

    # halt
    li t0, 0xfffffff0
    sw zero, 0(t0)

.section .rodata
msg:
    .ascii "hello world!"
    .set msg_len, . - msg

.balign 4
