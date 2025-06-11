#define MLOGSYS_printchar(c) asm volatile (".insn i CUSTOM_0, 0, zero, %0, 1" : : "r" (c) )
#define MLOGSYS_printflush() asm volatile (".insn i CUSTOM_0, 0, zero, zero, 2" : : )
#define MLOGSYS_drawflush() asm volatile (".insn i CUSTOM_0, 0, zero, zero, 3" : : )

#define _declare_MLOGDRAW_0(NAME) \
void MLOGDRAW_ ## NAME ()

#define _create_MLOGDRAW_0(NAME, FUNCT12) \
_declare_MLOGDRAW_0(NAME) \
{ \
    asm volatile (".insn i CUSTOM_0, 1, zero, zero, " #FUNCT12 \
                : \
                : \
                :); \
}

#define _declare_MLOGDRAW_1(NAME) \
void MLOGDRAW_ ## NAME ( \
    unsigned int arg0 \
)

#define _create_MLOGDRAW_1(NAME, FUNCT12) \
_declare_MLOGDRAW_1(NAME) \
{ \
    asm volatile (".insn i CUSTOM_0, 1, zero, %0, " #FUNCT12 \
                : \
                : "r" (arg0) \
                :); \
}

#define _declare_MLOGDRAW_2(NAME) \
void MLOGDRAW_ ## NAME ( \
    unsigned int arg0, \
    unsigned int arg1 \
)

#define _create_MLOGDRAW_2(NAME, FUNCT12) \
_declare_MLOGDRAW_2(NAME) \
{ \
    register ee_ptr_int a1 asm ("a1") = (ee_ptr_int)(arg1); \
    asm volatile (".insn i CUSTOM_0, 1, zero, %0, " #FUNCT12 \
                : \
                : "r" (arg0), "r" (a1) \
                :); \
}

#define _declare_MLOGDRAW_3(NAME) \
void MLOGDRAW_ ## NAME ( \
    unsigned int arg0, \
    unsigned int arg1, \
    unsigned int arg2 \
)

#define _create_MLOGDRAW_3(NAME, FUNCT12) \
_declare_MLOGDRAW_3(NAME) \
{ \
    register ee_ptr_int a1 asm ("a1") = (ee_ptr_int)(arg1); \
    register ee_ptr_int a2 asm ("a2") = (ee_ptr_int)(arg2); \
    asm volatile (".insn i CUSTOM_0, 1, zero, %0, " #FUNCT12 \
                : \
                : "r" (arg0), "r" (a1), "r" (a2) \
                :); \
}

#define _declare_MLOGDRAW_4(NAME) \
void MLOGDRAW_ ## NAME ( \
    unsigned int arg0, \
    unsigned int arg1, \
    unsigned int arg2, \
    unsigned int arg3 \
)

#define _create_MLOGDRAW_4(NAME, FUNCT12) \
_declare_MLOGDRAW_4(NAME) \
{ \
    register ee_ptr_int a1 asm ("a1") = (ee_ptr_int)(arg1); \
    register ee_ptr_int a2 asm ("a2") = (ee_ptr_int)(arg2); \
    register ee_ptr_int a3 asm ("a3") = (ee_ptr_int)(arg3); \
    asm volatile (".insn i CUSTOM_0, 1, zero, %0, " #FUNCT12 \
                : \
                : "r" (arg0), "r" (a1), "r" (a2), "r" (a3) \
                :); \
}

#define _declare_MLOGDRAW_5(NAME) \
void MLOGDRAW_ ## NAME ( \
    unsigned int arg0, \
    unsigned int arg1, \
    unsigned int arg2, \
    unsigned int arg3, \
    unsigned int arg4 \
)

#define _create_MLOGDRAW_5(NAME, FUNCT12) \
_declare_MLOGDRAW_5(NAME) \
{ \
    register ee_ptr_int a1 asm ("a1") = (ee_ptr_int)(arg1); \
    register ee_ptr_int a2 asm ("a2") = (ee_ptr_int)(arg2); \
    register ee_ptr_int a3 asm ("a3") = (ee_ptr_int)(arg3); \
    register ee_ptr_int a4 asm ("a4") = (ee_ptr_int)(arg4); \
    asm volatile (".insn i CUSTOM_0, 1, zero, %0, " #FUNCT12 \
                : \
                : "r" (arg0), "r" (a1), "r" (a2), "r" (a3), "r" (a4) \
                :); \
}

#define _declare_MLOGDRAW_6(NAME) \
void MLOGDRAW_ ## NAME ( \
    unsigned int arg0, \
    unsigned int arg1, \
    unsigned int arg2, \
    unsigned int arg3, \
    unsigned int arg4, \
    unsigned int arg5 \
)

#define _create_MLOGDRAW_6(NAME, FUNCT12) \
_declare_MLOGDRAW_6(NAME) \
{ \
    register ee_ptr_int a1 asm ("a1") = (ee_ptr_int)(arg1); \
    register ee_ptr_int a2 asm ("a2") = (ee_ptr_int)(arg2); \
    register ee_ptr_int a3 asm ("a3") = (ee_ptr_int)(arg3); \
    register ee_ptr_int a4 asm ("a4") = (ee_ptr_int)(arg4); \
    register ee_ptr_int a5 asm ("a5") = (ee_ptr_int)(arg5); \
    asm volatile (".insn i CUSTOM_0, 1, zero, %0, " #FUNCT12 \
                : \
                : "r" (arg0), "r" (a1), "r" (a2), "r" (a3), "r" (a4), "r" (a5) \
                :); \
}

_declare_MLOGDRAW_3(clear);
_declare_MLOGDRAW_4(color);
_declare_MLOGDRAW_1(col);
_declare_MLOGDRAW_1(stroke);
_declare_MLOGDRAW_4(line);
_declare_MLOGDRAW_4(rect);
_declare_MLOGDRAW_4(lineRect);
_declare_MLOGDRAW_5(poly);
_declare_MLOGDRAW_5(linePoly);
_declare_MLOGDRAW_6(triangle);
_declare_MLOGDRAW_6(image);
_declare_MLOGDRAW_2(print);
_declare_MLOGDRAW_2(translate);
_declare_MLOGDRAW_2(scale);
_declare_MLOGDRAW_1(rotate);
_declare_MLOGDRAW_0(reset);
