ASM_PROGRAMS = $(patsubst asm/%.s,%,$(wildcard asm/*.s))

RUST_PROGRAMS = $(patsubst rust/examples/%,%,$(wildcard rust/examples/*))

MLOG_PROGRAMS = $(patsubst src/%.mlog.jinja,%,$(wildcard src/*.mlog.jinja))

.PHONY: all
all: asm rust

.PHONY: asm
asm: $(ASM_PROGRAMS)

.PHONY: rust
rust: $(RUST_PROGRAMS)

.PHONY: mlog
mlog: $(MLOG_PROGRAMS) mlog-configs

.PHONY: coremark
coremark:
	cd coremark/coremark && $(MAKE) PORT_DIR=../mlogv32 ITERATIONS=10 clean load

$(ASM_PROGRAMS): %: build/%.bin build/%.dump

$(RUST_PROGRAMS): %: build/rust/examples/%.bin

$(MLOG_PROGRAMS): %: src/%.mlog

# see https://stackoverflow.com/a/61960833
build/%-0.mlog: build/%.bin scripts/bin_to_mlog.py
	-rm -f build/$*-[0-9].mlog build/$*-[0-9][0-9].mlog
	python -m mlogv32.scripts.bin_to_mlog build/$*.bin

build/rust/examples/%.bin: FORCE | build/rust
	cd rust/examples/$* && cargo robjcopy ../../../build/rust/$*.bin
	cd rust/examples/$* && cargo objdump --release -- --disassemble > ../../../build/rust/$*.dump

build/%.bin: build/%.out
	riscv32-unknown-elf-objcopy --output-target binary build/$*.out build/$*.bin

build/%.dump: build/%.out
	riscv32-unknown-elf-objdump --disassemble build/$*.out > build/$*.dump

build/%.out: build/%.o
	riscv32-unknown-elf-ld --script=link.x -o build/$*.out build/$*.o

build/%.o: asm/%.s | build
	riscv32-unknown-elf-gcc --compile -march=rv32ima_zicsr -o build/$*.o asm/$*.s

src/%.mlog: src/%.mlog.jinja
	python -m mlogv32.preprocessor file -o src/$*.mlog src/$*.mlog.jinja

.PHONY: mlog-configs
mlog-configs: src/config/configs.yaml
	python -m mlogv32.preprocessor configs src/config/configs.yaml

build:
	mkdir -p build

build/rust:
	mkdir -p build/rust

.PHONY: clean
clean:
	rm -rf build

.PHONY: clean-rust
clean-rust:
	cd rust && cargo clean

.PHONY: clean-coremark
clean-coremark:
	cd coremark/coremark && $(MAKE) PORT_DIR=../mlogv32 clean

.PHONY: FORCE
FORCE:
