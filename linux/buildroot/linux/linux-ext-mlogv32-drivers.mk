################################################################################
#
# Linux kernel drivers for mlogv32
#
################################################################################

LINUX_EXTENSIONS += mlogv32-drivers

define MLOGV32_DRIVERS_PREPARE_KERNEL
	mkdir -p $(LINUX_DIR)/drivers/mlogv32
	cp -dpfr $(MLOGV32_DRIVERS_DIR)/* $(LINUX_DIR)/drivers/mlogv32/
	echo 'obj-y += mlogv32/' >> $(LINUX_DIR)/drivers/Makefile
endef
