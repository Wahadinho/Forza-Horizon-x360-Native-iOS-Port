# Pinyon Shift on iOS / iPadOS

> **Fork notice:** This repository is an unofficial iOS / iPadOS fork of
> **[Pinyon Shift](https://github.com)** by
> [arcanite24](https://github.com), powered by
> [ShiftGlue](https://github.com/shiftglue-sdk). It contains **no**
> copyrighted game files, assets, or disc images. You must provide your own
> legally owned USA retail disc of *Forza Horizon* (`MS-2505`, title ID
> `4D5309C9`).

**Status: playable developer port.** The game compiles natively for `arm64-apple-ios`
and renders via Vulkan on top of Apple Metal using an embedded build of **MoltenVK 1.4.1**.
Because the PowerPC game code is statically recompiled to native ARM64 C++ ahead of time,
**JIT is not required** on iOS.

## Supported Devices

- **OS:** iOS 16.0 or iPadOS 16.0 and newer.
- **SoC baseline:** Apple A12 Bionic or newer (`armv8-a`, 64-bit).
- **Recommended hardware:**
  - **iPhone 15 Pro / 16 Pro / 17 Pro Max** (A17 Pro – A19 Pro, 8+ GB RAM) — runs at 60 fps on the *SMOOTH 60* preset.
  - **iPad (A16) / iPad Air / iPad Pro (M1–M4)** (6+ GB RAM) — playable on *SMOOTH 60* or *QUALITY 30*.

## How to Install (Sideloading)

Because the `.ipa` release is unsigned and contains no game data (~45 MB), install it
using **LiveContainer**, **SideStore**, or **AltStore**, and then copy your extracted
game files into the app's `Documents` folder.

### Step 1: Install the `.ipa`

1. Download `PinyonShift-ios-unsigned.ipa` from the **Releases** page.
2. Transfer it to your iPhone or iPad (via AirDrop or the Files app).
3. Open and install it in **LiveContainer** (recommended, no 3-app limit) or **SideStore / AltStore**.

### Step 2: Prepare Your Game Files on a Computer

On Windows, Linux, or macOS, extract your own USA *Forza Horizon* disc image using the
standard Pinyon Shift setup tool:

```bash
python3 tools/pinyon.py setup --iso /path/to/ForzaHorizon.iso
```

This creates the `.local/game` folder containing `base/default.xex` and `base/media/...`.

### Step 3: Copy `game/` to Your iPhone or iPad

The iOS build looks for your game data at `Documents/game/base/default.xex` inside the
app's container (`UIFileSharingEnabled` is enabled):

- **Via Finder (macOS) or Apple Devices / iTunes (Windows):**
  1. Connect your iPhone or iPad via USB.
  2. Open **Finder** -> select your device -> **Files** tab.
  3. Expand **Forza Horizon** (or **LiveContainer** -> `Data/Application/<UUID>/Documents/`) and drag the entire `game` folder into `Documents` so the path is `Documents/game/base/default.xex`.
- **Via the iOS Files app:**
  1. Copy the `game` folder to iCloud Drive or an external USB-C drive.
  2. Move `game` into **On My iPhone / iPad -> Forza Horizon** (or inside LiveContainer's `Documents` folder for the app).

## Controls and Graphics Settings

- **Controllers:** PlayStation (DualShock 4, DualSense), Xbox Wireless, and MFi Bluetooth controllers work out of the box via SDL3.
- **Touch Controls:** On-screen touch controls are built in and automatically adapt to the device's safe-area insets.
- **Graphics Presets:** Open the in-game **SETTINGS > GRAPHICS** menu (press **Back + Start** on a controller) to switch between:
  - **SMOOTH 60** (recommended): 1x resolution, MSAA off, shadows off, single-pass rendering, 60 fps target.
  - **QUALITY 30**: 1x resolution, 4x MSAA, shadows enabled, 30 fps cap.
- **Shader Cache:** On first launch, bundled ahead-of-time pipeline descriptions (`shaders/shareable/`) are copied to `Documents/pinyon_shift_state/cache/shaders/shareable/` and compiled in the background across 4 CPU threads.

## Building from Source (macOS)

1. Complete a host setup first so the PowerPC-to-C++ codegen output (`.local/generated/default`) is generated:
   ```bash
   python3 tools/pinyon.py setup --iso /path/to/ForzaHorizon.iso
   ```
2. Configure and build the iOS ARM64 release target:
   ```bash
   cmake --preset ios-arm64-release
   cmake --build --preset ios-arm64-release
   ```
3. Package the unsigned `.ipa`:
   ```bash
   python3 tools/package-ios.py
   ```
   The finished archive is written to `out/ios-package/PinyonShift-ios-unsigned.ipa`.

## Legal & Credits

- Original project & ShiftGlue SDK: **[arcanite24/pinyon-shift](https://github.com)** & **[arcanite24/shiftglue-sdk](https://github.com/shiftglue-sdk)**.
- Not affiliated with or endorsed by Microsoft, Xbox, Turn 10 Studios, or Playground Games.
