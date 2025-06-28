ENTRY(_start);

MEMORY {
    ROM  (rx)  : ORIGIN = 0x00000000, LENGTH = 512K
    RAM  (rwx) : ORIGIN = 0x80000000, LENGTH = 512K
}

_stack_start = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS {
    .text : {
        __stext = .;

        KEEP(*(.text.start));
        *(.text.reset);
        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    } > ROM

    .rodata : ALIGN(4) {
        . = ALIGN(4);
        __srodata = .;

        *(.srodata .srodata.*);
        *(.rodata .rodata.*);

        . = ALIGN(4);
        __erodata = .;
    } > ROM

    .data : ALIGN(4) {
        . = ALIGN(4);
        __sdata = .;

        __global_pointer$ = . + 0x800;
        *(.sdata .sdata.* .sdata2 .sdata2.*);
        *(.data .data.*);

        . = ALIGN(4);
        __edata = .;
    } > RAM AT > ROM

    __sidata = LOADADDR(.data);

    .bss (NOLOAD) : ALIGN(4) {
        . = ALIGN(4);
        __sbss = .;

        *(.sbss .sbss.* .bss .bss.*);

        . = ALIGN(4);
        __ebss = .;
    } > RAM
}
