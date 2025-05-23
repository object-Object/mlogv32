.section .text.start
    .word __etext

.global _start
_start:
    li x1, 0b1
    li x2, 1
    sll x3, x1, x2
    
    li x4, 0xffffffff
    li x5, 31
    sll x6, x4, x5

    li x7, 0b10000000000000000000000000000000
    li x8, 1
    srl x9, x7, x8

    li x10, 0b10000000000000000000000000000000
    li x11, 1
    sra x12, x10, x11

    li x13, 1
    li x14, 1
    srl x15, x13, x14

    li x16, 1
    li x17, 1
    sra x18, x16, x17

    li x19, 0
    li x20, 1
    srl x21, x19, x20

    li x22, 0
    li x23, 1
    sra x24, x22, x23

    j 0
