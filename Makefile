ASM_PROGRAMS = $(patsubst asm/%.s,%,$(wildcard asm/*.s))
RUST_PROGRAMS = $(filter-out mlogv32,$(patsubst rust/%,%,$(wildcard rust/*)))

.PHONY: all
all: asm rust

.PHONY: asm
asm: $(ASM_PROGRAMS)

.PHONY: rust
rust: $(RUST_PROGRAMS)

$(ASM_PROGRAMS): %: build/%-0.mlog build/%.bin build/%.dump

$(RUST_PROGRAMS): %: build/rust/%-0.mlog build/rust/%.bin

# see https://stackoverflow.com/a/61960833
build/%-0.mlog: build/%.bin scripts/bin_to_mlog.py
	-rm -f build/$*-[0-9].mlog build/$*-[0-9][0-9].mlog
	python scripts/bin_to_mlog.py build/$*.bin

build/rust/%.bin: | build/rust
	cd rust/$* && cargo robjcopy ../../build/rust/$*.bin

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
