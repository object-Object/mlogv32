ASM_PROGRAMS = $(patsubst asm/%.s,%,$(wildcard asm/*.s))
RUST_PROGRAMS = $(filter-out mlogv32,$(patsubst rust/%,%,$(wildcard rust/*)))

.PHONY: all
all: asm rust

.PHONY: asm
asm: $(ASM_PROGRAMS)

.PHONY: rust
rust: $(RUST_PROGRAMS)

$(ASM_PROGRAMS): %: build/%.mlog build/%.bin build/%.dump

$(RUST_PROGRAMS): %: | build/rust
	cd rust/$* && cargo robjcopy ../../build/rust/$*.bin
	python scripts/dump.py build/rust/$*.bin > build/rust/$*.mlog

# using python3 here because that works in wsl lmao
build/%.mlog: build/%.bin
	python3 scripts/dump.py build/$*.bin > build/$*.mlog

build/%.bin: build/%.out
	riscv64-unknown-elf-objcopy --output-target binary build/$*.out build/$*.bin

build/%.dump: build/%.out
	riscv64-unknown-elf-objdump --disassemble build/$*.out > build/$*.dump

build/%.out: build/%.o
	riscv64-unknown-elf-ld -melf32lriscv --script=rust/mlogv32/link.x -o build/$*.out build/$*.o

build/%.o: asm/%.s | build
	clang --target=riscv32 -march=rv32i --compile -o build/$*.o asm/$*.s

build:
	mkdir -p build

build/rust:
	mkdir -p build/rust

.PHONY: clean
clean:
	rm -rf build
