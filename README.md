# HandyGCCS
Handheld Game Console Controller Support (Handy Geeks) for Linux

Designed to bring the full controller functionality to handheld game consoles including:
- Programmable extra buttons
- Rumble effects

## Background
Many of the handheld game consoles designed for windows have buttons on then in addition to the normal "X-Box" style controls. These controls are typically keyboard macros for built in windows functions (such as CTRL+ALT+DEL). This software captures all input from these devices, as well as the built in controller, hides them from the system, and creates a new virtual controller that acts as a single input device. This ensures that input isn't duplicated, and all buttons appear to come from the same controller.

## Supported Devices

### Anbernic
- Win600

### AOKZOE
- AOKZOE A1 AR07
- AOKZOE A1 Pro
 
### ASUS
- ROG Ally

### Aya Neo
- Founders Edition and 2021 Series
- Next Series
- Air Series
- 2 Series
- GEEK Series

### Ayn
- Loki Max
- Loki Zero
- Loki MiniPro

### GPD
- GPD Win3
- GPD WinMax2
- GPD Win4

### OneNetBook
- OneXPlayer 1S
- OneXPlayer Mini
- OneXPlayer Mini Pro
- OneXFly

## Installation

### From the AUR
```
pikaur -Sy handygccs-git
sudo systemctl enable --now handycon
```

### From Source

```
git clone https://github.com/ShadowBlip/HandyGCCS.git
cd HandyGCCS
sudo ./build
sudo systemctl enable --now handycon
```

## Removal

### From the AUR
`pikaur -U handygccs-git`
