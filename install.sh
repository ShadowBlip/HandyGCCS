#!/bin/bash
set -e
echo "Installing HandyGCCS..."
sudo pacman -Sy --noconfirm - < pkg_depends.list
< pip_depends.list xargs python3 -m pip install
echo "Enabling controller functionality. NEXT users will need to configure the Home button in steam."
cp -v constants.py /usr/local/bin/
cp -v handycon.py /usr/local/bin/
cp -v handycon.service /etc/systemd/system/
cp -v handycon.conf /etc/modules-load.d/
cp -v 60-handycon.rules /etc/udev/rules.d/
if [ ! -d "/usr/share/libretro/autoconfig/udev" ]
then
    mkdir -p "/usr/share/libretro/autoconfig/udev"
fi
cp -v HandyGCCS-Controller.cfg /usr/share/libretro/autoconfig/udev/
udevadm control -R
systemctl enable handycon && systemctl start handycon
echo "Installation complete. You should now have additional controller functionality."
exit 0
