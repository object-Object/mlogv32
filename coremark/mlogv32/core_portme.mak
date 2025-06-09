# Copyright 2018 Embedded Microprocessor Benchmark Consortium (EEMBC)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# Original Author: Shay Gal-on

#File : core_portme.mak

RISCV_ARCH = rv32ima_zicsr

# Flag : OUTFLAG
#	Use this flag to define how to to get an executable (e.g -o)
OUTFLAG= -o
# Flag : CC
#	Use this flag to define compiler to use
CC 		= riscv32-unknown-elf-gcc
# Flag : LD
#	Use this flag to define compiler to use
LD		= riscv32-unknown-elf-gcc
# Flag : AS
#	Use this flag to define compiler to use
AS		= riscv32-unknown-elf-gcc
# Flag : CFLAGS
#	Use this flag to define compiler options. Note, you can add compiler options from the command line using XCFLAGS="other flags"
PORT_CFLAGS = -march=$(RISCV_ARCH) -O0 -g -ffreestanding
FLAGS_STR = "$(strip $(PORT_CFLAGS) $(XCFLAGS) $(XLFLAGS) $(LFLAGS_END)) "
CFLAGS = $(PORT_CFLAGS) --compile -I$(PORT_DIR) -I. -DFLAGS_STR=\"$(FLAGS_STR)\" 
#Flag : LFLAGS_END
#	Define any libraries needed for linking or other flags that should come at the end of the link line (e.g. linker scripts). 
#	Note : On certain platforms, the default clock_gettime implementation is supported but requires linking of librt.
SEPARATE_COMPILE=1
# Flag : SEPARATE_COMPILE
# You must also define below how to create an object file, and how to link.
OBJOUT 	= -o
LFLAGS 	= -T$(PORT_DIR)/../../rust/mlogv32/link.x
ASFLAGS = --compile -march=$(RISCV_ARCH)
OFLAG 	= -o
COUT 	= -c

LFLAGS_END = -nostartfiles -nolibc
# Flag : PORT_SRCS
# 	Port specific source files can be added here
#	You may also need cvt.c if the fcvt functions are not provided as intrinsics by your compiler!
PORT_SRCS = $(PORT_DIR)/core_portme.c $(PORT_DIR)/ee_printf.c $(PORT_DIR)/xmlogsys.c $(PORT_DIR)/entry.s $(PORT_DIR)/cvt.c
vpath %.c $(PORT_DIR)
vpath %.s $(PORT_DIR)

PORT_OBJS = $(PORT_DIR)/core_portme.o $(PORT_DIR)/ee_printf.o $(PORT_DIR)/xmlogsys.o $(PORT_DIR)/entry.o $(PORT_DIR)/cvt.o

# Flag : LOAD
#	For a simple port, we assume self hosted compile and run, no load needed.

# Flag : RUN
#	For a simple port, we assume self hosted compile and run, simple invocation of the executable

LOAD = echo "Please set LOAD to the process of loading the executable to the flash"
RUN = echo "Please set LOAD to the process of running the executable (e.g. via jtag, or board reset)"

OEXT = .o
EXE = .out

$(OPATH)$(PORT_DIR)/%$(OEXT) : %.c
	$(CC) $(CFLAGS) $(XCFLAGS) $(COUT) $< $(OBJOUT) $@

$(OPATH)%$(OEXT) : %.c
	$(CC) $(CFLAGS) $(XCFLAGS) $(COUT) $< $(OBJOUT) $@

$(OPATH)$(PORT_DIR)/%$(OEXT) : %.s
	$(AS) $(ASFLAGS) $< $(OBJOUT) $@

PORT_CLEAN = $(OPATH)coremark.bin $(OPATH)coremark.dump

.PHONY: port_prebuild
port_prebuild:

# Target: port_postbuild
# Generate any files that are needed after actual build end.
# E.g. change format to srec, bin, zip in order to be able to load into flash
.PHONY: port_postbuild
port_postbuild:
	riscv32-unknown-elf-objcopy --output-target binary $(OUTFILE) $(OPATH)coremark.bin
	riscv32-unknown-elf-objdump --disassemble $(OUTFILE) > $(OPATH)coremark.dump

# Target: port_prerun
# 	Do platform specific before run stuff. 
#	E.g. reset the board, backup the logfiles etc.
.PHONY: port_prerun
port_prerun:

# Target: port_postrun
# 	Do platform specific after run stuff. 
#	E.g. reset the board, backup the logfiles etc.
.PHONY: port_postrun
port_postrun:

# Target: port_preload
# 	Do platform specific before load stuff. 
#	E.g. reset the reset power to the flash eraser
.PHONY: port_preload
port_preload:

# Target: port_postload
# 	Do platform specific after load stuff. 
#	E.g. reset the reset power to the flash eraser
.PHONY: port_postload
port_postload:

# FLAG : OPATH
# Path to the output folder. Default - current folder.
OPATH = ./
MKDIR = mkdir -p

