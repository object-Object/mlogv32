.section .text.start
.global _start
_start:
    // initialize icache
    la t0, _etext
    .insn i CUSTOM_0, 0, zero, t0, 0

    // copy payload to RAM
    la t0, _sipayload
    la t1, _spayload
    la t2, _epayload
1:
    lw t3, 0(t0)
    sw t3, 0(t1)
    addi t0, t0, 4
    addi t1, t1, 4
    bltu t1, t2, 1b

    // hartid
    li a0, 0

    // DTB
    li a1, 0

    // jump to payload
    call _spayload

    // if the payload returns, halt the processor
    li t0, 0xfffffff0
    sw zero, 0(t0)    

.section .data.payload
.align 4
.incbin ZSBL_PAYLOAD_PATH

.section .rodata.kernel
.align 4
.incbin ZSBL_KERNEL_PATH
