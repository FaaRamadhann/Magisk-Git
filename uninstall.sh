#!/system/bin/sh

# This script will be executed on module uninstall
# Clean up all traces of the module

rm -f /data/local/tmp/faagit.log
rm -rf /data/local/tmp/git
rm -f /data/adb/service.d/faagit.sh

# Clean up git config and data if they exist
rm -rf /data/local/tmp/.gitconfig

exit 0
