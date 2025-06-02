.global _start
_start:
    li a2, 0
    li a3, 0

    li a0, 0
    li a1, 0
    
    mul a3, a0, a1
    mulh a2, a0, a1
    mulhu a2, a0, a1
    mulhsu a2, a0, a1

    li a0, 3
    li a1, 4
    
    mul a3, a0, a1
    mulh a2, a0, a1
    mulhu a2, a0, a1
    mulhsu a2, a0, a1

    li a0, 3
    li a1, -4
    
    mul a3, a0, a1
    mulh a2, a0, a1
    mulhu a2, a0, a1
    mulhsu a2, a0, a1

    li a0, -5
    li a1, 2
    
    mul a3, a0, a1
    mulh a2, a0, a1
    mulhu a2, a0, a1
    mulhsu a2, a0, a1

    li a0, 0xdeadbeef
    li a1, 0xbabecafe
    
    mul a3, a0, a1
    mulh a2, a0, a1
    mulhu a2, a0, a1
    mulhsu a2, a0, a1

loop:
    j loop
