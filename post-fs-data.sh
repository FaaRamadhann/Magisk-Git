#!/system/bin/sh

# Faa Magisk Git - post-fs-data
# Dipasang saat boot (post-fs-data) sebagai ROOT.
# - Binary Git & library disimpan di direktori modul /data/adb/modules
#   yang HANYA bisa diakses root.
# - Agar pengguna NON-root bisa memakainya, kita bind-mount runtime git
#   ke /data/local/tmp/faagit/git (path yang bisa ditelusuri pengguna biasa).

MODULE_DIR=/data/adb/modules/faagit
GIT_SRC="$MODULE_DIR/system/git"

GIT_MOUNT=/data/local/tmp/faagit/git

LOG=/data/local/tmp/faagit.log
echo "== post-fs-data $(date) ==" >> "$LOG" 2>/dev/null

# Pastikan binary & library terbaca
for d in "$GIT_SRC"/bin "$GIT_SRC"/libexec; do
    find "$d" -type f -exec chmod 755 {} \; 2>/dev/null
done
find "$GIT_SRC"/lib -maxdepth 1 -type f -exec chmod 644 {} \; 2>/dev/null

# Bind-mount runtime git ke lokasi yang bisa diakses user non-root
if [ -x "$GIT_SRC/bin/git" ]; then
    mkdir -p /data/local/tmp/faagit
    chmod 755 /data/local/tmp/faagit 2>/dev/null
    # Hanya bind-mount bila belum ter-mount (misal saat boot berulang)
    if ! mountpoint -q "$GIT_MOUNT" 2>/dev/null; then
        mkdir -p "$GIT_MOUNT"
        if mount --bind "$GIT_SRC" "$GIT_MOUNT" 2>>"$LOG"; then
            echo "  bind-mount OK: $GIT_MOUNT" >> "$LOG" 2>/dev/null
        else
            echo "  bind-mount GAGAL -> fallback root-only" >> "$LOG" 2>/dev/null
        fi
    fi
    setprop faagit.ready true
    chmod 755 "$GIT_MOUNT" 2>/dev/null
    echo "  Git module ready" >> "$LOG" 2>/dev/null
else
    echo "  ERROR: git binary tidak tersedia" >> "$LOG" 2>/dev/null
fi
