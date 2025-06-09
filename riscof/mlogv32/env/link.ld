OUTPUT_ARCH( "riscv" )
ENTRY(rvtest_entry_point)

MEMORY {
    ROM  (rx)  : ORIGIN = 0x00000000, LENGTH = 0x200000
    RAM  (rwx) : ORIGIN = 0x80000000, LENGTH = 0x200000
    MMIO (rw)  : ORIGIN = 0xf0000000, LENGTH = 16
}

SECTIONS
{
    .text : {
        KEEP(*(.text.init));
        *(.text)
        . = ALIGN(4);
        __etext = .;
    } > ROM

    .data : ALIGN(4) {
        __sdata = .;
        *(.data);
        *(.data.string);
    } > RAM AT > ROM

    . = ALIGN(4);
    __edata = .;

    __sidata = LOADADDR(.data);

    .bss (NOLOAD) : ALIGN(4) {
        . = ALIGN(4);
        __sbss = .;
        *(.bss);
    } > RAM

    . = ALIGN(4);
    __ebss = .;

    _end = .;
}
