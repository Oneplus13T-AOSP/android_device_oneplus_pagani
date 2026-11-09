#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils:../../../hardware/oplus/extract-utils-ext python3
#
# SPDX-FileCopyrightText: The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils_oplus import (
    add_generated_thermal_engine_config,
)

namespace_imports = [
    'hardware/oplus',
    'hardware/qcom-caf/sm8750',
    'vendor/oneplus/sm8750-common',
    'vendor/qcom/opensource/commonsys-intf/display',
]

def fixup_eis_snap_handle_format(ctx, file, file_path, *args, **kwargs):
    """Adapt COS17 EIS's five legacy handle-format reads to pagani's SnapHandle."""
    # Stock snapalloc format(): properties at 0x18 + format at 0x14 = 0x2c.
    # Our snapalloc (also checked in the running phone): 0x18 + 0x1c = 0x34.
    # 0x2c now contains unaligned_width, hence portrait preview's fmt:1280,
    # EGL_BAD_PARAMETER and repeated framebuffer/render failures.
    # Only these five loads feed ShareBuffer_CreateFromNativeHandle. Do not
    # replace other 0x2c loads, which access unrelated EIS state structures.
    # Anchors include the argument setup and the call in PKX110_17.0.0.104.
    patterns = (
        '042c40b9052080524500a072e303012a3ffcff97',
        '842e40b9e18b4429e32f40b905408052e00314aa24c4ff97',
        '042f40b9052080524500a072e00318aaeb1700b9b9c3ff97',
        '042c40b90189402986c2ff97',
        '042c40b90189402939c2ff97',
    )
    path = Path(file_path)
    data = path.read_bytes()
    replacements = []
    for pattern in patterns:
        old = bytes.fromhex(pattern)
        instruction = int.from_bytes(old[:4], 'little')
        new = (instruction + (2 << 10)).to_bytes(4, 'little') + old[4:]
        old_count, new_count = data.count(old), data.count(new)
        if (old_count, new_count) == (0, 1):
            continue
        if (old_count, new_count) != (1, 0):
            raise ValueError('Unexpected libEIS handle-format code; re-audit SnapHandle ABI')
        replacements.append((old, new))
    # Validate every anchor before writing, including on partially patched input.
    for old, new in replacements:
        data = data.replace(old, new, 1)
    if replacements:
        path.write_bytes(data)


blob_fixups: blob_fixups_user_type = {
    'odm/lib64/libEIS.so': blob_fixup()
        .call(fixup_eis_snap_handle_format, need_tmp_dir=False),
    (
        'odm/bin/hw/vendor-oplus-hardware-touch-V2-service',
        'vendor/lib64/libcamxcoreutils.so',
        'vendor/lib64/libcamxods.so',
    ): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so'),
    'odm/etc/init/init.camera_process.rc': blob_fixup()
        .regex_replace('    delete_recursion', '    #delete_recursion'),
    'odm/lib64/soundfx/libOplusSpatializerAidl.so': blob_fixup()
        .add_needed('libbase.so'),
    'odm/etc/init/occe_create.rc': blob_fixup()
        .regex_replace(r'(?m)^(?=/\*|\*)', '# '),
    'odm/lib64/libAlgoProcess.so': blob_fixup()
        .replace_needed('android.hardware.graphics.common-V5-ndk.so', 'android.hardware.graphics.common-V7-ndk.so'),
    (
        'odm/lib64/libAncHumanSegFigureFusion.so',
        'odm/lib64/libEIS.so',
        'odm/lib64/libEISLive.so',
        'odm/lib64/libHIS.so',
        'odm/lib64/libOPAlgoCamAiBeautyFaceRetouchCn.so',
        'odm/lib64/libOPAlgoCamAiUnifySkin.so',
        'odm/lib64/libOPAlgoCamFaceBeautyCap.so',
    ): blob_fixup()
        .clear_symbol_version('AHardwareBuffer_acquire')
        .clear_symbol_version('AHardwareBuffer_allocate')
        .clear_symbol_version('AHardwareBuffer_describe')
        .clear_symbol_version('AHardwareBuffer_lock')
        .clear_symbol_version('AHardwareBuffer_lockPlanes')
        .clear_symbol_version('AHardwareBuffer_release')
        .clear_symbol_version('AHardwareBuffer_unlock'),
    'odm/lib64/liboprec_audrec.so': blob_fixup()
        .replace_needed('libstdc++.so', 'libstdc++_vendor.so'),
    # Master/Pro-mode photos come out with RED/BLUE swapped. Pro mode captures RAW10 and the
    # OnePlus OCCE tone-mapper (libBasicTonePhoto.so) runs an OpenGL shader whose body contains a
    # U/V (Cb/Cr) reorder `dstYuv = vec4(dstYuv.r, dstYuv.b, dstYuv.g, 1.0)`. On this port the net
    # result is a single uncompensated chroma swap -> R/B swapped JPEG. Undo the swap in the
    # embedded GLSL (length-preserving). Normal/Photo mode does NOT use BasicTone, so this only
    # affects the (otherwise crisp) Master/Pro path..
    'odm/lib64/libBasicTonePhoto.so': blob_fixup()
        .binary_regex_replace(
            b'vec4\\(dstYuv\\.r, dstYuv\\.b, dstYuv\\.g, 1\\.0\\)',
            b'vec4(dstYuv.r, dstYuv.g, dstYuv.b, 1.0)',
        ),
    'odm/lib64/libsensorbridge.so': blob_fixup()
        .replace_needed('android.hardware.sensors-V2-ndk.so', 'android.hardware.sensors-V3-ndk.so'),
    (
        'vendor/lib64/camera/components/com.qti.node.dewarp.so',
        'vendor/lib64/hw/com.qti.chi.override.so',
        'vendor/lib64/libcamximageformatutils.so',
        'vendor/lib64/libchifeature2.so',
    ): blob_fixup()
        .replace_needed('android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.allocator-V2-ndk.so'),
    'vendor/lib64/vendor.qti.hardware.camera.offlinecamera-service-impl.so': blob_fixup()
        .replace_needed('android.hardware.graphics.allocator-V1-ndk.so', 'android.hardware.graphics.allocator-V2-ndk.so')
        # convertAndImportBuffer reads the offline-metadata buffer size from the SnapHandle's
        # aligned_width_in_bytes field (handle+0x1c), but on this build that field holds a bogus
        # stride (e.g. 512) for the metadata BLOB while the real byte size is in the next field
        # (aligned_width_in_pixels, handle+0x20). That truncates the metadata copy to 512 bytes
        # and crashes CamX (MetaBuffer::AllocateBuffer). Patch the load to read +0x20 instead of
        # +0x1c:  ldr w27,[x21,#0x1c] (bb1e40b9) -> ldr w27,[x21,#0x20] (bb2240b9).
        # 12-byte anchor = ldr x21,[x12,#0x30]; ldr w27,[x21,#0x1c]; ldr w0,[x21,#0xc].
        .binary_regex_replace(
            b'\x95\x19\x40\xf9\xbb\x1e\x40\xb9\xa0\x0e\x40\xb9',
            b'\x95\x19\x40\xf9\xbb\x22\x40\xb9\xa0\x0e\x40\xb9',
        ),
    'odm/lib64/libsharebuffer_impl.so': blob_fixup()
        .replace_needed('libutils.so', 'libutils-stock.so')
        .replace_needed('libui.so', 'libui-stock.so'),
    'odm/lib64/libHIS.so':blob_fixup()
        .replace_needed('libui.so', 'libui-stock.so'),
    'vendor/lib64/libui-stock.so': blob_fixup()
        .replace_needed('android.hardware.graphics.common-V5-ndk.so', 'android.hardware.graphics.common-V7-ndk.so'),
}  # fmt: skip

module = ExtractUtilsModule(
    'pagani',
    'oneplus',
    namespace_imports=namespace_imports,
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    add_firmware_proprietary_file=True,
)

add_generated_thermal_engine_config(module)

if __name__ == '__main__':
    utils = ExtractUtils.device_with_common(
        module, 'sm8750-common', module.vendor
    )
    utils.run()
