"""Builds the release files into ../dist (outside the repository).

python tools/build_release.py --owner <github-user> [--host-exe path/to/quick-profile-switch-host.exe]

- replaces the OWNER placeholder in the repository links (manifest, setup page, README)
- packs extension/ as quick-profile-switch-<version>.zip for addons.mozilla.org
- copies the helper .exe and writes SHA256SUMS.txt
- runs the private-data scan if ../../private_terms.txt exists
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(os.path.dirname(ROOT), "dist")
PLACEHOLDER_FILES = ["extension/manifest.json", "extension/setup.js", "README.md"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True, help="GitHub user or organisation that hosts the repository")
    ap.add_argument("--host-exe", help="built quick-profile-switch-host.exe")
    args = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", args.owner):
        sys.exit("Invalid GitHub name")

    for rel in PLACEHOLDER_FILES:
        path = os.path.join(ROOT, rel)
        text = open(path, encoding="utf-8").read()
        new = text.replace("github.com/OWNER/", f"github.com/{args.owner}/")
        if new != text:
            open(path, "w", encoding="utf-8", newline="").write(new)
            print("links updated:", rel)

    ext = os.path.join(ROOT, "extension")
    for rel in ("manifest.json", "setup.js"):
        if "github.com/OWNER/" in open(os.path.join(ext, rel), encoding="utf-8").read():
            sys.exit(f"Placeholder left in {rel}")
    version = json.load(open(os.path.join(ext, "manifest.json"), encoding="utf-8"))["version"]

    os.makedirs(DIST, exist_ok=True)
    zip_path = os.path.join(DIST, f"quick-profile-switch-{version}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, _, files in os.walk(ext):
            for f in sorted(files):
                full = os.path.join(folder, f)
                z.write(full, os.path.relpath(full, ext).replace(os.sep, "/"))
    outputs = [zip_path]
    print("add-on package:", zip_path)

    if args.host_exe:
        exe = os.path.join(DIST, "quick-profile-switch-host.exe")
        shutil.copy2(args.host_exe, exe)
        digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
        with open(os.path.join(DIST, "SHA256SUMS.txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write(f"{digest}  quick-profile-switch-host.exe\n")
        outputs.append(exe)
        print("helper:", exe, digest)

    terms = os.path.join(os.path.dirname(ROOT), "private_terms.txt")
    if not os.path.exists(terms):
        print("WARNING: no private_terms.txt next to the repository folder, private-data scan skipped")
    else:
        env = dict(os.environ, QPS_PRIVATE_TERMS=terms)
        subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "scan_private.py"), ROOT, *outputs], env=env, check=False)


if __name__ == "__main__":
    main()
