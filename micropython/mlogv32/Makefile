# Include the core environment definitions; this will set $(TOP).
include ../micropython/py/mkenv.mk

# Include py core make definitions.
include $(TOP)/py/py.mk
include $(TOP)/extmod/extmod.mk

# Define toolchain and other tools.
CROSS_COMPILE ?= riscv32-unknown-elf-

# Set CFLAGS and libraries.
RV32_ARCH ?= rv32ima_zicsr
RV32_ABI = ilp32

AFLAGS += -march=$(RV32_ARCH) -mabi=$(RV32_ABI)
CFLAGS += -march=$(RV32_ARCH) -mabi=$(RV32_ABI) -ffreestanding -I. -I$(BUILD) -I$(TOP)
LDFLAGS += -march=$(RV32_ARCH) -mabi=$(RV32_ABI) -nostartfiles -Tlink.x

LIBS += -lm

ifeq ($(DEBUG), 1)
CFLAGS += -Og
else
CFLAGS += -Os
endif

# Define the required source files.
SRC_C = \
	init.c \
	main.c \
	mphalport.c \
	shared/readline/readline.c \
	shared/runtime/gchelper_generic.c \
	shared/runtime/pyexec.c \
	shared/runtime/stdout_helpers.c \

SRC_S = \
	entry.s \

# Define source files containing qstrs.
SRC_QSTR += shared/readline/readline.c shared/runtime/pyexec.c

# Define the required object files.
OBJ = $(PY_O) $(addprefix $(BUILD)/, $(SRC_C:.c=.o) $(SRC_S:.s=.o))

# Define the top-level target, the main firmware.
all: $(BUILD)/firmware.bin $(BUILD)/firmware.elf

# Define how to build the firmware.
$(BUILD)/firmware.elf: $(OBJ)
	$(ECHO) "LINK $@"
	$(Q)$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)
	$(Q)$(SIZE) $@

$(BUILD)/firmware.bin: $(BUILD)/firmware.elf
	$(ECHO) "GEN $@"
	$(Q)$(OBJCOPY) --output-target binary $< $@

# Include remaining core make rules.
include $(TOP)/py/mkrules.mk
