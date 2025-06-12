use core::arch::global_asm;

// init icache as soon as riscv-rt lets us
#[rustfmt::skip]
global_asm!("
.global __pre_init
__pre_init:
    la t0, __etext
    .insn i CUSTOM_0, 0, zero, t0, 0
    ret

.global _pre_init_trap
_pre_init_trap:
    li t0, 0xfffffff0
    jr t0
");
