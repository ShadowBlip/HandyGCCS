#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

from time import sleep

handycon = None


def init_handheld(handheld_controller):
    global handycon
    devices = []
    proc_dev_fd = open("/proc/bus/input/devices", "r")
    for line in proc_dev_fd:
        devices.append(line)
    proc_dev_fd.close()

    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.2
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_NAME = "Microsoft X-Box 360 pad"
    handycon.KEYBOARD_NAME = "Asus Keyboard"
    handycon.KEYBOARD_2_NAME = "Asus Keyboard"
    GAMEPAD_ADDRESS_LIST = [
        "usb-0000:08:00.3-2/input0",
        "usb-0000:09:00.3-2/input0",
        "usb-0000:0a:00.3-2/input0",
    ]
    KEYBOARD_ADDRESS_LIST = [
        "usb-0000:08:00.3-3/input0",
        "usb-0000:09:00.3-3/input0",
        "usb-0000:0a:00.3-3/input0",
    ]
    KEYBOARD_2_ADDRESS_LIST = [
        "usb-0000:08:00.3-3/input2",
        "usb-0000:09:00.3-3/input2",
        "usb-0000:0a:00.3-3/input2",
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

    if (
        not handycon.GAMEPAD_ADDRESS
        or not handycon.KEYBOARD_ADDRESS
        or not handycon.KEYBOARD_2_ADDRESS
    ):
        handycon.logger.warn(
            "Unable to identify one or more input devices by address. Please submit a bug report with a copy of '/proc/bus/input/devices'"
        )
        exit()

    # asus_hid needs tiem to initialize and set the gamepad mode or everything breaks. Wait for 10s to let that happen.
    sleep(10)


# Captures keyboard events and translates them to virtual device events.


async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button2 = handycon.button_map["button2"]  # Default: QAM
    button4 = handycon.button_map["button4"]  # Default: OSK
    button5 = handycon.button_map["button5"]  # Default: BTN_MODE
    button7 = handycon.button_map["button7"]  # Default: Toggle Performance
    button8 = handycon.button_map["button8"]  # Default: BTN_THUMBL
    button9 = handycon.button_map["button9"]  # Default: BTN_THUMBR

    # Loop variables
    button_on = seed_event.value
    this_button = None

    # Handle missed keys.
    if active_keys == [] and handycon.event_queue != []:
        this_button = handycon.event_queue[0]

    # BUTTON 2 (Default: QAM) Armory Crate Button Short Press
    if active_keys == [148] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
    elif (
        active_keys == []
        and seed_event.code in [148]
        and button_on == 0
        and button2 in handycon.event_queue
    ):
        this_button = button2

    # BUTTON 4 (Default: OSK) Control Center Long Press.
    if (
        active_keys == [29, 56, 111]
        and button_on == 1
        and button4 not in handycon.event_queue
    ):
        handycon.event_queue.append(button4)
        await handycon.do_rumble(0, 150, 1000, 0)
    elif (
        active_keys == []
        and seed_event.code in [29, 56, 111]
        and button_on == 0
        and button4 in handycon.event_queue
    ):
        this_button = button4

    # BUTTON 5 (Default: Mode) Control Center Short Press.
    if active_keys == [186] and button_on == 1 and button5 not in handycon.event_queue:
        handycon.event_queue.append(button5)
    elif (
        active_keys == []
        and seed_event.code in [186]
        and button_on == 0
        and button5 in handycon.event_queue
    ):
        this_button = button5

    # BUTTON 7 (Default: Toggle Performance) Armory Crate Button Long Press
    # This button triggers immediate down/up after holding for ~1s an F17 and then
    # released another down/up for F18 on release. We use the F18 "KEY_UP" for release.
    if active_keys == [187] and button_on == 1 and button7 not in handycon.event_queue:
        await handycon.do_rumble(0, 150, 1000, 0)
        await handycon.handle_key_down(seed_event, button7)
    elif (
        active_keys == []
        and seed_event.code in [188]
        and button_on == 0
        and button7 in handycon.event_queue
    ):
        await handycon.handle_key_up(seed_event, button7)

    # BUTTON 11 (Default: Happy Trigger 1) Left Paddle
    if active_keys == [184] and button_on == 1 and button8 not in handycon.event_queue:
        await handycon.handle_key_down(seed_event, button8)
    elif (
        active_keys == []
        and seed_event.code in [184]
        and button_on == 0
        and button8 in handycon.event_queue
    ):
        await handycon.handle_key_up(seed_event, button8)

    # BUTTON 4 (Default: Happy Trigger 2) Right Paddle
    if active_keys == [185] and button_on == 1 and button9 not in handycon.event_queue:
        await handycon.handle_key_down(seed_event, button9)
    elif (
        active_keys == []
        and seed_event.code in [185]
        and button_on == 0
        and button9 in handycon.event_queue
    ):
        await handycon.handle_key_up(seed_event, button9)

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
