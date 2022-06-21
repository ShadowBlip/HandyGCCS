#!/bin/bash
set -e

echo "Removing HandyGCCS..."
systemctl stop handycon && systemctl disable handycon
rm -v /usr/local/bin/handycon.py 
rm -v /etc/systemd/system/handycon.service 
rm -v /etc/udev/rules.d/60-handycon.rules 
udevadm control -R
echo "Removal complete. Original configuration has been restored."
exit 0
