.global _start
_start:
    la s0, msg
    li s1, 0
    la s2, msg_len
    
loop:
    lbu t0, 0(s0)
    .insn i CUSTOM_0, 0, zero, t0, 1 # printchar

    addi s0, s0, 1
    addi s1, s1, 1
    blt s1, s2, loop

    .insn i CUSTOM_0, 0, zero, zero, 2 # printflush

    .insn i CUSTOM_0, 0, zero, zero, 0 # halt

.section .rodata
msg:
    .ascii "hello world!"
    .set msg_len, . - msg

.balign 4
