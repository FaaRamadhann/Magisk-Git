#!/usr/bin/env python3
"""
Faa Magisk Git - Build Script
Membuat module Magisk Git menjadi file .zip siap install.
"""

import os
import sys
import zipfile
from datetime import datetime

# Konfigurasi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = BASE_DIR
TEMP_DIR = os.path.join(os.path.dirname(BASE_DIR), "temp")
OUTPUT_NAME = "Faa-Magisk-Git.zip"
OUTPUT_FILE = os.path.join(BASE_DIR, OUTPUT_NAME)

GIT_VERSION = "2.55.0"

# File/folder yang TIDAK ikut dikemas ke dalam .zip
EXCLUDE = [
    "build.py",
    "fetch_git.py",
    "README.md",
    OUTPUT_NAME,
    "__pycache__",
]


def read_module_prop():
    """Baca module.prop untuk mendapatkan versi & nama module."""
    prop_path = os.path.join(MODULE_DIR, "module.prop")
    props = {}
    if os.path.isfile(prop_path):
        with open(prop_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    key, _, value = line.partition("=")
                    props[key.strip()] = value.strip()
    return props


def should_exclude(name):
    """Cek apakah file/folder harus dikeluarkan dari zip."""
    for ex in EXCLUDE:
        if name == ex or name.endswith(ex):
            return True
    return False


def build_zip(module_dir, output_path, temp_dir=None):
    """Kemas folder module menjadi file .zip Magisk."""
    if not os.path.isdir(module_dir):
        print(f"[ERROR] Folder module tidak ditemukan: {module_dir}")
        sys.exit(1)

    module_prop = read_module_prop()
    version = module_prop.get("version", GIT_VERSION)
    name = module_prop.get("name", "Faa Magisk Git")

    print("=" * 50)
    print("  Faa Magisk Git - Build Script")
    print("=" * 50)
    print(f"  Module     : {name}")
    print(f"  Version    : {version}")
    print(f"  Input dir  : {module_dir}")
    print(f"  Output     : {output_path}")
    print("-" * 50)
    print("  Mengemas module...")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(module_dir):
            # Skip folder yang dikecualikan
            dirs[:] = [d for d in dirs if not should_exclude(d)]
            for file in files:
                # Skip file yang tidak diperlukan
                if should_exclude(file) or file.endswith(('.pyc', '.DS_Store')):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, module_dir)
                zf.write(file_path, arcname)
                print(f"    + {arcname}")

    size = os.path.getsize(output_path) / 1024
    print("-" * 50)
    print(f"[SUCCESS] Module berhasil dibuat!")
    print(f"  File    : {output_path}")
    print(f"  Ukuran  : {size:.1f} KB")
    print(f"  Waktu   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    return output_path


def main():
    print(f"[INFO] Base dir : {BASE_DIR}")
    print(f"[INFO] Module dir: {MODULE_DIR}")

    if not os.path.isdir(MODULE_DIR):
        print(f"[ERROR] Folder module tidak ditemukan: {MODULE_DIR}")
        sys.exit(1)

    if not os.path.isdir(os.path.join(MODULE_DIR, "META-INF")):
        print("[WARNING] Folder META-INF tidak ditemukan!")
        print("[WARNING] Module mungkin tidak bisa diinstall oleh Magisk.")

    if TEMP_DIR:
        os.makedirs(TEMP_DIR, exist_ok=True)

    build_zip(MODULE_DIR, OUTPUT_FILE, TEMP_DIR)


if __name__ == "__main__":
    main()
