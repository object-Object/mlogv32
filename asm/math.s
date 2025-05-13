.global _start
_start:
    li x1, 1
    li x2, 1
    slt x3, x1, x2
    
    li x4, 1
    li x5, 2
    slt x6, x4, x5

    li x7, -1
    li x8, 1
    slt x9, x7, x8

    li x10, 10
    li x11, -2
    sub x12, x10, x11

    li x13, 10
    li x14, 12
    sub x15, x13, x14

    j 0
