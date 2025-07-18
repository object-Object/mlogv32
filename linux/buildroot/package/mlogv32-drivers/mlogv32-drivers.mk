################################################################################
#
# Linux kernel drivers for mlogv32
#
################################################################################

MLOGV32_DRIVERS_VERSION = 0.1.0
MLOGV32_DRIVERS_SITE = $(MLOGV32_DRIVERS_PKGDIR)/src
MLOGV32_DRIVERS_SITE_METHOD = local

$(eval $(generic-package))
