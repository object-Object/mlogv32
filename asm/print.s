.global _start
_start:
    la s0, msg
    li s1, 0
    la s2, msg_len
    
loop:
    lbu a0, 0(s0)
    li a7, 1 # printchar
    ecall

    addi s0, s0, 1
    addi s1, s1, 1
    blt s1, s2, loop

    li a7, 2 # printflush
    ecall

    j 0

.section .data
msg:
    .ascii "hello world!"
    .set msg_len, . - msg

.balign 4
