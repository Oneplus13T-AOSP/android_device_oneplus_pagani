/*
 * Copyright (C) 2024 The LineageOS Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <aidl/android/hardware/power/BnPower.h>
#include <aidl/vendor/oplus/hardware/touch/IOplusTouch.h>
#include <charconv>
#include <limits>
#include <android-base/strings.h>
#include <android-base/logging.h>
#include <linux/input.h>
#include <android/binder_manager.h>

namespace aidl {
namespace google {
namespace hardware {
namespace power {
namespace impl {
namespace pixel {

constexpr unsigned int kDoubleTapGesture = 1U << 1;

using ::aidl::android::hardware::power::Mode;

using ::aidl::vendor::oplus::hardware::touch::IOplusTouch;

bool isDeviceSpecificModeSupported(Mode type, bool* _aidl_return) {
    switch (type) {
        case Mode::DOUBLE_TAP_TO_WAKE:
            *_aidl_return = true;
            return true;
        default:
            return false;
    }
}

bool setDeviceSpecificMode(Mode type, bool enabled) {
    switch (type) {
        case Mode::DOUBLE_TAP_TO_WAKE: {
            const std::string instance = std::string() + IOplusTouch::descriptor + "/default";
            auto touchService = IOplusTouch::fromBinder(
                ndk::SpAIBinder(AServiceManager_waitForService(instance.c_str())));
            LOG(INFO) << "Power mode: " << toString(type) << " isDoubleTapEnabled: " << enabled;

            if (!touchService) {
                LOG(ERROR) << "Unable to obtain OplusTouch service";
                return true;
            }

            std::string contents;
            auto status = touchService->touchReadNodeFile(0, 21, &contents);
            if (!status.isOk()) {
                LOG(ERROR) << "Unable to read gesture mask: " << status.getDescription();
                return true;
            }
            contents = ::android::base::Trim(contents);
            unsigned int mask = 0;
            const auto parsed = std::from_chars(contents.data(),
                                               contents.data() + contents.size(), mask, 16);
            if (parsed.ec != std::errc{} || parsed.ptr != contents.data() + contents.size() ||
                mask > static_cast<unsigned int>(std::numeric_limits<int>::max())) {
                LOG(ERROR) << "Invalid gesture mask: " << contents;
                return true;
            }
            mask = enabled ? (mask | kDoubleTapGesture) : (mask & ~kDoubleTapGesture);

            // Keep the shared gesture gate enabled; change only the DT2W bit.
            int result = 0;
            status = touchService->touchWriteNodeFile(0, 1, "1", &result);
            if (!status.isOk() || result < 0) {
                LOG(ERROR) << "Unable to enable gesture gate: " << status.getDescription()
                           << ", result: " << result;
                return true;
            }
            status = touchService->touchWriteNodeFile(0, 21, std::to_string(mask), &result);
            if (!status.isOk() || result < 0) {
                LOG(ERROR) << "Unable to write gesture mask: " << status.getDescription()
                           << ", result: " << result;
            }
            return true;
        }
        default:
            return false;
    }
}

}  // namespace pixel 
}  // namespace impl
}  // namespace power
}  // namespace hardware
}  // namespace google
}  // namespace aidl
