THIS_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

BR2_EXTERNAL_SRC := $(THIS_DIR)/buildroot

BUILDROOT_RELEASE ?= https://buildroot.org/downloads/buildroot-2025.02.4.tar.gz

BUILDROOT ?= $(HOME)/buildroot
BR2_EXTERNAL ?= $(HOME)/br2_external

MAKE_BUILDROOT = $(MAKE) -C $(BUILDROOT) BR2_EXTERNAL=$(BR2_EXTERNAL)

.DEFAULT_GOAL := all

.PHONY: setup-buildroot
setup-buildroot:
	curl --location "$(BUILDROOT_RELEASE)" | tar xzv --directory $(BUILDROOT)

.PHONY: everything
everything: load-configs dtbs all opensbi-rebuild zsbl get-images

.PHONY: dtbs-rebuild
dtbs-rebuild: dtbs opensbi-rebuild zsbl get-images

.PHONY: load-configs
load-configs: mlogv32_defconfig

.PHONY: get-images
get-images:
	rm -rf $(THIS_DIR)/output

	mkdir -p $(THIS_DIR)/output/images
	cp -r $(BUILDROOT)/output/images $(THIS_DIR)/output

	mkdir -p $(THIS_DIR)/output/build
	cp $(BUILDROOT)/output/build/linux-*/vmlinux $(THIS_DIR)/output/build

.PHONY: dump-images
dump-images:
	-riscv32-unknown-linux-gnu-objdump \
		--wide \
		--disassemble \
		$(THIS_DIR)/output/images/fw_jump.elf > $(THIS_DIR)/output/images/fw_jump.dump

	-riscv32-unknown-linux-gnu-objdump \
		--wide \
		--disassemble \
		--show-all-symbols \
		--section .text \
		--section .loader \
		$(THIS_DIR)/output/images/zsbl.elf > $(THIS_DIR)/output/images/zsbl.dump

	-riscv32-unknown-linux-gnu-objdump \
		--wide \
		--disassemble \
		$(THIS_DIR)/output/build/vmlinux > $(THIS_DIR)/output/build/vmlinux.dump

# copy this directory to/from BR2_EXTERNAL to make buildroot run faster when this directory is in a Windows Docker volume
%:
ifeq ($(BR2_EXTERNAL_SRC),$(BR2_EXTERNAL))
	$(MAKE_BUILDROOT) $@
else
	rsync --archive --delete $(BR2_EXTERNAL_SRC)/ $(BR2_EXTERNAL)
	-$(MAKE_BUILDROOT) $@
	cp -r --update --no-target-directory $(BR2_EXTERNAL) $(BR2_EXTERNAL_SRC)
endif
