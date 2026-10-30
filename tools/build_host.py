"""Builds host/quick_profile_switch_host.py into a single quick-profile-switch-host.exe (needs: pip install pyinstaller).

python tools/build_host.py   ->   ../dist-build/dist/quick-profile-switch-host.exe

Modules the helper does not need (network, crypto, compression, decimal) are left out: smaller file and fewer
bundled third-party components (see THIRD-PARTY-NOTICES.md).
"""
import os
import PyInstaller.__main__

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = os.path.join(ROOT, "host")
OUT = os.path.join(os.path.dirname(ROOT), "dist-build")
EXCLUDE = ["_hashlib", "_ssl", "ssl", "_socket", "socket", "select", "selectors", "_decimal", "decimal",
           "_pydecimal", "_lzma", "lzma", "_bz2", "bz2", "unicodedata"]

args = ["--noconfirm", "--clean", "--onefile", "--noconsole", "--name", "quick-profile-switch-host",
        "--icon", os.path.join(HOST, "icon.ico"), "--version-file", os.path.join(HOST, "version_info.txt"),
        "--distpath", os.path.join(OUT, "dist"), "--workpath", os.path.join(OUT, "work"), "--specpath", os.path.join(OUT, "work")]
for module in EXCLUDE:
    args += ["--exclude-module", module]
PyInstaller.__main__.run(args + [os.path.join(HOST, "quick_profile_switch_host.py")])
