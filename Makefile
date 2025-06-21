ASM_PROGRAMS = $(patsubst asm/%.s,%,$(wildcard asm/*.s))

RUST_PROGRAMS = $(filter-out webserver,$(patsubst rust/examples/%,%,$(wildcard rust/examples/*)))

MLOG_PROGRAMS = $(patsubst src/%.mlog.jinja,%,$(filter-out src/config/base.mlog.jinja,$(wildcard src/*.mlog.jinja) $(wildcard src/*/*.mlog.jinja)))

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

webserver: FORCE | build/rust
	cd rust/examples/webserver && cargo objcopy --bin server --release -- --output-target binary ../../../build/rust/webserver_server.bin
	cd rust/examples/webserver && cargo objcopy --bin client --release -- --output-target binary ../../../build/rust/webserver_client.bin

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

src/init.mlog: src/main.labels.mlog

# only extract uppercase labels
src/main.labels.mlog: src/main.mlog
	python -m mlogv32.preprocessor labels --filter '[^a-z]+' -o src/main.labels.mlog src/main.mlog

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
