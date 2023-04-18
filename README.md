# HandyGCCS
Handheld Game Console Controller Support (Handy Geeks) for Linux

Designed to bring the full controller functionality to handheld game consoles including:
- Programmable extra buttons
- Gyroscope joystick input
- Rumble effects

## Background
Many of the handheld game consoles designed for windows have buttons on then in addition to the normal "X-Box" style controls. These controls are typically keyboard macros for built in windows functions (such as CTRL+ALT+DEL). This software captures all input from these devices, as well as the built in controller, hides them from the system, and creates a new virtual controller that acts as a single input device. This ensures that input isn't duplicated, and all buttons appear to come from the same controller.

## Emulated Buttons
Most of the buttons are mapped to the steam shortcuts for various functions in the new GamepadUI, to include:
- Quick Access Menu
- The Guide (Steam/Xbox/Playstion) button
- On Screen Keyboard
- Screenshot
- Escape

More functions can be added as possible configuration if desired for your personal cofiguration, submit an issue or pull request to ge them added. 

## Supported Devices
### Anbernic
- Win600

### AYANEO
- Founders Edition
- 2021 and 2021 Pro
- Next and Next Pro
- Air and Air Pro
- 2 and GEEK

### OneXPlayer
- OneXPlayer 1S
- OneXPlayer Gundam
- OneXPlayer AMD
- OneXPlayer Mini
- OneXPlayer Mini Pro

### AOK ZOE
- AOK ZOE A1 

### GPD
- GPD WinMax2
- GPD Win3 (Experimental)
- GPD Win4 (Experimental)

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

