OUTPUT_ARCH(riscv)
ENTRY(_start)

/* memory size definitions */
__ROM = 16M;
__RAM = 16M;

MEMORY {
    /* ROM */
    ROM (rx) : ORIGIN = 0x00000000, LENGTH = __ROM

    /* RAM */
    RAM     (rwx) : ORIGIN = 0x80000000,                LENGTH = __RAM - 256K
    OPENSBI (rwx) : ORIGIN = 0x80000000 + __RAM - 256K, LENGTH = 256K
}

SECTIONS {
    .text : {
        . = ALIGN(4);
        *(.text);
        . = ALIGN(4);
    } > ROM

    .rodata : {
        . = ALIGN(4);
        *(.rodata);
        . = ALIGN(4);
    } > ROM

    /* rootfs must be page-aligned, and we need to know the exact address for the dts */
    .rootfs : {
        . = ALIGN(4K);
        _srootfs = .;
        *(.rootfs);
        . = ALIGN(4K);
        _erootfs = .;
    } > ROM

    .kernel : {
        . = ALIGN(4);
        _skernel = .;
        *(.kernel);
        . = ALIGN(4);
        _ekernel = .;
    } > RAM AT > ROM

    _sikernel = LOADADDR(.kernel);

    OVERLAY : {
        .loader {
            . = ALIGN(4);
            _sloader = .;
            *(.loader);
            . = ALIGN(4);
            _eloader = .;
        }

        .opensbi {
            . = ALIGN(4);
            _sopensbi = .;
            *(.opensbi);
            . = ALIGN(4);
            _eopensbi = .;
        }
    } > OPENSBI AT > ROM

    _siloader = LOADADDR(.loader);
    _siopensbi = LOADADDR(.opensbi);
}

ASSERT(_srootfs == 0x1000, "Incorrect rootfs start address, update dts");
