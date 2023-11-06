#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

import sys
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff

from .. import constants as cons

handycon = None

def init_handheld(handheld_controller):
    global handycon
    devices = []
    proc_dev_fd = open('/proc/bus/input/devices', 'r')
    for line in proc_dev_fd:
        devices.append(line)
    proc_dev_fd.close()

    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.2
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    handycon.KEYBOARD_NAME = 'Asus Keyboard'
    handycon.KEYBOARD_2_NAME = 'Asus Keyboard'
    GAMEPAD_ADDRESS_LIST = [
            'usb-0000:08:00.3-2/input0',
            'usb-0000:09:00.3-2/input0',
            'usb-0000:0a:00.3-2/input0',
            ]
    KEYBOARD_ADDRESS_LIST = [
            'usb-0000:08:00.3-3/input0',
            'usb-0000:09:00.3-3/input0',
            'usb-0000:0a:00.3-3/input0',
            ]
    KEYBOARD_2_ADDRESS_LIST = [
            'usb-0000:08:00.3-3/input2',
            'usb-0000:09:00.3-3/input2',
            'usb-0000:0a:00.3-3/input2',
            ]
    for line in devices:
        for address in GAMEPAD_ADDRESS_LIST:
            if address in line:
                handycon.GAMEPAD_ADDRESS = address
        for address in KEYBOARD_ADDRESS_LIST:
            if address in line:
                handycon.KEYBOARD_ADDRESS = address
        for address in KEYBOARD_2_ADDRESS_LIST:
            if address in line:
                handycon.KEYBOARD_2_ADDRESS = address

    if not handycon.GAMEPAD_ADDRESS or not handycon.KEYBOARD_ADDRESS or not handycon.KEYBOARD_2_ADDRESS:
        handycon.logger.warn("Unable to identify one or more input devices by address. Please submit a bug report with a copy of '/proc/bus/input/devices'")
        exit()


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button1 = handycon.button_map["button1"]  # Default Screenshot
    button2 = handycon.button_map["button2"]  # Default QAM
    button3 = handycon.button_map["button3"]  # Default ESC 
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE
    button6 = handycon.button_map["button6"] 
    button7 = handycon.button_map["button7"] 
    button8 = handycon.button_map["button8"] 
    button9 = handycon.button_map["button9"] 
    button10 = handycon.button_map["button10"] 
    button11 = handycon.button_map["button11"] 
    button12 = handycon.button_map["button12"] 

    ## Loop variables
    button_on = seed_event.value
    this_button = None

    # Handle missed keys. 
    if active_keys == [] and handycon.event_queue != []:
        this_button = handycon.event_queue[0]

    # BUTTON 1 (Default: Screenshot) Paddle + Y
    if active_keys == [184] and button_on == 1 and button1 not in handycon.event_queue:
        handycon.event_queue.append(button1)
    elif active_keys == [] and seed_event.code in [184, 185] and button_on == 0 and button1 in handycon.event_queue:
        this_button = button1

    # BUTTON 2 (Default: QAM) Armory Crate Button Short Press
    if active_keys == [148] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
    elif active_keys == [] and seed_event.code in [148] and button_on == 0 and button2 in handycon.event_queue:
        this_button = button2

    # BUTTON 3 (Default: ESC) Paddle + X Temp disabled, goes nuts.
    # This event triggers from KEYBOARD_2.
    if active_keys == [25, 125] and button_on == 1 and button3 not in handycon.event_queue:
        handycon.event_queue.append(button3)
    elif active_keys == [] and seed_event.code in [49, 125, 185] and button_on == 0 and button3 in handycon.event_queue:
        this_button = button3

    # BUTTON 4 (Default: OSK) Paddle + D-Pad UP
    if active_keys == [88] and button_on == 1 and button4 not in handycon.event_queue:
        handycon.event_queue.append(button4)
    elif active_keys == [] and seed_event.code in [88, 185] and button_on == 0 and button4 in handycon.event_queue:
        this_button = button4

    # BUTTON 5 (Default: Mode) Control Center Short Press.
    if active_keys == [186] and button_on == 1 and button5 not in handycon.event_queue:
        handycon.event_queue.append(button5)
    elif active_keys == [] and seed_event.code in [186] and button_on == 0 and button5 in handycon.event_queue:
        this_button = button5

    # BUTTON 6 (Default: Launch Chimera) Paddle + A
    if active_keys == [68] and button_on == 1 and button6 not in handycon.event_queue:
        handycon.event_queue.append(button6)
    elif active_keys == [] and seed_event.code in [68, 185] and button_on == 0 and button6 in handycon.event_queue:
        this_button = button6

    # BUTTON 7 (Default: Toggle Performance) Armory Crate Button Long Press
    # This button triggers immediate down/up after holding for ~1s an F17 and then
    # released another down/up for F18 on release. We use the F18 "KEY_UP" for release.
    if active_keys == [187] and button_on == 1 and button7 not in handycon.event_queue:
        handycon.event_queue.append(button7)
        await handycon.do_rumble(0, 150, 1000, 0)
    elif active_keys == [] and seed_event.code in [188] and button_on == 0 and button7 in handycon.event_queue:
        this_button = button7

    # BUTTON 8 (Default: Mode) Control Center Long Press.
    # This event triggers from KEYBOARD_2.
    if active_keys == [29, 56, 111] and button_on == 1 and button8 not in handycon.event_queue:
        handycon.event_queue.append(button8)
        await handycon.do_rumble(0, 150, 1000, 0)
    elif active_keys == [] and seed_event.code in [29, 56, 111] and button_on == 0 and button8 in handycon.event_queue:
        this_button = button8

    # BUTTON 9 (Default: Toggle Mouse) Paddle + D-Pad DOWN
    # This event triggers from KEYBOARD_2.
    if active_keys == [1, 29, 42] and button_on == 1 and button9 not in handycon.event_queue:
        handycon.event_queue.append(button9)
    elif active_keys == [] and seed_event.code in [1, 29, 42, 185] and button_on == 0 and button9 in handycon.event_queue:
        this_button = button9

    # BUTTON 10 (Default: ALT+TAB) Paddle + D-Pad LEFT
    # This event triggers from KEYBOARD_2.
    if active_keys == [32, 125] and button_on == 1 and button10 not in handycon.event_queue:
        handycon.event_queue.append(button10)
    elif active_keys == [] and seed_event.code in [32, 125, 185] and button_on == 0 and button10 in handycon.event_queue:
        this_button = button10

    # BUTTON 11 (Default: KILL) Paddle + D-Pad RIGHT
    # This event triggers from KEYBOARD_2.
    if active_keys == [15, 125] and button_on == 1 and button11 not in handycon.event_queue:
        handycon.event_queue.append(button11)
    elif active_keys == [] and seed_event.code in [15, 125, 185] and button_on == 0 and button11 in handycon.event_queue:
        this_button = button11

    # BUTTON 12 (Default: Toggle Gyro) Paddle + B
    # This event triggers from KEYBOARD_2.
    if active_keys == [49, 125] and button_on == 1 and button12 not in handycon.event_queue:
        handycon.event_queue.append(button12)
    elif active_keys == [] and seed_event.code in [25, 125, 185] and button_on == 0 and button12 in handycon.event_queue:
        this_button = button12

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not handycon.last_button:
        handycon.event_queue.remove(this_button)
        handycon.last_button = this_button
        await handycon.emit_now(seed_event, this_button, 1)

    # Clean up old button presses.
    elif handycon.last_button and not this_button:
        await handycon.emit_now(seed_event, handycon.last_button, 0)
        handycon.last_button = None
