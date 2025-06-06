#ifndef _COMPLIANCE_MODEL_H
#define _COMPLIANCE_MODEL_H
#define RVMODEL_DATA_SECTION \
        .align 8; .global begin_regstate; begin_regstate:               \
        .word 128;                                                      \
        .align 8; .global end_regstate; end_regstate:                   \
        .word 4;

//RV_COMPLIANCE_HALT
#define RVMODEL_HALT                                              \
  .insn i CUSTOM_0, 0, zero, zero, 0;

#define RVMODEL_BOOT \
  .word __etext; \
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
  la t0, __sbss; \
  la t1, __ebss; \
mlogv32_clear_bss: \
  bgeu t0, t1, mlogv32_bss_done; \
  sb zero, 0(t0); \
  addi t0, t0, 1; \
  j mlogv32_clear_bss; \
mlogv32_bss_done:

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
#define RVMODEL_IO_WRITE_STR(_R, _STR)
//RVTEST_IO_CHECK
#define RVMODEL_IO_CHECK()
//RVTEST_IO_ASSERT_GPR_EQ
#define RVMODEL_IO_ASSERT_GPR_EQ(_S, _R, _I)
//RVTEST_IO_ASSERT_SFPR_EQ
#define RVMODEL_IO_ASSERT_SFPR_EQ(_F, _R, _I)
//RVTEST_IO_ASSERT_DFPR_EQ
#define RVMODEL_IO_ASSERT_DFPR_EQ(_D, _R, _I)

#define RVMODEL_SET_MSW_INT

#define RVMODEL_CLEAR_MSW_INT

#define RVMODEL_CLEAR_MTIMER_INT

#define RVMODEL_CLEAR_MEXT_INT


#endif // _COMPLIANCE_MODEL_H
