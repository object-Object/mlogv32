/*
source: https://github.com/rust-embedded/riscv/blob/fdc3bb65a258/riscv-rt/link.x.in
*/

ENTRY(_start);

MEMORY {
    /*
    LENGTH = num_ram_procs * 4096*4
    0x10000000 = 128*128 * 4096*4
    0x8000000 = 128*64 * 4096*4
    */
    ram (rwx) : ORIGIN = 0, LENGTH = 0x8000000
}

REGION_ALIAS("REGION_TEXT",   ram);
REGION_ALIAS("REGION_RODATA", ram);
REGION_ALIAS("REGION_DATA",   ram);
REGION_ALIAS("REGION_BSS",    ram);
REGION_ALIAS("REGION_HEAP",   ram);
REGION_ALIAS("REGION_STACK",  ram);

PROVIDE(_stack_start = ORIGIN(REGION_STACK) + LENGTH(REGION_STACK));
PROVIDE(_stack_size = 8M);

/* users can optionally enable the heap by adding another linker script to override this value */
PROVIDE(_heap_size = 0);

SECTIONS {
    .text : {
        __stext = .;

        KEEP(*(.text.start));
        *(.text.reset);
        *(.text .text.*);

        . = ALIGN(4);
        __etext = .;
    } > REGION_TEXT

    .rodata : ALIGN(4) {
        . = ALIGN(4);
        __srodata = .;

        *(.srodata .srodata.*);
        *(.rodata .rodata.*);

        . = ALIGN(4);
        __erodata = .;
    } > REGION_RODATA

    .data : ALIGN(4) {
        . = ALIGN(4);
        __sdata = .;

        PROVIDE(__global_pointer$ = . + 0x800);
        *(.sdata .sdata.* .sdata2 .sdata2.*);
        *(.data .data.*);
    } > REGION_DATA AT > REGION_RODATA

    . = ALIGN(4);
    __edata = .;

    __sidata = LOADADDR(.data);

    .bss (NOLOAD) : ALIGN(4) {
        . = ALIGN(4);
        __sbss = .;

        *(.sbss .sbss.* .bss .bss.*);
    } > REGION_BSS

    . = ALIGN(4);
    __ebss = .;

    /* fictitious region that represents the memory available for the heap */
    .heap (NOLOAD) : {
        __sheap = .;
        . += _heap_size;
        . = ALIGN(4);
        __eheap = .;
    } > REGION_HEAP

    /* fictitious region that represents the memory available for the stack */
    .stack (NOLOAD) : {
        __estack = .;
        . = ABSOLUTE(_stack_start);
        __sstack = .;
    } > REGION_STACK

    /* fake output .got section */
    /* Dynamic relocations are unsupported. This section is only used to detect
       relocatable code in the input files and raise an error if relocatable code
       is found */
    .got (INFO) :
    {
        KEEP(*(.got .got.*));
    }
}

/* Do not exceed this mark in the error messages above                                    | */
ASSERT(ORIGIN(REGION_TEXT) % 4 == 0, "
ERROR(mlogv32): the start of the REGION_TEXT must be 4-byte aligned");

ASSERT(ORIGIN(REGION_RODATA) % 4 == 0, "
ERROR(mlogv32): the start of the REGION_RODATA must be 4-byte aligned");

ASSERT(ORIGIN(REGION_DATA) % 4 == 0, "
ERROR(mlogv32): the start of the REGION_DATA must be 4-byte aligned");

ASSERT(ORIGIN(REGION_HEAP) % 4 == 0, "
ERROR(mlogv32): the start of the REGION_HEAP must be 4-byte aligned");

ASSERT(ORIGIN(REGION_STACK) % 4 == 0, "
ERROR(mlogv32): the start of the REGION_STACK must be 4-byte aligned");

ASSERT(__sdata % 4 == 0 && __edata % 4 == 0, "
BUG(mlogv32): .data is not 4-byte aligned");

ASSERT(__sidata % 4 == 0, "
BUG(mlogv32): the LMA of .data is not 4-byte aligned");

ASSERT(__sbss % 4 == 0 && __ebss % 4 == 0, "
BUG(mlogv32): .bss is not 4-byte aligned");

ASSERT(__sheap % 4 == 0, "
BUG(mlogv32): start of .heap is not 4-byte aligned");

ASSERT(SIZEOF(.stack) > _stack_size, "
ERROR(mlogv32): .stack section is too small for allocating the stack.
Consider changing `_stack_size`.");

/* # Other checks */
ASSERT(SIZEOF(.got) == 0, "
ERROR(mlogv32): .got section detected in the input files. Dynamic relocations are not
supported. If you are linking to C code compiled using the `cc` crate then modify your
build script to compile the C code _without_ the -fPIC flag. See the documentation of
the `cc::Build.pic` method for details.");

/* Do not exceed this mark in the error messages above                                    | */
