.global _start
_start:
    # PAUSE (apparently not supported by clang)
    .word 0b00000001000000000000000000001111

    ebreak

    ecall

loop:
    j loop
