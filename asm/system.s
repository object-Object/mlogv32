.section .text.start
    .word __etext

.global _start
_start:
    # PAUSE (apparently not supported by clang)
    .word 0b00000001000000000000000000001111
    
    ebreak
    
    li a0, 0
    li a7, 0 # halt
    ecall

