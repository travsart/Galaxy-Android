#!/usr/bin/env python3
"""Build all native and packaging inputs, then produce a signed Android APK."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--build-type",
        "--type",
        choices=("debug", "release"),
        default="debug",
        help="native build configuration and APK signing mode (default: debug)",
    )
    parser.add_argument(
        "--keystore",
        type=Path,
        help="release keystore (or set ANDROID_KEYSTORE)",
    )
    parser.add_argument(
        "--key-alias",
        help="release key alias (or set ANDROID_KEY_ALIAS)",
    )
    args = parser.parse_args()

    build_dir = ROOT / f"build-mobile-{args.build_type}"
    output_apk = ROOT / "out-mobile" / f"GalaxyAndroid-{args.build_type}.apk"
    environment = os.environ.copy()
    environment["BUILD"] = str(build_dir)
    environment["CONFIG"] = "Debug" if args.build_type == "debug" else "Release"
    environment["GALAXY_BUILD_DIR"] = str(build_dir)

    package_command = [
        sys.executable,
        str(ROOT / "package_mobile_apk.py"),
        "--build-type",
        args.build_type,
        "--output",
        str(output_apk),
    ]

    if args.build_type == "release":
        keystore = args.keystore or (Path(environment["ANDROID_KEYSTORE"]) if environment.get("ANDROID_KEYSTORE") else None)
        key_alias = args.key_alias or environment.get("ANDROID_KEY_ALIAS")
        required = {
            "release keystore": keystore,
            "release key alias": key_alias,
            "ANDROID_KEYSTORE_PASSWORD": environment.get("ANDROID_KEYSTORE_PASSWORD"),
            "ANDROID_KEY_PASSWORD": environment.get("ANDROID_KEY_PASSWORD"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            parser.error(
                "release signing requires " + ", ".join(missing)
                + "; provide credentials through environment variables"
            )
        package_command.extend(("--keystore", str(keystore.resolve()), "--key-alias", key_alias))

    subprocess.run(["bash", str(ROOT / "build_mobile.sh")], cwd=ROOT, env=environment, check=True)
    subprocess.run(package_command, cwd=ROOT, env=environment, check=True)
    print(f"APK: {output_apk}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())