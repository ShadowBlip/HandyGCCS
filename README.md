# HandyGCCS
Handheld Game Console Controller Support (Handy Geeks) for Linux

Designed to bring the full controller functionality to handheld game consoles including:
- Programmable extra buttons.
- Gyroscope joystick support.
- Support for all Aya Neo and OneXPlayer devices.

### Under active development, check back later!

## Installation

### From the AUR
```
pikaur -Sy handygccs-git
sudo udevadm control -R
sudo systemctl enable handycon && sudo systemctl start handycon
```

### From Source

```
git clone https://github.com/ShadowBlip/HandyGCCS.git
cd HandyGCCS
sudo make install
```

## Removal

### From the AUR
`pikaur -U handygccs-git`

### From Source
```
cd <clonedir>
sudo make clean
```

