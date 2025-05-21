typedef enum {
    Halt,
    PrintChar,
    PrintFlush,
    DrawClear,
    DrawColor,
    DrawCol,
    DrawStroke,
    DrawLine,
    DrawRect,
    DrawLineRect,
    DrawPoly,
    DrawLinePoly,
    DrawTriangle,
    DrawImage,
    DrawPrint,
    DrawTranslate,
    DrawScale,
    DrawRotate,
    DrawReset,
    DrawFlush,
} Syscall;

unsigned int ecall(
    unsigned int arg0,
    unsigned int arg1,
    unsigned int arg2,
    unsigned int arg3,
    unsigned int arg4,
    unsigned int arg5,
    unsigned int arg6,
    Syscall which
);