include $(sort $(wildcard $(BR2_EXTERNAL_MLOGV32_PATH)/package/*/*.mk))

.PHONY: save-configs
save-configs: linux-update-defconfig busybox-update-config
	$(MAKE) savedefconfig BR2_DEFCONFIG=$(BR2_EXTERNAL_MLOGV32_PATH)/configs/mlogv32_defconfig

.PHONY: dtbs
dtbs: $(BR2_EXTERNAL_MLOGV32_PATH)/board/mlogv32/dts/mlogv32.dtb

.PHONY: gen-compile-commands
gen-compile-commands:
	cd $(LINUX_DIR) && scripts/clang-tools/gen_compile_commands.py -o $(BR2_EXTERNAL_MLOGV32_PATH)/compile_commands.json

.PHONY: zsbl
zsbl:
	riscv32-unknown-elf-gcc \
		-nostartfiles \
		-DZSBL_ROOTFS_PATH=\"$(BINARIES_DIR)/rootfs.cramfs\" \
		-DZSBL_KERNEL_PATH=\"$(BINARIES_DIR)/Image\" \
		-DZSBL_OPENSBI_PATH=\"$(BINARIES_DIR)/fw_jump.bin\" \
		-T$(BR2_EXTERNAL_MLOGV32_PATH)/board/mlogv32/zsbl/zsbl.ld \
		$(BR2_EXTERNAL_MLOGV32_PATH)/board/mlogv32/zsbl/zsbl.S \
		-o $(BINARIES_DIR)/zsbl.elf
	riscv32-unknown-elf-objcopy --output-target binary $(BINARIES_DIR)/zsbl.elf $(BINARIES_DIR)/zsbl.bin

%.dtb: %.dts
	dtc $< -o $@
