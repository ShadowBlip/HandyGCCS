#!/bin/bash
set -e

echo "Removing HandyGCCS..."
systemctl stop handycon && systemctl disable handycon
rm -v /usr/lib/modules-load.d/handycon.conf
rm -v /usr/lib/systemd/system/handycon.service
rm -v /usr/lib/udev/rules.d/60-handycon.rules
rm -v /usr/share/handygccs/scripts/constants.py
rm -v /usr/share/handygccs/scripts/handycon.py
rm -v /usr/share/libretro/autoconfig/udev/HandyGCCS-Controller.cfg
udevadm control -R
echo "Removal complete. Original configuration has been restored."
exit 0
