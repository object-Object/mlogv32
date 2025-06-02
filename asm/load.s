.global _start
_start:
    la x1, word
    lw x2, 0(x1) # 16909060 (0x01020304)
    lh x3, 0(x1) # 772 (0x0304)
    lh x4, 2(x1) # 258 (0x0102)
    lb x5, 0(x1) # 4 (0x04)
    lb x6, 1(x1) # 3 (0x03)
    lb x7, 2(x1) # 2 (0x02)
    lb x8, 3(x1) # 1 (0x01)

    la x9, negative
    lb x10, 0(x9)  # 4294967293 (-3)
    lbu x11, 0(x9) # 253 (0b11111101)

    lh x12, 3(x0)  # misaligned load exception

loop:
    j loop

.section .rodata
.balign 4
word:
    .word 0x01020304 # LE: 0x04030201

negative:
    .byte -3

.balign 4
