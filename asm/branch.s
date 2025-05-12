.global _start
_start:
    li x1, 2
    li x2, -1
    bge x1, x2, true

false:
    li x3, 0
    j finally

true:
    li x3, 1

finally:
    j finally