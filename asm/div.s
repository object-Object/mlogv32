.global _start
_start:
    li a2, 0
    li a3, 0

    li a0, 14
    li a1, 3

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, 15
    li a1, 3

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, 16
    li a1, 3

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, 1
    li a1, 2

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, 6
    li a1, -3

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, 7
    li a1, -3

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, -6
    li a1, 3

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, -7
    li a1, 3

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, 1
    li a1, 0

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, 0
    li a1, 0

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, -1
    li a1, 0

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

    li a0, -2147483648
    li a1, -1

    div a2, a0, a1
    rem a3, a0, a1
    divu a2, a0, a1
    remu a3, a0, a1

loop:
    j loop
