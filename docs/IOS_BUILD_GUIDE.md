# Complete iOS / iPadOS Build Guide (from Source)

This guide covers every step required to compile **Pinyon Shift (iOS Fork)** from
source on an Apple Silicon Mac and package an unsigned `.ipa` for **LiveContainer**,
**SideStore**, or **AltStore**.

---

## 1. Prerequisites

- **Mac:** Apple Silicon (M1 / M2 / M3 / M4) running macOS 14.0 or newer.
- **Xcode:** Installed from the Mac App Store with the **iOS (iPhoneOS) SDK** installed.
  Verify that the iPhoneOS SDK is active:
  ```bash
  xcode-select -p
  xcrun --sdk iphoneos --show-sdk-path
  ```
- **Homebrew build tools:**
  ```bash
  brew install cmake ninja python@3.12
  ```
- **Legal Game Disc:** Your own USA retail disc image of *Forza Horizon* (`MS-2505`, title ID `4D5309C9`) as an `.iso` file.

---

## 2. Clone the Repository (with Submodules)

```bash
git clone --recursive https://github.com<your-username>/pinyon-shift-ios.git
cd pinyon-shift-ios
```

*(If you already cloned without `--recursive`, initialize `shiftglue-sdk` with `git submodule update --init --recursive`.)*

---

## 3. Generate Recompiled C++ Code & Extract Game Assets

Before cross-compiling for iOS, run the standard host setup once on your Mac. This
verifies your disc image, generates the ahead-of-time PowerPC-to-C++ translation in
`.local/generated/default/`, and extracts the game files into `.local/game/base/`:

```bash
python3 tools/pinyon.py setup --iso /path/to/ForzaHorizon.iso
```

*(Optional)* Generate the shareable AOT shader pipeline list so it gets bundled into the `.ipa`:

```bash
python3 tools/pinyon.py prepare-shaders
```

---

## 4. Configure and Compile for iOS (`arm64-apple-ios`)

Configure the CMake iOS preset and build the native ARM64 binaries and MoltenVK runtime:

```bash
cmake --preset ios-arm64-release
cmake --build --preset ios-arm64-release
```

When compilation finishes, the staged binaries are located in `out/build/ios-arm64-release/pinyon_shift.app/` and `out/build/ios-arm64-release/rexglue-artifacts/libMoltenVK.1.dylib`.

---

## 5. Package the Unsigned `.ipa`

Run the iOS packaging script to assemble `PinyonShift.app`, embed all `.dylib` frameworks, generate app icons from `icon.png`, bundle AOT shader lists, and produce `PinyonShift-ios-unsigned.ipa`:

```bash
python3 tools/package-ios.py
```

Optional flags:
- `--bundle-id <id>` — Override `CFBundleIdentifier` (default: `://vrkutak.com.fh`).
- `--icon <path>` — Use a custom 1024x1024 PNG icon (default: `icon.png`).

The final archive is created at:
```text
out/ios-package/PinyonShift-ios-unsigned.ipa
```

---

## 6. Install and Transfer Game Data to iPhone / iPad

1. **Install `.ipa`:** AirDrop `out/ios-package/PinyonShift-ios-unsigned.ipa` to your iPhone or iPad and import it into **LiveContainer** or **SideStore**.
2. **Copy `game/` folder:** Connect your iPhone/iPad to your Mac via USB, open **Finder -> [Your Device] -> Files**, and drag `.local/game` into the app's `Documents` folder so the resulting structure on the device is:
   ```text
   Documents/game/base/default.xex
   Documents/game/base/media/...
   ```
3. **Launch & Configure:** Open **Forza Horizon**, connect a controller (or use on-screen touch controls), and select **SMOOTH 60** in **SETTINGS > GRAPHICS** for optimal performance.
