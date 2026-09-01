#!/sbin/sh

# Faa Magisk Git - Installer customization script
# Menyalin binary Git systemless, membuat symlink & mengatur permission.

SKIPMOUNT=false
PROPFILE=false
POSTFSDATA=true
LATESTARTSERVICE=true

GIT_DIR="$MODPATH/system/git"
LIB64_DIR="$MODPATH/system/lib64"

ui_print "********************************"
ui_print "   Faa Magisk Git"
ui_print "********************************"
ui_print "  Author : Faa Ramadhan"
ui_print "  Arch   : $(getprop ro.product.cpu.abi 2>/dev/null)"
ui_print " "

if [ -d "$GIT_DIR" ]; then
    ui_print "  [1/3] Menyiapkan symlink Git..."

    # Buat symlink dari manifest (.symlinks) yang dibuat oleh fetch_git.py
    # Path di manifest relatif terhadap root module (system/git/... atau
    # system/lib64/...).
    MANIFEST="$GIT_DIR/.symlinks"
    if [ -f "$MANIFEST" ]; then
        SYMLINK_COUNT=0
        while IFS= read -r line; do
            [ -z "$line" ] && continue
            path="${line%%	*}"
            target="${line##*	}"
            [ -z "$path" ] && continue
            if [ -e "$MODPATH/$path" ]; then
                ui_print "    . skip (exist): $path"
                continue
            fi
            ln -s "$target" "$MODPATH/$path" 2>/dev/null && SYMLINK_COUNT=$((SYMLINK_COUNT + 1))
        done < "$MANIFEST"
        ui_print "    $SYMLINK_COUNT symlink dibuat"
    fi

    ui_print "  [2/3] Menyiapkan permission..."
    # Binary & library harus executable
    find "$GIT_DIR/bin" -type f -exec chmod 755 {} \; 2>/dev/null
    find "$GIT_DIR/libexec" -type f -exec chmod 755 {} \; 2>/dev/null
    find "$GIT_DIR/lib" "$LIB64_DIR" -maxdepth 1 -type f -exec chmod 644 {} \; 2>/dev/null
    chmod 755 "$MODPATH/system/bin/git" 2>/dev/null

    ui_print "  [3/3] Menghapus file kerja build..."
    rm -f "$GIT_DIR/.symlinks" "$GIT_DIR/.gitversion"

    ui_print " "
    ui_print "  Git siap. Wrapper: /system/bin/git"
    ui_print "  Runtime (root&user): /data/local/tmp/faagit/git"
else
    ui_print "  ! system/git tidak ditemukan."
    ui_print "  ! Jalankan fetch_git.py dulu lalu build.py."
fi

ui_print " "
ui_print "Installation complete!"
ui_print "Please reboot your device to apply changes."
ui_print " "
