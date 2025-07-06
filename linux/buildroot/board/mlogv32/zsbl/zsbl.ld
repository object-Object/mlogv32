OUTPUT_ARCH(riscv)
ENTRY(_start)

MEMORY {
    ROM     (rx)  : ORIGIN = 0x00000000,              LENGTH = 0x400000
    KERNEL  (rx)  : ORIGIN = 0x400000,                LENGTH = 16M - 0x400000
    RAM     (rwx) : ORIGIN = 0x80000000,              LENGTH = 16M - 256K
    PAYLOAD (rwx) : ORIGIN = 0x80000000 + 16M - 256K, LENGTH = 256K
}

SECTIONS {
    .text : {
        KEEP(*(.text.start));
        *(.text .text.*);
    } > ROM

    .rodata : {
        . = ORIGIN(KERNEL);
        *(.rodata.kernel);
        . = ALIGN(4);
        _etext = .;
    } > KERNEL

    .data : {
        . = ALIGN(4);
        _spayload = .;
        *(.data.payload);
        . = ALIGN(4);
        _epayload = .;
    } > PAYLOAD AT > ROM

    _sipayload = LOADADDR(.data);
}
