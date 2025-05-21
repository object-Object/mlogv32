.section .text.start
.global _start

_start:
    la t1, _stack_start
    andi sp, t1, -16
    add s0, sp, zero

    la gp, __global_pointer$
    
    # Clear BSS section
    la t0, __sbss
    la t1, __ebss
clear_bss:
    bgeu t0, t1, bss_done
    sb zero, 0(t0)
    addi t0, t0, 1
    j clear_bss
bss_done:

    # Jump to C code
    call main
    
    # In case main returns
1:  j 1b
