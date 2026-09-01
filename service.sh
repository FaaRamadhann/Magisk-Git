#!/system/bin/sh

# Faa Magisk Git - late_start service
# Menyediakan Git di PATH untuk sesi shell & verifikasi install.

MODID=faagit
GIT_BIN=/data/adb/modules/$MODID/system/git/bin/git

LOG=/data/local/tmp/faagit.log
echo "== service $(date) ==" >> "$LOG" 2>/dev/null

# Cek apakah git berfungsi melalui wrapper
if [ -x /system/bin/git ]; then
    VER="$(/system/bin/git --version 2>/dev/null)"
    if [ -n "$VER" ]; then
        echo "  $VER" >> "$LOG" 2>/dev/null
    else
        echo "  ERROR: git gagal dijalankan (cek LD_LIBRARY_PATH/libs)" >> "$LOG" 2>/dev/null
    fi
else
    echo "  ERROR: /system/bin/git tidak ditemukan" >> "$LOG" 2>/dev/null
fi
