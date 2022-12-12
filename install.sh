#!/bin/bash
set -e
echo "Installing HandyGCCS..."
sudo pacman -Sy --noconfirm - < pkg_depends.list
< pip_depends.list xargs python3 -m pip install
echo "Enabling controller functionality. NEXT users will need to configure the Home button in steam."
if [ ! -d "/usr/share/handygccs/scripts" ]
then
    mkdir -p "/usr/share/handygccs/scripts"
fi
cp -v constants.py /usr/share/handygccs/scripts
cp -v handycon.py /usr/share/handygccs/scripts
cp -v handycon.service /usr/lib/systemd/system/
cp -v handycon.conf /usr/lib/modules-load.d/
cp -v 60-handycon.rules /usr/lib/udev/rules.d/
if [ ! -d "/usr/share/libretro/autoconfig/udev" ]
then
    mkdir -p "/usr/share/libretro/autoconfig/udev"
fi
cp -v HandyGCCS-Controller.cfg /usr/share/libretro/autoconfig/udev/
udevadm control -R
systemctl enable handycon && systemctl start handycon
echo "Installation complete. You should now have additional controller functionality."
exit 0
