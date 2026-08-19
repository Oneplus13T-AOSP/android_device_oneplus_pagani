#
# Copyright (C) 2021-2025 The LineageOS Project
#
# SPDX-License-Identifier: Apache-2.0
#

# Inherit from those products. Most specific first.
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Inherit from pagani device
$(call inherit-product, device/oneplus/pagani/device.mk)

# Inherit some common PixelOS stuff.
$(call inherit-product, vendor/custom/config/common_full_phone.mk)

# Inherit BCR
$(call inherit-product, vendor/bcr/bcr.mk)

PRODUCT_NAME := custom_pagani
PRODUCT_DEVICE := pagani
PRODUCT_MANUFACTURER := OnePlus
PRODUCT_BRAND := OnePlus
PRODUCT_MODEL := PKX110

PRODUCT_GMS_CLIENTID_BASE := android-oneplus

PRODUCT_BUILD_PROP_OVERRIDES += \
    BuildDesc="qssi-user 16 BP2A.250605.015 1785568253866 release-keys" \
    BuildFingerprint=OnePlus/PKX110/OP60F5L1:16/AP3A.240617.008/V.526b505-2d5a96d-2d6b5ad:user/release-keys \
    DeviceName=OP60F5L1 \
    DeviceProduct=PKX110 \
    SystemDevice=OP60F5L1 \
    SystemName=PKX110
