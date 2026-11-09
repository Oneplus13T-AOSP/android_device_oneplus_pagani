# COS17 camera compatibility review (2026-11-09)

Portrait preview on the connected PKX110 reported `LibEIS` EGL error 12300
(EGL_BAD_PARAMETER), `fmt:1280`, incomplete framebuffers and repeated render
failures. The camera app, camera provider and cameraserver remained alive in
that trace; it did not show an app/HAL crash.

The COS17 `libEIS.so` reads pixel format directly at native_handle + 0x2c
before calling ShareBuffer_CreateFromNativeHandle. This matches stock
snapalloc's format accessor: properties start at 0x18, format at +0x14.
PixelOS's current snapalloc uses properties +0x1c, so the format is at 0x34.
The old 0x2c location contains unaligned_width, explaining `fmt:1280`.
Both accessors were disassembled from the stock dump and running device:
`vendor/lib64/vendor.qti.hardware.display.snapalloc-impl.so`.
The source agrees: hardware/qcom-caf/sm8750/display/core/snapalloc/
SnapHandleInternal.cpp, SnapHandleProperties and SnapHandleData<1>.

The extraction fixup changes only five audited LDR w4 instructions immediately
feeding handle imports at virtual addresses 0x13524, 0x2158c, 0x21738,
0x21c10 and 0x21d44. It changes +0x2c to +0x34, preserves the other fields
and does not replace unrelated 0x2c state accesses. Full instruction/call anchors
are checked before writing; unknown or duplicate anchors fail extraction.
Existing AHardwareBuffer symbol-version fixups still apply via extract-utils'
merged fixup list. vendor/oneplus/pagani's cached libEIS must be updated together.

This is specific to this COS17 blob and the current single-view SnapHandle
layout. It must be re-audited if snapalloc/the blob changes; it must not be used
with the stock allocator layout or treated as generic multiview support.

Validation:

```
python3 device/oneplus/pagani/tests/test_eis_fixup.py /path/to/cos/odm/lib64/libEIS.so
```

The real stock blob passes four tests: exactly five LDR immediate changes,
idempotence, rejection of a changed final anchor without writes, and duplicate
anchor rejection. The cached blob was checked separately to retain its existing
AHardwareBuffer version fixes. This establishes the incorrect-format fix, not
successful portrait capture: the patched library has not been installed and
portrait preview/capture still requires an on-device retest. No kernel change
is indicated by the observed failure.
