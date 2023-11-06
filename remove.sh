#!/bin/bash
rm -rf build dist src/handycon.egg-info
sudo rm -rf /usr/lib/python3*/site-packages/handycon*
sudo rm /usr/bin/handycon
sudo rm -rf /usr/share/handygccs
sudo rm -rf /etc/handygccs
sudo rm /usr/lib/systemd/system/handycon.service
sudo rm /usr/lib/udev/hwdb.d/59-handygccs-ayaneo.hwdb
sudo rm /usr/lib/udev/rules.d/60-handycon.rules
sudo systemd-hwdb update
sudo udevadm control -R

