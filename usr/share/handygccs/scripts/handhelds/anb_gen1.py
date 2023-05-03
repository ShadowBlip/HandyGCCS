#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

import asyncio
import sys
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff

sys.path.append("../common")
import common as com

sys.path.append("../constants")
import constants as cons

event_queue = [] # Stores incoming button presses to block spam

# Constants
def init_handheld():
    com.BUTTON_DELAY = 0.04
    com.CAPTURE_CONTROLLER = True
    com.CAPTURE_KEYBOARD = True
    com.CAPTURE_POWER = True
    com.GAMEPAD_ADDRESS = 'usb-0000:02:00.3-5/input0'
    com.GAMEPAD_NAME = 'Microsoft X-Box 360 pad'
    com.KEYBOARD_ADDRESS = 'isa0060/serio0/input0'
    com.KEYBOARD_NAME = 'AT Translated Set 2 keyboard'

# Captures keyboard events and translates them to virtual device events.
async def capture_keyboard_events():
    # Get access to global variables. These are globalized because the function
    # is instanciated twice and need to persist accross both instances.
    global last_button

    last_button = None
    # Capture keyboard events and translate them to mapped events.
    while com.running:
        if com.keyboard_device:
            try:
                async for seed_event in com.keyboard_device.async_read_loop():
                    if seed_event.type != e.EV_KEY:
                        continue
                    # Loop variables
                    active_keys = com.keyboard_device.active_keys()
                    button_on = seed_event.value

                    # Debugging variables
                    if active_keys != []:
                        cons.logger.debug(f"Active Keys: {active_keys}, Seed Value: {seed_event.value}, Seed Code: {seed_event.code}, Seed Type: {seed_event.type}.")
                        cons.logger.debug(f"Queued events: {event_queue}")
                    elif active_keys == [] and event_queue != []:
                        cons.logger.debug(f"Seed Value: {seed_event.value}, Seed Code: {seed_event.code}, Seed Type: {seed_event.type}.")
                        cons.logger.debug(f"Queued events: {event_queue}")
                    
                    await process_event(seed_event, active_keys)

            except Exception as err:
                cons.logger.error(f"{err} | Error reading events from {keyboard_device.name}")
                com.restore_keyboard()
                com.keyboard_device = None
                com.keyboard_event = None
                com.keyboard_path = None
        else:
            cons.logger.info("Attempting to grab keyboard device...")
            com.get_keyboard()
            await asyncio.sleep(cons.DETECT_DELAY)

# Captures keyboard events and translates them to virtual device events.
async def process_event(seed_event, active_keys):
    global last_button
    global event_queue

    # Button map shortcuts for easy reference.
    button1 = com.button_map["button1"]  # Default Screenshot
    button2 = com.button_map["button2"]  # Default QAM
    button3 = com.button_map["button3"]  # Default ESC
    button4 = com.button_map["button4"]  # Default OSK
    button5 = com.button_map["button5"]  # Default MODE
    button6 = ["RyzenAdj Toggle"]
    button7 = ["Open Chimera"]

    ## Loop variables
    events = []
    this_button = None
    button_on = seed_event.value

    # Automatically pass default keycodes we dont intend to replace.
    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
        events.append(seed_event)

    # BUTTON 1 (BUTTON 4 ALT Mode) (Default: Screenshot) Long press KB
    if active == [24, 29, 125] and button_on == 2 and button1 not in event_queue:
        if button4 in event_queue:
            event_queue.remove(button4)
        if button5 in event_queue:
            event_queue.remove(button5)
        event_queue.append(button1)
    elif active == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button1 in event_queue:
        this_button = button1

    # BUTTON 2 (Default: QAM) Home key.
    if active == [34, 125] and button_on == 1 and button2 not in event_queue:
        if button5 in event_queue:
            event_queue.remove(button5)
        event_queue.append(button2)
    elif active == [] and seed_event.code in [34, 125] and button_on == 0 and button2 in event_queue:
        this_button = button2

    # BUTTON 3, BUTTON 2 ALt mode (Defalt ESC)
    elif active == [1] and button_on == 1 and button3 not in event_queue:
        if button2 in event_queue:
            event_queue.remove(button2)
        event_queue.append(button3)
        await com.do_rumble(0, 75, 1000, 0)
    elif active == [] and seed_event.code == 1 and button_on == 0 and button3 in event_queue:
        this_button = button3

    # BUTTON 4 (Default: OSK) Short press KB
    if active == [24, 29, 125] and button_on == 1 and button4 not in event_queue:
        if button5 in event_queue:
            event_queue.remove(button5)
        event_queue.append(button4)
    elif active == [] and seed_event.code in [24, 29, 125] and button_on == 0 and button4 in event_queue:
        this_button = button4

    # BUTTON 5 (Default: GUIDE) Meta/Windows key.
    if active == [125] and button_on == 1 and button5 not in event_queue:
        event_queue.append(button5)
    elif active == [] and seed_event.code == 125 and button_on == 0 and button5 in event_queue:
        this_button = button5

    # BUTTON 5 ALT mode, toggle performance_mode
    if active == [1, 29, 42] and button_on == 1 and button6 not in event_queue:
        if button5 in event_queue:
            event_queue.remove(button5)
        event_queue.append(button6)
        await com.toggle_performance()

    elif active == [] and seed_event in [1, 29, 42] and button_on == 0 and button6 in event_queue:
        event_queue.remove(button6)
    

    # Handle L_META from power button
    elif active_keys == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and com.shutdown == True:
        com.shutdown = False

    # Create list of events to fire.
    # Handle new button presses.
    if this_button and not last_button:
        for button_event in this_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 1)
            events.append(event)
        event_queue.remove(this_button)
        last_button = this_button

    # Clean up old button presses.
    elif last_button and not this_button:
        for button_event in last_button:
            event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], 0)
            events.append(event)
        last_button = None

    # Push out all events.
    if events != []:
        await com.emit_events(events)
