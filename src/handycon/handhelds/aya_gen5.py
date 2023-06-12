#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

import sys
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff

from .. import constants as cons

handycon = None

def init_handheld(handheld_controller):
    global handycon
    handycon = handheld_controller
    handycon.BUTTON_DELAY = 0.09
    handycon.CAPTURE_CONTROLLER = True
    handycon.CAPTURE_KEYBOARD = True
    handycon.CAPTURE_POWER = True
    handycon.GAMEPAD_ADDRESS = 'usb-0000:64:00.3-3/input0'
    handycon.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    #handycon.GYRO_I2C_ADDR = 0x68
    #handycon.GYRO_I2C_BUS = 1
    handycon.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    handycon.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'


# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global handycon

    # Button map shortcuts for easy reference.
    button1 = handycon.button_map["button1"]  # Default Screenshot
    button2 = handycon.button_map["button2"]  # Default QAM
    button3 = handycon.button_map["button3"]  # Default ESC
    button4 = handycon.button_map["button4"]  # Default OSK
    button5 = handycon.button_map["button5"]  # Default MODE
    button6 = ["RyzenAdj Toggle"]
    button7 = ["Open Chimera"]

    ## Loop variables
    events = []
    this_button = None
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        events.append(seed_event)
    # This device class uses the same active_keys events with different values for AYA SPACE, LC, and RC.
    if active_keys == [29, 125] or active_keys == [97, 125]:

        # LC | Default: Screenshot / Launch Chimera
        if button_on == 102 and handycon.event_queue == []:
            if handycon.HAS_CHIMERA_LAUNCHER:
                handycon.event_queue.append(button7)
            else:
                handycon.event_queue.append(button1)
                await handycon.emit_now(seed_event, button1, 1)
        # RC | Default: OSK
        elif button_on == 103 and handycon.event_queue == []:
            handycon.event_queue.append(button4)
            await handycon.emit_now(seed_event, button4, 1)
        # AYA Space | Default: MODE
        elif button_on == 104 and handycon.event_queue == []:
            handycon.event_queue.append(button5)
            await handycon.emit_now(seed_event, button5, 1)

    elif active_keys == [] and seed_event.code in [97, 125] and button_on == 0 and handycon.event_queue != []:
        if button7 in handycon.event_queue:
            handycon.event_queue.remove(button7)
            handycon.launch_chimera()
        if button1 in handycon.event_queue:
            handycon.event_queue.remove(button1)
            await handycon.emit_now(seed_event, button1, 0)
        if button4 in handycon.event_queue:
            handycon.event_queue.remove(button4)
            await handycon.emit_now(seed_event, button4, 0)
        if button5 in handycon.event_queue:
            handycon.event_queue.remove(button5)
            await handycon.emit_now(seed_event, button5, 0)

    # Small button | Default: QAM
    if active_keys == [32, 125] and button_on == 1 and button2 not in handycon.event_queue:
        handycon.event_queue.append(button2)
        await handycon.emit_now(seed_event, button2, 1)
    elif active_keys == [] and seed_event.code in [32, 125] and button_on == 0 and button2 in handycon.event_queue:
        handycon.event_queue.remove(button2)
        await handycon.emit_now(seed_event, button2, 0)

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and handycon.event_queue == [] and handycon.shutdown == True:
        handycon.shutdown = False

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not handycon.last_button:
        for button_event in this_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 1)
            events.append(event)
        handycon.event_queue.remove(this_button)
        handycon.last_button = this_button

    # Clean up old button presses.
    elif handycon.last_button and not this_button:
        for button_event in handycon.last_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 0)
            events.append(event)
        handycon.last_button = None

    # Push out all events.
    if events != []:
        await handycon.emit_events(events)
