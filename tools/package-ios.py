#!/usr/bin/env python3
"""Package the built ios-arm64-release target into an unsigned .ipa for LiveContainer / SideStore."""

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Package Pinyon Shift for iOS (unsigned .ipa)")
    parser.add_argument("--build-dir", default="out/build/ios-arm64-release", help="CMake iOS build directory")
    parser.add_argument("--output-dir", default="out/ios-package", help="Output directory for .app and .ipa")
    parser.add_argument("--bundle-id", default="://vrkutak.com.fh", help="CFBundleIdentifier")
    parser.add_argument("--icon", default="icon.png", help="Path to 1024x1024 PNG icon")
    parser.add_argument("--aot-shaders", default=".local/preview/cache/shaders/shareable",
                        help="Optional directory with shareable AOT shader files (.xpso/.xsh)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    build_dir = (repo_root / args.build_dir).resolve()
    out_dir = (repo_root / args.output_dir).resolve()
    app_src = build_dir / "pinyon_shift.app"
    pkg_dir = out_dir / "PinyonShift.app"
    fw_dir = pkg_dir / "Frameworks"

    if not (app_src / "pinyon_shift").is_file():
        raise FileNotFoundError(f"iOS binary not found at {app_src / 'pinyon_shift'}. Build ios-arm64-release first.")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    fw_dir.mkdir(parents=True)

    exe_dst = pkg_dir / "pinyon_shift"
    shutil.copy2(app_src / "pinyon_shift", exe_dst)
    if (app_src / "gamecontrollerdb.txt").is_file():
        shutil.copy2(app_src / "gamecontrollerdb.txt", pkg_dir / "gamecontrollerdb.txt")

    dylib_paths = [
        build_dir / "rexglue-artifacts" / "libMoltenVK.1.dylib",
        app_src / "librexgpu-fh1.dylib",
        app_src / "librexruntime.dylib",
        app_src / "libpinyon_shift_SpeechFacade_default.dylib",
        app_src / "libpinyon_shift_XMediaFacade_default.dylib",
    ]
    for src_lib in dylib_paths:
        if not src_lib.is_file():
            raise FileNotFoundError(f"Required iOS dylib missing: {src_lib}")
        for dst_folder in (pkg_dir, fw_dir):
            dst_lib = dst_folder / src_lib.name
            shutil.copy2(src_lib, dst_lib)
            subprocess.run(["install_name_tool", "-id", f"@rpath/{src_lib.name}", str(dst_lib)], check=True)

    subprocess.run(["install_name_tool", "-add_rpath", "@executable_path/Frameworks", str(exe_dst)], check=False)

    aot_dir = (repo_root / args.aot_shaders).resolve()
    if aot_dir.is_dir():
        dst_shaders = pkg_dir / "shaders" / "shareable"
        dst_shaders.mkdir(parents=True, exist_ok=True)
        for item in aot_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, dst_shaders / item.name)

    icon_src = (repo_root / args.icon).resolve()
    if not icon_src.is_file():
        icon_src = repo_root / "config" / "steam" / "icon.png"
    if icon_src.is_file():
        for filename, size in [
            ("AppIcon60x60@2x.png", 120),
            ("AppIcon60x60@3x.png", 180),
            ("Icon.png", 180),
            ("AppIcon76x76@2x~ipad.png", 152),
            ("AppIcon83.5x83.5@2x~ipad.png", 167),
        ]:
            subprocess.run(
                ["sips", "-z", str(size), str(size), str(icon_src), "--out", str(pkg_dir / filename)],
                stdout=subprocess.DEVNULL,
                check=True,
            )

    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com">
<plist version="1.0">
<dict>
	<key>CFBundleDevelopmentRegion</key>
	<string>en</string>
	<key>CFBundleDisplayName</key>
	<string>Forza Horizon</string>
	<key>CFBundleExecutable</key>
	<string>pinyon_shift</string>
	<key>CFBundleIconFile</key>
	<string>Icon.png</string>
	<key>CFBundleIconFiles</key>
	<array>
		<string>Icon.png</string>
		<string>AppIcon60x60@2x.png</string>
		<string>AppIcon60x60@3x.png</string>
	</array>
	<key>CFBundleIdentifier</key>
	<string>{args.bundle_id}</string>
	<key>CFBundleInfoDictionaryVersion</key>
	<string>6.0</string>
	<key>CFBundleName</key>
	<string>PinyonShift</string>
	<key>CFBundlePackageType</key>
	<string>APPL</string>
	<key>CFBundleShortVersionString</key>
	<string>0.9.5</string>
	<key>CFBundleVersion</key>
	<string>1</string>
	<key>LSApplicationCategoryType</key>
	<string>public.app-category.racing-games</string>
	<key>LSRequiresIPhoneOS</key>
	<true/>
	<key>MinimumOSVersion</key>
	<string>16.0</string>
	<key>UIDeviceFamily</key>
	<array>
		<integer>1</integer>
		<integer>2</integer>
	</array>
	<key>UIFileSharingEnabled</key>
	<true/>
	<key>LSSupportsOpeningDocumentsInPlace</key>
	<true/>
	<key>UIRequiresFullScreen</key>
	<true/>
	<key>UIStatusBarHidden</key>
	<true/>
	<key>UISupportedInterfaceOrientations</key>
	<array>
		<string>UIInterfaceOrientationLandscapeLeft</string>
		<string>UIInterfaceOrientationLandscapeRight</string>
	</array>
	<key>UISupportedInterfaceOrientations~ipad</key>
	<array>
		<string>UIInterfaceOrientationLandscapeLeft</string>
		<string>UIInterfaceOrientationLandscapeRight</string>
	</array>
</dict>
</plist>
"""
    (pkg_dir / "Info.plist").write_text(info_plist, encoding="utf-8")

    payload_dir = out_dir / "Payload"
    payload_dir.mkdir()
    shutil.copytree(pkg_dir, payload_dir / "PinyonShift.app")
    ipa_path = out_dir / "PinyonShift-ios-unsigned.ipa"
    subprocess.run(["zip", "-qry", str(ipa_path), "Payload"], cwd=str(out_dir), check=True)
    shutil.rmtree(payload_dir)
    print(f"Packaged unsigned iOS IPA: {ipa_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
