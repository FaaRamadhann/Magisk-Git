<div align="center">

# Faa Magisk Git

Modul **Magisk / KernelSU / APatch** untuk menginstal **Git** ke dalam perangkat Android secara systemless.

[![Magisk](https://img.shields.io/badge/Magisk-Module-%2301af9c)](https://github.com/topjohnwu/Magisk)
[![KernelSU](https://img.shields.io/badge/KernelSU-Module-%23231816)](https://github.com/tiann/KernelSU)
[![APatch](https://img.shields.io/badge/APatch-Module-%2332de84)](https://github.com/apatch/apatch)
[![Git](https://img.shields.io/badge/Git-2.55.0-%23de4c36)](https://git-scm.com)
[![License](https://img.shields.io/github/license/FaaRamadhann/Magisk-Git)](LICENSE)

</div>

---

## Apa itu Faa Magisk Git?

Modul ini menyediakan **Git** (`git`) sebagai perintah sistem di Android. Setelah terinstall,
kamu bisa menjalankan Git langsung dari terminal — tanpa `su -c` setiap kali, tanpa Termux,
dan tersedia di PATH (`/system/bin/git`).

Bineri Git + seluruh library dependency (libcurl, openssl, pcre2, zlib, libssh2, dsb.)
diambil dari **repo paket resmi Termux** (`packages.termux.dev`) untuk arsitektur **arm64**.
Versi modul otomatis mengikuti versi paket git Termux terkini.

## Fitur

- **Git 2.55.0** (arm64-v8a) lengkap dengan dependency (curl, openssl, zlib, pcre2, ...)
- Perintah langsung: `git`
- Mendukung operasi Git standar: `init`, `add`, `commit`, `clone`, `pull`, `push`, `log`, dll.
- **Tidak butuh `su`** — cukup ketik di shell biasa
- Runtime diletakkan di `/system` (lib di `/system/lib64`) sehingga user non-root bisa menjalankannya
- `fetch_git.py` untuk menarik versi terbaru dari repo Termux + `build.py` untuk mem-packing jadi `.zip`

## Persyaratan

- **Android:** 8.0+ (direkomendasikan)
- **Arsitektur:** ARM64 (arm64-v8a)
- **Root:** Magisk / KernelSU / APatch

> ⚠️ Modul ini dikemas untuk **arm64**. Perangkat `x86_64`/`armeabi-v7a` perlu build ulang
> (lihat bagian Build dari Source).

---

## Cara Install

Ada dua cara: **via PC (Windows/Linux)** atau **via Termux di HP**.

### A. Via PC (Windows / Linux) — pakai `adb push`

**Langkah 0 — Siapkan (clone + build zip):**

Prasyarat: sudah ada `git` dan `python 3` (versi apa pun) di PC.

```bash
# 1. Clone repo ini
git clone https://github.com/FaaRamadhann/Magisk-Git.git
cd Magisk-Git

# 2. (Opsional) Kalau mau versi terbaru dengan bineri yang sudah termasuk,
#    langsung pakai zip yang sudah tersedia (Faa-Magisk-Git.zip).
#    Kalau kamu edit sendiri dan mau re-pack:
python build.py
```

Perintah `python build.py` menghasilkan file:
```
Faa-Magisk-Git.zip
```

> Membangun dari nol butuh internet (mengunduh paket `.deb` Termux). Kalau tinggal
> `git clone`, zip `Faa-Magisk-Git.zip` sudah ikut tersedia di repo ini.

**Langkah 1 — Hubungkan HP ke PC:**

Aktifkan **USB Debugging** di HP (Developer Options), lalu colok USB.

```bash
# Cek HP terdeteksi
adb devices
# Harus muncul status "device"

# (Windows) Untuk memastikan adb ada di PATH, atau pakai path penuh,
# misal: C:\AndroidSDK\platform-tools\adb.exe
```

**Langkah 2 — Push zip ke HP:**

```bash
adb push Faa-Magisk-Git.zip /sdcard/
```

**Langkah 3 — Install lewat Magisk (dari HP):**

Buka aplikasi **Magisk** → tab **Modul** → **Install dari penyimpanan** → pilih
`Faa-Magisk-Git.zip`.

Atau via terminal/shell (root):

```bash
# masuk shell adb
adb shell
# lalu jalankan sebagai root
su -c 'magisk --install-module /sdcard/Faa-Magisk-Git.zip'
```

**Langkah 4 — Reboot:**

```
reboot
```

**Langkah 5 — Cek:**

```bash
git --version   # git version 2.55.0
```

---

### B. Via Termux (di HP, tanpa PC)

Prasyarat: sudah ada **Termux** dan akses **root** (`su`).

**Langkah 1 — Install git & clone:**

```bash
pkg install -y git python
git clone https://github.com/FaaRamadhann/Magisk-Git.git
cd Magisk-Git
```

**Langkah 2 — (Opsional) Build zip:**

```bash
python build.py
```

> Kalau file `Faa-Magisk-Git.zip` sudah ada di repo, langkah ini bisa dilewati.
> Membutuhkan internet bila ingin menarik bineri terbaru: `python fetch_git.py`.

**Langkah 3 — Pindahkan zip ke penyimpanan (agar bisa dipilih Magisk):**

```bash
cp Faa-Magisk-Git.zip /sdcard/
```

**Langkah 4 — Install via Magisk:**

Buka aplikasi **Magisk** → **Modul** → **Install dari penyimpanan** → pilih zip.

Atau lewat Termux dengan root:

```bash
su -c 'magisk --install-module /sdcard/Faa-Magisk-Git.zip'
```

**Langkah 5 — Reboot:**

```bash
su -c reboot
```

**Langkah 6 — Cek:**

```bash
git --version
```

---

## Cara Pakai

Setelah reboot, perintah **`git`** langsung tersedia dari **shell normal** (tanpa `su`):

```bash
# Cek versi
git --version

# Konfigurasi identitas (wajib sekali sebelum commit)
git config --global user.name "Nama Kamu"
git config --global user.email "email@kamu.com"

# Bikin repo baru
mkdir proyek && cd proyek
git init
echo "hallo" > readme.txt
git add readme.txt
git commit -m "pesan pertama"

# Clone repo dari internet
git clone https://github.com/FaaRamadhann/Magisk-Git.git
cd Magisk-Git && git log --oneline -5
```

**Perintah `git` bisa dipakai langsung tanpa `su`** — library berada di `/system/lib64`
(jalur pencarian linker default), dan runtime di-bind ke `/data/local/tmp/faagit/git`
agar bisa diakses user biasa.

Wrapper otomatis menonaktifkan config/attribute sistem bawaan Termux
(`GIT_CONFIG_NOSYSTEM=1` / `GIT_ATTR_NOSYSTEM=1`) agar tidak muncul error
`unable to access .../gitconfig: Permission denied`. Konfigurasi global disimpan
di `~/.gitconfig` biasa.

> **HTTPS clone (SSL):** bila muncul `SSL certificate problem`, arahkan Git ke kumpulan
> CA Android:
> ```bash
> SSL_CERT_DIR=/system/etc/security/cacerts git clone https://github.com/org/repo.git
> ```
> atau set sekali untuk sesi shell: `export SSL_CERT_DIR=/system/etc/security/cacerts`.

---

## Struktur Modul

```
Magisk-Git/
├── module.prop            # Metadata modul (id, nama, versi, pengarang)
├── customize.sh           # Instalasi: buat symlink + atur permission
├── post-fs-data.sh        # Bind-mount runtime git utk akses user non-root
├── service.sh             # Verifikasi git saat late_start
├── uninstall.sh           # Bersih-bersih saat uninstall
├── build.py               # Packing modul jadi .zip
├── fetch_git.py           # Unduh & ekstrak git + dependency dari repo Termux
├── README.md / LICENSE
├── META-INF/              # Installer Magisk
└── system/                # Di-mount ke /system (bisa diakses non-root)
    ├── bin/git            # -> /system/bin/git (wrapper launcher, masuk PATH)
    ├── git/               # Runtime Git (bin, lib, libexec/git-core, share)
    └── lib64/             # -> /system/lib64 (lib yang di-link user non-root)
```

**Cara kerja:**

1. Magisk me-mount `system/` module ke `/system/`. Wrapper `git` (`system/bin/git`,
   shell script) tersedia di `/system/bin/git` → masuk PATH.
2. Folder `system/lib64` di-mount ke `/system/lib64` → **library ditemukan
   langsung oleh linker** (bionic mengabaikan `LD_LIBRARY_PATH` untuk user non-root,
   jadi lib wajib ada di jalur pencarian default).
3. Seluruh runtime Git berada di `/data/adb/modules/faagit/system/git`. Karena path
   `/data/adb/*` hanya bisa dilewati root, `post-fs-data.sh` **bind-mount** runtime ke
   `/data/local/tmp/faagit/git` agar binary & `libexec/git-core` bisa dieksekusi oleh
   user biasa.
4. Wrapper `git` menyetel `LD_LIBRARY_PATH`, `GIT_EXEC_PATH`, `GIT_TEMPLATE_DIR` lalu
   `exec` binary Git asli.

---

## Build dari Source (Opsional / Lanjutan)

Tidak perlu meng-compile apa pun — bineri diambil dari **repo paket Termux**
(`packages.termux.dev`), sama seperti bineri yang dipakai di Termux.

Prasyarat: **PC (Windows/Linux)** dengan **Python 3** + koneksi internet.

```bash
# 1. Tarik & ekstrak git + semua dependency (libcurl, openssl, zlib, pcre2, dll)
python fetch_git.py --arch aarch64

# 2. Pack jadi .zip
python build.py
```

Hasil:
```
Faa-Magisk-Git.zip
```

`fetch_git.py` akan:
- Membaca indeks paket Termux untuk arsitektur yang diminta (`aarch64`)
- Men-resolve dependency Git otomatis
- Mengunduh `.deb` masing-masing (cache di `../temp/deb`)
- Mengekstrak `bin/`, `lib/`, `libexec/`, `share/` ke `system/git/`
- Menyiapkan `system/lib64` (SONAME ber-versi untuk jalur linker non-root)
- Menyinkronkan `module.prop` ke versi git terbaru

Arsitektur yang didukung oleh Termux: `aarch64`, `arm`, `x86_64`, `i686`.

---

## Troubleshooting

| Masalah | Solusi |
| --- | --- |
| `Git tidak ditemukan` setelah install | Wajib **reboot** setelah install agar `system/bin` di-mount. Gunakan versi zip terbaru. |
| `git: inaccessible or not found` | Wrapper ketemu tapi runtime belum ada — reinstall modul & reboot. |
| Hanya jalan saat `su -c` (root) | Modul versi lama. Update ke versi terbaru (lib baru di `/system/lib64` + bind-mount runtime). |
| `library "libz.so.1" not found` | Perangkat belum reboot setelah update, atau zip lama. Reinstall & reboot. |
| `SSL certificate problem` saat clone https | `SSL_CERT_DIR=/system/etc/security/cacerts git clone ...` |
| Arsitektur tidak didukung | Modul untuk `arm64`; perangkat lain perlu `python fetch_git.py --arch <arch>` & build ulang. |

---

## Kredit

- [Termux](https://termux.dev) — repo paket & bineri git + dependency (lisensi masing-masing paket)
- [Git](https://git-scm.com) — [Git License](https://github.com/git/git/blob/master/COPYING)

## Lisensi

[MIT License](LICENSE) — © 2026 Faa Ramadhan
