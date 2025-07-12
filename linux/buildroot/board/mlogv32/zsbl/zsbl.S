#define FAST_ROM y

.set UART0_BASE, 0xf0000010

.macro log message
    la a0, 1f
    call do_print
.pushsection .rodata
1:  .asciz "[zsbl] \message\r\n"
.popsection
.endm

.macro copy name
    la t0, _si\name
    la t1, _s\name
    la t2, _e\name
1:
    lw t3, 0(t0)
    sw t3, 0(t1)
    addi t0, t0, 4
    addi t1, t1, 4
    bltu t1, t2, 1b
.endm

.section .text
.global _start
_start:
    // enable UART
    la t0, UART0_BASE
    li t1, 1
    sb t1, 8(t0)

    // copy loader to RAM
    log "loading kernel..."
    copy loader

    // copy kernel to RAM
    call loader

    // copy OpenSBI to RAM
    log "loading OpenSBI..."
    copy opensbi

    log "done!"

    // wait for UART THR to drain so we don't lose any logs if OpenSBI initializes UART0 in the same tick
    la t0, UART0_BASE
1:
    lbu t1, 0x14(t0)
    andi t1, t1, 0b100000
    beqz t1, 1b

    // jump to OpenSBI
    li a0, 0 // hartid
    li a1, 0 // DTB (null)
    tail _sopensbi

do_print:
    la t0, UART0_BASE
1:
    lbu t1, 0(a0)
    beqz t1, 2f
    sb t1, 0(t0)
    addi a0, a0, 1
    j 1b
2:
    ret

#ifndef FAST_ROM
.section .loader, "ax", @progbits
.balign 4
#endif
loader:
    // copy kernel to RAM
    // we do this here so the copy operation can be covered by the icache
    copy kernel
    ret

.section .rootfs, "a", @progbits
.balign 4
    .incbin ZSBL_ROOTFS_PATH

.section .kernel, "ax", @progbits
.balign 4
    .incbin ZSBL_KERNEL_PATH

.section .opensbi, "ax", @progbits
.balign 4
    .incbin ZSBL_OPENSBI_PATH
