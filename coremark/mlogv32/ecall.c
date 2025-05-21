#include "core_portme.h"
#include <coremark.h>
#include "ecall.h"

// https://github.com/torvalds/linux/blob/a5806cd506af5a7c19bcd596e4708b5c464bfd21/arch/riscv/kernel/sbi_ecall.c#L20
unsigned int ecall(
    unsigned int arg0,
    unsigned int arg1,
    unsigned int arg2,
    unsigned int arg3,
    unsigned int arg4,
    unsigned int arg5,
    unsigned int arg6,
    Syscall which
) {
    register ee_ptr_int a0 asm ("a0") = (ee_ptr_int)(arg0);
    register ee_ptr_int a1 asm ("a1") = (ee_ptr_int)(arg1);
    register ee_ptr_int a2 asm ("a2") = (ee_ptr_int)(arg2);
    register ee_ptr_int a3 asm ("a3") = (ee_ptr_int)(arg3);
    register ee_ptr_int a4 asm ("a4") = (ee_ptr_int)(arg4);
    register ee_ptr_int a5 asm ("a5") = (ee_ptr_int)(arg5);
    register ee_ptr_int a6 asm ("a6") = (ee_ptr_int)(arg6);
    register ee_ptr_int a7 asm ("a7") = (ee_ptr_int)(which);
    asm volatile ("ecall"
                : "+r" (a0)
                : "r" (a1), "r" (a2), "r" (a3), "r" (a4), "r" (a5), "r" (a6), "r" (a7)
                :);
    return a0;
}
