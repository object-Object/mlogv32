#include <stdint.h>
#include "init.h"

// Python internal features.
#define MICROPY_ENABLE_GC                       (1)
#define MICROPY_HELPER_REPL                     (1)
#define MICROPY_ERROR_REPORTING                 (MICROPY_ERROR_REPORTING_TERSE)
#define MICROPY_FLOAT_IMPL                      (MICROPY_FLOAT_IMPL_FLOAT)

#define MICROPY_EMIT_RV32                       (1)
#define MICROPY_EMIT_INLINE_RV32                (1)

#define MICROPY_CONFIG_ROM_LEVEL                (MICROPY_CONFIG_ROM_LEVEL_CORE_FEATURES)

// Fine control over Python builtins, classes, modules, etc.
#define MICROPY_PY_ASYNC_AWAIT                  (0)
#define MICROPY_PY_IO                           (0)

#define MICROPY_PY_BUILTINS_HELP                (1)
#define MICROPY_PY_BUILTINS_HELP_MODULES        (1)
#define MICROPY_PY_FSTRINGS                     (1)
#define MICROPY_PY_MATH_CONSTANTS               (1)
#define MICROPY_PY_MATH_FACTORIAL               (1)
#define MICROPY_PY_PLATFORM                     (1)
#define MICROPY_PY_RANDOM                       (1)

#define MICROPY_PY_ASYNCIO                      (0)
#define MICROPY_PY_IO_IOBASE                    (0)
#define MICROPY_PY_JSON                         (0)
#define MICROPY_PY_OS                           (0)
#define MICROPY_PY_SELECT                       (0)
#define MICROPY_PY_SELECT_SELECT                (0)
#define MICROPY_PY_SYS_PS1_PS2                  (0)
#define MICROPY_PY_SYS_STDFILES                 (0)
#define MICROPY_PY_SYS_STDIO_BUFFER             (0)
#define MICROPY_PY_TIME                         (0)

// Type definitions for the specific machine.

typedef intptr_t mp_int_t; // must be pointer size
typedef uintptr_t mp_uint_t; // must be pointer size
typedef long mp_off_t;

// We need to provide a declaration/definition of alloca().
#include <alloca.h>

// Define the port's name and hardware.
#define MICROPY_HW_BOARD_NAME "mindustry"
#define MICROPY_HW_MCU_NAME   "mlogv32"

#define MP_STATE_PORT MP_STATE_VM

#define MICROPY_PORT_INIT_FUNC init()
#define MICROPY_PORT_DEINIT_FUNC deinit()
