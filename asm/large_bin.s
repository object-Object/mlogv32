.global _start
_start:
    la x1, word1
    lw x2, 0(x1)
    sb zero, 3(x1)
    lw x3, 0(x1)

    la x4, word2
    lw x5, 0(x4)
    sb zero, 3(x4)
    lw x6, 0(x4)

    la x7, word3
    lw x8, 0(x7)
    sb zero, 3(x7)
    lw x9, 0(x7)

    j 0

.section .data

    .org 512
    .balign 4
word1:
    .word 0x01020304 # 16909060

    .org 2048
    .balign 4
word2:
    .word 0x05060708 # 84281096

    .org 5000
    .balign 4
word3:
    .word 0x090a0b0c # 151653132

.balign 4