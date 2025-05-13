.global _start
_start:
    li x1, 0
    li x2, 10
    li x3, 0
    li x4, -10

loop1:
    addi x1, x1, 1
    blt x1, x2, loop1

loop2:
    addi x3, x3, -1
    bge x3, x4, loop2

    j 0
