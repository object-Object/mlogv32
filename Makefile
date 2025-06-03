ASM_PROGRAMS = $(patsubst asm/%.s,%,$(wildcard asm/*.s))

RUST_PROJECTS = $(patsubst rust/%,%,$(wildcard rust/*))
RUST_PROGRAMS = $(filter-out mlogv32,$(RUST_PROJECTS))

.PHONY: all
all: asm rust

.PHONY: asm
asm: $(ASM_PROGRAMS)

.PHONY: rust
rust: $(RUST_PROGRAMS)

.PHONY: coremark
coremark:
	cd coremark/coremark && $(MAKE) PORT_DIR=../mlogv32 ITERATIONS=10 clean load

$(ASM_PROGRAMS): %: build/%.bin build/%.dump

$(RUST_PROGRAMS): %: build/rust/%.bin

# see https://stackoverflow.com/a/61960833
build/%-0.mlog: build/%.bin scripts/bin_to_mlog.py
	-rm -f build/$*-[0-9].mlog build/$*-[0-9][0-9].mlog
	python scripts/bin_to_mlog.py build/$*.bin

build/rust/%.bin: FORCE | build/rust
	cd rust/$* && cargo robjcopy ../../build/rust/$*.bin
	cd rust/$* && cargo objdump --release -- --disassemble > ../../build/rust/$*.dump

build/%.bin: build/%.out
	riscv32-unknown-elf-objcopy --output-target binary build/$*.out build/$*.bin

build/%.dump: build/%.out
	riscv32-unknown-elf-objdump --disassemble build/$*.out > build/$*.dump

build/%.out: build/%.o
	riscv32-unknown-elf-ld --script=rust/mlogv32/link.x -o build/$*.out build/$*.o

build/%.o: asm/%.s | build
	riscv32-unknown-elf-gcc --compile -o build/$*.o asm/$*.s

build:
	mkdir -p build

build/rust:
	mkdir -p build/rust

.PHONY: clean
clean:
	rm -rf build

.PHONY: clean-rust
clean-rust: $(addprefix clean-rust/,$(RUST_PROJECTS))

clean-rust/%:
	cd rust/$* && cargo clean

.PHONY: clean-coremark
clean-coremark:
	cd coremark/coremark && $(MAKE) PORT_DIR=../mlogv32 clean

.PHONY: FORCE
FORCE:
