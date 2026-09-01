#!/usr/bin/env python3
"""
Faa Magisk Git - Fetch & Inject Script
Mengunduh paket .deb git Termux (+ dependency) lalu mengekstrak binary-nya
ke dalam module/system/git/ agar menjadi modul Git systemless.

Versi Git mengikuti paket repo Termux (paket git). Jika versi di
module.prop tidak cocok, skrip ini akan menulis ulang sesuai versi paket.

Cara pakai:
    python fetch_git.py            # default: aarch64
    python fetch_git.py --arch arm
    python fetch_git.py --arch x86_64

Setelah selesai, jalankan build.py untuk mengemas module menjadi .zip.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

# ---------------------------------------------------------------- config
HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_DIR = HERE
SYSTEM_GIT = os.path.join(MODULE_DIR, "system", "git")
TEMP_DIR = os.path.join(os.path.dirname(HERE), "temp")
DEB_DIR = os.path.join(TEMP_DIR, "deb")

REPO_BASE = "https://packages.termux.dev/apt/termux-main"
PACKAGES_URL = REPO_BASE + "/dists/stable/main/binary-{arch}/Packages"

# Arsitektur Termux -> nama folder lokal yang dipakai script instalasi
ARCH_LOCAL_MAP = {
    "aarch64": "arm64",
    "arm":     "arm",
    "x86_64":  "x86_64",
    "i686":    "i686",
}

# Root package yang kita butuhkan. Semua dependency di-resolve otomatis.
ROOT_PACKAGES = ["git"]

# Paket yang berupa file konfigurasi/data ringan tetap di-scan, tapi
# path binary/lib di bawah prefix data ter-generate dari isi tarball.


def fetch_url(url, dest=None):
    print(f"  [net] {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "faagit-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if dest:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        print(f"  [sav] {dest} ({len(data)} bytes)")
    return data


# ------------------------------------------------------------- Packages idx
def parse_packages(text):
    """Parse APT Packages index -> {name: {field: value}}"""
    result = {}
    for block in text.split("\n\n"):
        lines = [ln for ln in block.split("\n") if ln]
        if not lines or not lines[0].startswith("Package:"):
            continue
        info = {}
        for ln in lines:
            if ": " in ln:
                k, _, v = ln.partition(": ")
                info.setdefault(k, v)
        name = info.get("Package")
        if name:
            result[name] = info
    return result


def parse_dep_names(dep_str):
    """Extract plain package names from an APT Depends string."""
    if not dep_str:
        return []
    names = set()
    for alt in dep_str.split(","):
        alt = alt.strip()
        m = re.match(r"^([a-zA-Z0-9+.-]+)", alt)
        if m:
            names.add(m.group(1))
    return sorted(names)


def resolve_closure(pkgmap, roots):
    """Resolver dependency closure (mengikuti Depends)."""
    needed = set()
    queue = list(roots)
    while queue:
        p = queue.pop(0)
        if p in needed:
            continue
        info = pkgmap.get(p)
        if not info:
            print(f"  [warn] package '{p}' tidak ditemukan di repo")
            continue
        needed.add(p)
        for dep in parse_dep_names(info.get("Depends", "")):
            if dep not in needed:
                queue.append(dep)
    return needed


# ------------------------------------------------------------- deb extraction
def extract_ar_member(ar_bytes, member_name):
    """Ekstrak satu member dari archive ar (format .deb)."""
    if ar_bytes[:8] != b"!<arch>\n":
        raise RuntimeError("bukan archive ar")
    pos = 8
    while pos < len(ar_bytes):
        if ar_bytes[pos:pos+16].strip() == b"":
            break
        name = ar_bytes[pos:pos+16].decode("utf-8", "replace").strip()
        size_str = ar_bytes[pos+48:pos+58].decode("utf-8", "replace").strip()
        try:
            size = int(size_str)
        except ValueError:
            size = 0
        data_start = pos + 60
        data = ar_bytes[data_start:data_start+size]
        if name == member_name:
            return data
        # ar members are 2-byte aligned
        pos = data_start + size + (2 - (size % 2)) % 2
    raise RuntimeError(f"member {member_name} tidak ditemukan")


def extract_deb(deb_path, out_dir):
    """Extract data.tar.* dari .deb (format ar) ke out_dir."""
    os.makedirs(out_dir, exist_ok=True)
    with open(deb_path, "rb") as f:
        ar_bytes = f.read()

    # cari member data.tar.*
    data_member = None
    magic = ar_bytes[:8]
    if magic == b"!<arch>\n":
        pos = 8
        while pos < len(ar_bytes):
            if ar_bytes[pos:pos+16].strip() == b"":
                break
            name = ar_bytes[pos:pos+16].decode("utf-8", "replace").strip()
            if name.startswith("data.tar"):
                data_member = name
                break
            size_str = ar_bytes[pos+48:pos+58].decode("utf-8", "replace").strip()
            try:
                size = int(size_str)
            except ValueError:
                size = 0
            pos = pos + 60 + size + (2 - (size % 2)) % 2

        if data_member:
            tar_bytes = extract_ar_member(ar_bytes, data_member)
        else:
            raise RuntimeError(f"tidak ada data.tar di {deb_path}")
    else:
        # fallback: coba sebagai zip (format lama)
        import zipfile
        with zipfile.ZipFile(deb_path) as zf:
            inner = [n for n in zf.namelist() if n.startswith("data.tar.")]
            if not inner:
                raise RuntimeError(f"tidak ada data.tar di {deb_path}")
            tar_bytes = zf.read(inner[0])

    tmp_tar = os.path.join(tempfile.gettempdir(), "faagit_" + os.path.basename(os.path.basename(deb_path)))
    with open(tmp_tar, "wb") as f:
        f.write(tar_bytes)
    # gunakan mode r:* untuk auto-detect kompresi (xz, gz, bz2, dll)
    with tarfile.open(tmp_tar, mode="r:*") as tar:
        _safe_extract(tar, out_dir)
    os.remove(tmp_tar)
    return out_dir


def _safe_extract(tar, path):
    """Ekstrak tar dengan proteksi path traversal."""
    dest = os.path.realpath(path)
    for member in tar.getmembers():
        member_path = os.path.realpath(os.path.join(dest, member.name))
        if not member_path.startswith(dest + os.sep) and member_path != dest:
            continue
    tar.extractall(dest, filter="data") if hasattr(tarfile, "data_filter") else tar.extractall(dest)


def copy_tree(src, dst, symlink_manifest, base_rel):
    """Salin file reguler; catat symlink ke manifest (untuk dibuat saat install)."""
    os.makedirs(dst, exist_ok=True)
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(target, exist_ok=True)
        for f in files:
            s = os.path.join(root, f)
            d = os.path.join(target, f)
            if os.path.islink(s):
                # catat symlink: <relative-path-module> -> <target>
                mod_rel = os.path.join(base_rel, rel if rel != "." else "", f)
                symlink_manifest.append((mod_rel.replace("\\", "/"),
                                         os.readlink(s).replace("\\", "/")))
            else:
                try:
                    shutil.copy2(s, d)
                except OSError as e:
                    # lewati file yang path-nya bermasalah di Windows
                    print(f"  [skip] {d}: {e}")


def collect_deb_files(extract_root, git_root, prefix, symlink_manifest):
    """
    Pindahkan file dari folder data (extract_root/data/...) ke
    git_root dengan struktur:
      bin/   -> git_root/bin
      lib/   -> git_root/lib
      share/ -> git_root/share (git-core, templates, dll)
      libexec/ -> git_root/libexec
    prefix: nilai $PREFIX yang dipakai paket (biasanya /data/data/com.termux/files/usr)
    """
    data_dir = os.path.join(extract_root, "data", prefix.lstrip("/"))
    if not os.path.isdir(data_dir):
        # coba cari otomatis
        cand = os.path.join(extract_root, "data")
        sub = os.path.join(cand, *[p for p in prefix.split("/") if p])
        if os.path.isdir(sub):
            data_dir = sub
        else:
            data_dir = find_data_root(extract_root)
    if not os.path.isdir(data_dir):
        return 0

    count = 0
    for sub in ("bin", "libexec", "lib"):
        s = os.path.join(data_dir, sub)
        if os.path.isdir(s):
            # base path manifest relatif terhadap root MODULE:
            # system/git/<sub>/...
            base_rel = os.path.join("system", "git", sub)
            copy_tree(s, os.path.join(git_root, sub), symlink_manifest, base_rel)
            count += 1
    s = os.path.join(data_dir, "share")
    if os.path.isdir(s):
        # share/git-core -> git_root/share/git-core dsb
        copy_tree(s, os.path.join(git_root, "share"), symlink_manifest,
                  os.path.join("system", "git", "share"))
        count += 1
    # file khusus di root data (misal certs)
    for name in os.listdir(data_dir):
        s = os.path.join(data_dir, name)
        if os.path.isfile(s) and not os.path.islink(s):
            shutil.copy2(s, os.path.join(git_root, name))
            count += 1
    return count


def find_data_root(extract_root):
    data = os.path.join(extract_root, "data")
    if os.path.isdir(data):
        for root, dirs, _files in os.walk(data):
            if "bin" in dirs or "lib" in dirs:
                return root
            dirs[:] = [d for d in dirs if d not in ("..",)]
            # hentikan bila sudah dalam
    return data


# --------------------------------------------------------------------------
# system/lib64 : library yang bisa di-link oleh pengguna NON-root.
#
# Bionic linker Android (untuk user non-root) mengabaikan LD_LIBRARY_PATH,
# sehingga library git harus berada di jalur pencarian default linker, yaitu
# /system/lib64. Magic mount Magisk menggabungkan module/system/lib64 ke
# /system/lib64 secara otomatis.
#
# Untuk menghindari tabrakan dengan library AOSP, kita hanya menyalin nama
# SONAME *berversi* (libcrypto.so.3, libssl.so.3, libz.so.1, libexpat.so.1,
# libncursesw.so.6, dst) — nama polos seperti libcrypto.so/libssl.so/libz.so
# (punya AOSP) TIDAK disalin.
# --------------------------------------------------------------------------
def create_system_lib64(git_root, symlink_manifest):
    """Salin library SONAME yang dibutuhkan git ke system/lib64."""
    lib_src = os.path.join(git_root, "lib")
    lib64_dir = os.path.join(MODULE_DIR, "system", "lib64")
    # bersihkan dulu agar tidak ada file basi dari run sebelumnya
    if os.path.isdir(lib64_dir):
        shutil.rmtree(lib64_dir, ignore_errors=True)
    os.makedirs(lib64_dir, exist_ok=True)

    needed_versioned = {
        "libcrypto.so.3",
        "libssl.so.3",
        "libz.so.1",
        "libexpat.so.1",
        "libiconv.so",
        "libcharset.so",
        "libpcre2-8.so",
        "libcurl.so",
        "libnghttp2.so",
        "libnghttp3.so",
        "libngtcp2.so",
        "libngtcp2_crypto_ossl.so",
        "libssh2.so",
        "libncursesw.so.6",
    }

    # peta SONAME -> file rujukan (manangani symlink berantai di lib/)
    def link_target(p, depth=0):
        if depth > 20:
            return p
        if os.path.islink(p):
            return link_target(os.path.join(os.path.dirname(p), os.readlink(p)),
                               depth + 1)
        return p

    # peta soname -> symlink target dari manifest (untuk soname yang
    # di lib/ berupa symlink dan tidak ada sebagai file di Windows)
    # Path manifest relatif terhadap root MODULE: "system/git/lib/<soname>"
    manifest_target = {}
    for p_rel, tgt in symlink_manifest:
        if p_rel.startswith("system/git/lib/"):
            manifest_target[p_rel.rsplit("/", 1)[1]] = tgt

    for soname in sorted(needed_versioned):
        src_file = os.path.join(lib_src, soname)
        # cari file real: cek path asli, lalu manifest, lalu sisa lib
        if not (os.path.exists(src_file) or os.path.islink(src_file)) \
                and soname in manifest_target:
            tgt = manifest_target[soname]
            real = link_target(os.path.join(lib_src, tgt))
        else:
            real = link_target(src_file)
        if not os.path.exists(real):
            # coba langsung dari lib bila real masih tak ditemukan
            if os.path.exists(src_file):
                real = src_file
        if not os.path.exists(real):
            print(f"  [lib64] skip (tidak ada): {soname}")
            continue

        if os.path.basename(real) != soname:
            # soname → symlink ke nama file real (selalu dicatat ke manifest
            # agar dibuat ulang saat install di perangkat)
            dst = os.path.join(lib64_dir, soname)
            if not (os.path.exists(dst) or os.path.islink(dst)):
                os.symlink(os.path.basename(real), dst)
            symlink_manifest.append(("system/lib64/" + soname,
                                     os.path.basename(real)))
        # salin file real
        shutil.copy2(real, os.path.join(lib64_dir, os.path.basename(real)))
    print(f"  [lib64] disiapkan: {sorted(os.listdir(lib64_dir))}")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description="Fetch & inject Termux git untuk Magisk module")
    ap.add_argument("--arch", default="aarch64",
                    choices=["aarch64", "arm", "x86_64", "i686"])
    args = ap.parse_args()

    arch = args.arch
    local_arch = ARCH_LOCAL_MAP[arch]
    print("=" * 50)
    print("  Faa Magisk Git - Fetch & Inject")
    print("=" * 50)
    print(f"  Arch        : {arch}")
    print(f"  Repo        : {REPO_BASE}")
    print(f"  Target dir  : {SYSTEM_GIT}")
    print(f"  Temp dir    : {TEMP_DIR}")
    print("-" * 50)

    # 1. Unduh index Packages
    print("[1/4] Mengunduh index Packages...")
    pkgs_text = fetch_url(PACKAGES_URL.format(arch=arch)).decode("utf-8", "ignore")
    pkgmap = parse_packages(pkgs_text)
    print(f"  Total paket di repo: {len(pkgmap)}")

    # 2. Resolve dependency
    closure = resolve_closure(pkgmap, ROOT_PACKAGES)
    print(f"[2/4] Dependency ter-resolve ({len(closure)} paket):")
    for p in sorted(closure):
        print(f"       - {p} = {pkgmap[p].get('Version')}")

    # 3. Unduh semua .deb
    os.makedirs(DEB_DIR, exist_ok=True)
    print("[3/4] Mengunduh .deb paket...")
    deb_files = []
    for p in sorted(closure):
        info = pkgmap[p]
        fn = info.get("Filename")
        if not fn:
            print(f"  [warn] {p}: tidak ada Filename")
            continue
        url = REPO_BASE + "/" + fn
        fname = os.path.basename(fn)
        dest = os.path.join(DEB_DIR, fname)
        # pakai cache bila ada
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            print(f"  [cach] {fname}")
        else:
            fetch_url(url, dest)
        deb_files.append(dest)

    # 4. Ekstrak & gabungkan ke system/git
    print("[4/4] Mengekstrak & menyusun system/git...")
    if os.path.isdir(SYSTEM_GIT):
        shutil.rmtree(SYSTEM_GIT)
    os.makedirs(SYSTEM_GIT, exist_ok=True)

    total_files = 0
    git_version = None
    symlink_manifest = []  # (path_rel, target)
    for deb in deb_files:
        base = os.path.basename(deb)
        name = base.split("_", 1)[0]
        # ambil versi dari nama file .deb (contoh: git_2.55.0_aarch64.deb)
        vers = re.findall(r"_([0-9][0-9.]+(?::[0-9.]+)?)(?:_|\.)", base)
        m = vers[0] if vers else None
        with tempfile.TemporaryDirectory(prefix="faagit_extract_") as tmp:
            try:
                extract_deb(deb, tmp)
            except Exception as e:
                print(f"  [warn] gagal ekstrak {base}: {e}")
                continue
            # tentukan prefix: baca dari path 'data/...' dalam paket
            data_root = os.path.join(tmp, "data")
            prefix = guess_prefix(data_root) or "/data/data/com.termux/files/usr"
            n = collect_deb_files(tmp, SYSTEM_GIT, prefix, symlink_manifest)
            print(f"  [ok] {name}: {n} file")
            total_files += n
            if name == "git" and m:
                git_version = m

    # system/lib64 : library untuk hal-link NON-root (via /system/lib64)
    print("  [lib64] Menyiapkan library untuk akses user non-root...")
    create_system_lib64(SYSTEM_GIT, symlink_manifest)

    # Tulis .gitversion marker
    verfile = os.path.join(SYSTEM_GIT, ".gitversion")
    with open(verfile, "w") as f:
        f.write(git_version or "unknown")
    print(f"  Marker version: {git_version}")

    # Sinkronkan versi ke module.prop (agar versi selalu cocok dengan paket git)
    if git_version:
        sync_module_prop(git_version)

    # Tulis manifest symlink untuk dibuat saat install
    manifest_path = os.path.join(SYSTEM_GIT, ".symlinks")
    sorted_manifest = sorted(set(symlink_manifest))
    with open(manifest_path, "w", encoding="utf-8") as f:
        for path_rel, target in sorted_manifest:
            f.write(f"{path_rel}\t{target}\n")
    print(f"  Symlink manifest: {len(sorted_manifest)} entri -> {manifest_path}")

    print("-" * 50)
    print(f"[DONE] {total_files} file disalin ke {SYSTEM_GIT}")
    print("  Jalankan 'python build.py' untuk mengemas module menjadi .zip")
    print("=" * 50)


def sync_module_prop(git_version):
    """Sinkronkan versi di module.prop dengan versi git yang di-fetch."""
    prop_path = os.path.join(MODULE_DIR, "module.prop")
    if not os.path.isfile(prop_path):
        return
    digits = git_version.split(":", 1)[-1].split("-", 1)[0]
    # buang sufiks non-numerik (mis. r1) -> versi murni x.y.z
    ver = ".".join(digits.split(".")[:3])
    # versionCode = xyyzz (mis. 2.55.0 -> 25500)
    parts = ver.split(".")
    while len(parts) < 3:
        parts.append("0")
    vercode = parts[0] + "".join(p.zfill(2) for p in parts[1:])
    lines = []
    with open(prop_path, "r", encoding="utf-8") as f:
        for ln in f:
            if ln.startswith("version="):
                ln = f"version={ver}\n"
            elif ln.startswith("versionCode="):
                ln = f"versionCode={vercode}\n"
            lines.append(ln)
    with open(prop_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"  module.prop disinkronkan -> version={ver}, versionCode={vercode}")


def guess_prefix(data_root):
    """Tebak prefix $PREFIX dari struktur data/... di paket .deb."""
    if not os.path.isdir(data_root):
        return None
    # data/<path>/bin , data/<path>/lib dst
    for root, dirs, _ in os.walk(data_root):
        if "bin" in dirs or "lib" in dirs or "libexec" in dirs:
            rel = os.path.relpath(root, data_root).replace("\\", "/")
            return "/" + rel
    return None


if __name__ == "__main__":
    main()
