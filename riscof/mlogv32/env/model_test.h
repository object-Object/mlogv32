#ifndef _COMPLIANCE_MODEL_H
#define _COMPLIANCE_MODEL_H
#define RVMODEL_DATA_SECTION \
        .align 8; .global begin_regstate; begin_regstate:               \
        .word 128;                                                      \
        .align 8; .global end_regstate; end_regstate:                   \
        .word 4;

//RV_COMPLIANCE_HALT
#define RVMODEL_HALT                                              \
  li t0, 0xfffffff0; \
  sw zero, 0(t0);

// initialize icache, uart0, .text, .data, and .bss
// see https://github.com/riscv-non-isa/riscv-arch-test/issues/202
#define RVMODEL_BOOT \
  .option norelax; \
  .section .text.init.rom; \
  \
  la t0, __etext_rom; \
  .insn i CUSTOM_0, 0, zero, t0, 0; \
  \
  li t0, 0xf0000010; \
  li t1, 0b111; \
  sb t1, 0x08(t0); \
  \
  la t0, __sitext; \
  la t1, __stext; \
  la t2, __etext; \
  beqz t2, mlogv32_text_done; \
mlogv32_load_text: \
  bgeu t1, t2, mlogv32_text_done; \
  lb t3, 0(t0); \
  sb t3, 0(t1); \
  addi t0, t0, 1; \
  addi t1, t1, 1; \
  j mlogv32_load_text; \
mlogv32_text_done: \
  \
  la t0, __sidata; \
  la t1, __sdata; \
  la t2, __edata; \
mlogv32_load_data: \
  bgeu t1, t2, mlogv32_data_done; \
  lb t3, 0(t0); \
  sb t3, 0(t1); \
  addi t0, t0, 1; \
  addi t1, t1, 1; \
  j mlogv32_load_data; \
mlogv32_data_done: \
  \
  la t0, __sbss; \
  la t1, __ebss; \
mlogv32_clear_bss: \
  bgeu t0, t1, mlogv32_bss_done; \
  sb zero, 0(t0); \
  addi t0, t0, 1; \
  j mlogv32_clear_bss; \
mlogv32_bss_done: \
  \
  RVMODEL_IO_WRITE_STR(t0, "\n--- ", MLOGV32_TEST_NAME, " ---\n") \
  \
  tail rvtest_init;

//RV_COMPLIANCE_DATA_BEGIN
#define RVMODEL_DATA_BEGIN                                              \
  RVMODEL_DATA_SECTION                                                        \
  .align 4;\
  .global begin_signature; begin_signature:

//RV_COMPLIANCE_DATA_END
#define RVMODEL_DATA_END                                                      \
  .align 4;\
  .global end_signature; end_signature:  

//RVTEST_IO_INIT
#define RVMODEL_IO_INIT
//RVTEST_IO_WRITE_STR
#define RVMODEL_IO_WRITE_STR(ScrReg, ...) \
  la ScrReg, 2f; \
  sw a0, 0(ScrReg); \
  sw a1, 4(ScrReg); \
  sw a2, 8(ScrReg); \
  la a2, 3f; \
0: \
  lbu a0, 0(a2); \
  beqz a0, 1f; \
  li a1, 0xf0000010; \
  sb a0, 0(a1); \
  addi a2, a2, 1; \
  j 0b; \
1: \
  la ScrReg, 2f; \
  lw a0, 0(ScrReg); \
  lw a1, 4(ScrReg); \
  lw a2, 8(ScrReg); \
  .pushsection .data.string,"aw",@progbits; \
  .balign 4; \
2: .word 0, 0, 0; \
3: .ascii __VA_ARGS__; .byte 0; \
  .popsection;

#define MLOGV32_IO_WRITE_HEX__CHAR(Shift) \
  srli a0, a2, Shift; \
  andi a0, a0, 0xf; \
  addi a0, a0, 48; \
  li a1, 58; \
  bltu a0, a1, 0f; \
  addi a0, a0, 7; \
0: \
  li a1, 0xf0000010; \
  sb a0, 0(a1);

#define MLOGV32_IO_WRITE_HEX(ScrReg, Reg) \
  la ScrReg, 1f; \
  sw Reg, 0(ScrReg); \
  sw a0, 4(ScrReg); \
  sw a1, 8(ScrReg); \
  sw a2, 12(ScrReg); \
  lw a2, 0(ScrReg); \
  \
  MLOGV32_IO_WRITE_HEX__CHAR(28) \
  MLOGV32_IO_WRITE_HEX__CHAR(24) \
  MLOGV32_IO_WRITE_HEX__CHAR(20) \
  MLOGV32_IO_WRITE_HEX__CHAR(16) \
  MLOGV32_IO_WRITE_HEX__CHAR(12) \
  MLOGV32_IO_WRITE_HEX__CHAR(8) \
  MLOGV32_IO_WRITE_HEX__CHAR(4) \
  MLOGV32_IO_WRITE_HEX__CHAR(0) \
  \
  la ScrReg, 2f; \
  lw Reg, 0(ScrReg); \
  lw a0, 4(ScrReg); \
  lw a1, 8(ScrReg); \
  lw a2, 12(ScrReg); \
  .pushsection .data.string,"aw",@progbits; \
  .balign 4; \
1: .word 0, 0, 0, 0; \
  .popsection;

//RVTEST_IO_CHECK
#define RVMODEL_IO_CHECK()
//RVTEST_IO_ASSERT_GPR_EQ
#define RVMODEL_IO_ASSERT_GPR_EQ(ScrReg, Reg, Value) \
  li ScrReg, Value; \
  beq ScrReg, Reg, 4f; \
  RVMODEL_IO_WRITE_STR(ScrReg, "Expected ", #Reg, " == ", #Value, ", got 0x") \
  MLOGV32_IO_WRITE_HEX(ScrReg, Reg) \
  RVMODEL_IO_WRITE_STR(ScrReg, "\n") \
4:
//RVTEST_IO_ASSERT_SFPR_EQ
#define RVMODEL_IO_ASSERT_SFPR_EQ(_F, _R, _I)
//RVTEST_IO_ASSERT_DFPR_EQ
#define RVMODEL_IO_ASSERT_DFPR_EQ(_D, _R, _I)

#define RVMODEL_SET_MSW_INT

#define RVMODEL_CLEAR_MSW_INT

#define RVMODEL_CLEAR_MTIMER_INT

#define RVMODEL_CLEAR_MEXT_INT


#endif // _COMPLIANCE_MODEL_H
