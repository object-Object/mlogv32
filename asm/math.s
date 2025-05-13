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

    j 0
