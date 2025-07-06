.PHONY: load-configs
load-configs: mlogv32_defconfig

.PHONY: save-configs
save-configs: linux-update-defconfig
	$(MAKE) savedefconfig BR2_DEFCONFIG=$(BR2_EXTERNAL_MLOGV32_PATH)/configs/mlogv32_defconfig

.PHONY: dtbs
dtbs: $(BR2_EXTERNAL_MLOGV32_PATH)/board/mlogv32/dts/mlogv32.dtb

.PHONY: zsbl
zsbl:
	riscv32-unknown-elf-gcc \
		-nostartfiles \
		-DZSBL_PAYLOAD_PATH=\"$(BINARIES_DIR)/fw_jump.bin\" \
		-DZSBL_KERNEL_PATH=\"$(BINARIES_DIR)/Image\" \
		-T$(BR2_EXTERNAL_MLOGV32_PATH)/board/mlogv32/zsbl/zsbl.ld \
		$(BR2_EXTERNAL_MLOGV32_PATH)/board/mlogv32/zsbl/zsbl.S \
		-o $(BINARIES_DIR)/zsbl.elf
	riscv32-unknown-elf-objcopy --output-target binary $(BINARIES_DIR)/zsbl.elf $(BINARIES_DIR)/zsbl.bin

%.dtb: %.dts
	dtc $< -o $@
