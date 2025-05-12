.global _start
_start:
    li x1, 1
    li x2, 2
    add x3, x1, x2

    li x4, 16
    jalr x5, x4, 1 // misaligned
