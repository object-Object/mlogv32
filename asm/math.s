.global _start
_start:
    li x1, 0b0101
    li x2, 0b0011
    xor x3, x1, x2 # should be 0b0110 == 6
    
    li x4, 0b0101
    li x5, 0b0011
    or x6, x4, x5 # should be 0b0111 == 7

    li x7, 0b0101
    li x8, 0b0011
    and x9, x7, x8 # should be 0b0001 == 1

    j 0
