#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

# Partitions
BOARD_SUPER_PARTITION_SIZE := 14956888064

# Include the common OEM chipset BoardConfig.
include device/oneplus/sm8750-common/BoardConfigCommon.mk

DEVICE_PATH := device/oneplus/pagani

# Assert
TARGET_OTA_ASSERT_DEVICE := OP60F5L1

# Display
TARGET_SCREEN_DENSITY := 480

# Kernel
TARGET_KERNEL_ADDITIONAL_FLAGS += CONFIG_PAGANI_DTB=y

# Opt in to the primary optical UDFPS compatibility path for this product.
TARGET_KERNEL_ADDITIONAL_FLAGS += KCFLAGS+=-DOPLUS_OFP_UIREADY_COMPAT=1

# Properties
TARGET_ODM_PROP += $(DEVICE_PATH)/properties/odm.prop
TARGET_SYSTEM_EXT_PROP += $(DEVICE_PATH)/properties/system_ext.prop
TARGET_VENDOR_PROP += $(DEVICE_PATH)/properties/vendor.prop

# Recovery
TARGET_RECOVERY_UI_MARGIN_HEIGHT := 103

# Include the proprietary files BoardConfig.
include vendor/oneplus/pagani/BoardConfigVendor.mk

BUILD_BROKEN_VENDOR_PROPERTY_NAMESPACE := true

# Pagani-only Dolby DMS service policy and stable AIDL compatibility.
BOARD_VENDOR_SEPOLICY_DIRS += vendor/oneplus/dolby-pagani/sepolicy/vendor
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += vendor/oneplus/dolby-pagani/configs/vintf/dms-framework-matrix.xml
