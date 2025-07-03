OUTPUT_ARCH( "riscv" )
ENTRY(rvtest_entry_point)

MEMORY {
    ROM (rx)  : ORIGIN = 0x00000000, LENGTH = 18M
    RAM (rwx) : ORIGIN = 0x80000000, LENGTH = 21M
}

__stext = 0;
__etext = 0;
__sitext = 0;

SECTIONS
{
    .text : ALIGN(4) {
        KEEP(*(.text.init.rom));
        *(.text.init);
        *(.text);
        . = ALIGN(4);
        __etext_rom = .;
    } > ROM

    .data : ALIGN(4) {
        __sdata = .;
        *(.data);
        *(.data.string);
        . = ALIGN(4);
        __edata = .;
    } > RAM AT > ROM

    __sidata = LOADADDR(.data);

    .bss (NOLOAD) : ALIGN(4) {
        __sbss = .;
        *(.bss);
        . = ALIGN(4);
        __ebss = .;
    } > RAM

    _end = .;
}
