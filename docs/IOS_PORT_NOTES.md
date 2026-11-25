# iOS / iPadOS Porting Notes & Solved Issues

This document records every platform-specific obstacle encountered while porting
[arcanite24/pinyon-shift](https://github.com) and
[ShiftGlue](https://github.com) to `arm64-apple-ios`,
along with the exact technical solution applied in this fork.

---

## 1. CMake Cross-Compilation & iPhoneOS SDK Detection
- **Problem:** CMake presets only targeted `mac-arm64` (`macosx` SDK) and `android-arm64`. Host-only desktop components such as `dxilconv`, `shader-playground`, and AMD FidelityFX (`rexglue_fidelityfx_runtime`) attempted to link against macOS Homebrew dylibs (`/opt/homebrew/lib/libvulkan.dylib`), failing with `ld: building for 'iOS', but linking in dylib built for 'macOS'`.
- **Solution:**
  - Added `ios-base` and `ios-arm64-release` presets in `CMakePresets.json` (`CMAKE_SYSTEM_NAME=iOS`, `CMAKE_OSX_ARCHITECTURES=arm64`, `CMAKE_OSX_DEPLOYMENT_TARGET=16.0`, `PINYON_SHIFT_CPU_BASELINE=armv8-a`).
  - Defined `REX_PLATFORM_IOS=1` globally under `if(IOS)` in `CMakeLists.txt`.
  - Disabled desktop-only targets (`dxilconv`, `rexglue_fidelityfx_runtime`, and `_rexglue_stage_fidelityfx_runtime`) when `IOS` is set.
  - Enabled static/embedded MoltenVK (`REX_BUILD_MOLTENVK=ON`) and built SDL3 for iOS `UIKit`.

## 2. Virtual Memory Inspection (`<mach/mach_vm.h>` vs `<mach/vm_map.h>`)
- **Problem:** `thirdparty/shiftglue-sdk/src/core/memory_posix.cpp` included `<mach/mach_vm.h>` and called `mach_vm_region()`, which Apple's iPhoneOS SDK explicitly forbids (`error: mach_vm.h unsupported`).
- **Solution:** Under `#if REX_PLATFORM_IOS`, replaced `<mach/mach_vm.h>` with `<mach/vm_map.h>` and mapped `vm_address_t`, `vm_size_t`, and `vm_region_64()` to `QueryProtect()`.

## 3. Android-Only UI Code in Settings Menu
- **Problem:** `src/ui/settings_menu.cpp` unconditionally compiled `rex::ui::vulkan::CallAndroidActivityMethod("importGpuDriver")` for mobile targets, causing a linker/compiler error on iOS.
- **Solution:** Guarded the Adreno/Turnip external driver picker with `#if defined(__ANDROID__)`, leaving the mobile **SMOOTH 60** and **QUALITY 30** presets intact on iOS.

## 4. iOS Entry Point (`UIApplicationMain` via `SDL_main`)
- **Problem:** Without `<SDL3/SDL_main.h>`, iOS launched standard C `int main()` without initializing `UIApplicationMain` or the `UIKit` run loop, immediately exiting with `App returned from its main function with code 1`.
- **Solution:** Included `<SDL3/SDL_main.h>` in `thirdparty/shiftglue-sdk/src/ui/windowed_app_main_sdl.cpp` for `REX_PLATFORM_IOS` and set `SDL_HINT_ORIENTATIONS` to `"LandscapeLeft LandscapeRight"`.

## 5. SDL3 Video Driver Selection (`"uikit"` instead of `"cocoa"`)
- **Problem:** Because Darwin sets `REX_PLATFORM_MAC=1` alongside `REX_PLATFORM_IOS=1`, `SDLWindowedAppContext::Initialize()` requested the macOS `"cocoa"` video driver on iOS, failing `SDL_InitSubSystem(SDL_INIT_VIDEO)`.
- **Solution:** Added `#if REX_PLATFORM_IOS` ahead of `#elif REX_PLATFORM_MAC` in `windowed_app_context_sdl.cpp` to select `"uikit"`.

## 6. Dynamic Library Staging for `dlopen` and `@rpath`
- **Problem:** `librexgpu-fh1.dylib` is loaded dynamically via `dlopen` next to the executable, while `libMoltenVK.1.dylib` and `librexruntime.dylib` are resolved via `@rpath`. Placing dylibs only in `Frameworks/` caused `GPU plugin 'fh1' not found`.
- **Solution:** `tools/package-ios.py` stages all required `.dylib` binaries in **both** the `.app` root (beside `pinyon_shift`) and `Frameworks/`, sets their install names to `@rpath/<name>`, and adds `@executable_path/Frameworks` to the executable's rpath.

## 7. Reserving 4.5 GB Guest Address Space (`shm_open` Limit on iOS)
- **Problem:** `Memory::Initialize()` reserves `0x120000000` bytes (~4.5 GB) of virtual address space via `CreateFileMappingHandle()`. On iOS, `shm_open()` enforces a strict kernel limit (~32 MB), causing `Unable to reserve the 4gb guest address space`.
- **Solution:** Added an `#elif REX_PLATFORM_IOS` path in `CreateFileMappingHandle()` (`memory_posix.cpp`) that creates an unlinked sparse temporary file in `$TMPDIR` (`mkstemp` + immediate `unlink` + `ftruncate64`). APFS sparse files consume zero physical disk space while allowing `mmap` to map the full 32-bit Xbox 360 virtual and physical views.

## 8. iOS App Sandbox & `Documents/` Paths
- **Problem:** The `.app` bundle directory is strictly read-only on iOS; attempting to create `pinyon_shift_state/` next to the executable fails, and users need an accessible location to transfer game data (`game/base/default.xex`).
- **Solution:**
  - Redirected default `g_state_root` on iOS to `$HOME/Documents/pinyon_shift_state` in `src/pinyon_shift_diagnostics.cpp`.
  - Configured `paths.game_data_root` in `src/pinyon_shift_app.cpp` to look in `$HOME/Documents/game/base` (or `$HOME/Documents/game`) with `UIFileSharingEnabled=true` in `Info.plist`.

## 9. Cooperative Fibers on Apple ARM64 (`ucontext` Removal)
- **Problem:** Pressing **Start** in the title menu triggered `SwitchToFiber: no valid fiber` and crashed because `getcontext()` / `makecontext()` / `swapcontext()` return `ENOSYS` on iOS.
- **Solution:** Enabled `REX_FIBER_STACK_SWITCH=1` for `REX_PLATFORM_IOS` in `include/rex/thread/fiber.h` and implemented Darwin Mach-O ARM64 assembly routines (`_rex_fiber_switch` and `_rex_fiber_start` using `.private_extern` and Apple symbol prefixes) in `src/core/fiber_posix.cpp`.

## 10. Black Screen & Freeze When Pulling Down Notification Center / Control Center
- **Problem:** Pulling down iOS Control Center (e.g. to start screen recording) fired `SDL_EVENT_WILL_ENTER_BACKGROUND`, causing `WindowSDL::HandleAppBackground` to retire the Vulkan swapchain (black screen) and `rex_app.cpp` to pause GPU/audio/guest clocks (freeze).
- **Solution:** Kept the `CAMetalLayer` swapchain and runtime active during iOS `kWillEnterBackground` transitions so system overlays and screen recording work without interrupting rendering.

## 11. Shader Compilation Stutter Mitigation (AOT Pipeline Prewarming)
- **Problem:** First-time gameplay compiles Xbox 360 shaders into Metal pipelines on the fly via MoltenVK, causing frame hitches.
- **Solution:** Bundled the shareable ahead-of-time pipeline list (`4D5309C9.fbo.aot.xpso`) inside `PinyonShift.app/shaders/shareable/` and automatically seeded it into `Documents/pinyon_shift_state/cache/shaders/shareable/` at startup so the 4-thread background pipeline compiler prewarms Metal shaders before racing begins.

## 12. Game Mode & Controller Entitlements
- **Solution:** Added `LSApplicationCategoryType = public.app-category.racing-games` and `GCSupportedGameControllers` in `Info.plist` so iOS/iPadOS automatically enables **Game Mode** (prioritized GPU scheduling and low-latency Bluetooth polling for DualShock 4, DualSense, and Xbox controllers).
