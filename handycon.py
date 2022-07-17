#!/sbin/python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

import asyncio
import os
import signal
import sys
import dbus
import subprocess

from evdev import InputDevice, InputEvent, UInput, ecodes as e, categorize, list_devices, RelEvent
from pathlib import PurePath as p
from shutil import move
from time import sleep

# Declare global variables

# Constants
# EVENTS
EVENT_OSK = [[e.EV_KEY, e.BTN_MODE], [e.EV_KEY, e.BTN_NORTH]]
EVENT_ESC = [[e.EV_MSC, e.MSC_SCAN], [e.EV_KEY, e.KEY_ESC]]
EVENT_QAM = [[e.EV_KEY, e.BTN_MODE], [e.EV_KEY, e.BTN_SOUTH]]
EVENT_SCR = [[e.EV_KEY, e.BTN_MODE], [e.EV_KEY, e.BTN_TR]]
EVENT_HOME = [[e.EV_KEY, e.BTN_MODE]]

# CONTROLLERS
CONTROLLER_NAME_LIST = [
        'Microsoft X-Box 360 pad',
        'Generic X-Box pad',
        ]
CONTROLLER_ADDRESS_LIST = [
        'usb-0000:00:14.0-9/input0',
        'usb-0000:02:00.3-5/input0'
        'usb-0000:03:00.3-4/input0',
        ]

#KEYBOARDS
KEYBOARD_NAME_LIST = [
        'AT Translated Set 2 keyboard',
        ]
KEYBOARD_ADDRESS_LIST = [
        'isa0060/serio0/input0',
        ]

# Track button on/off (prevents spam presses)
event_queue = [] # Stores incoming button presses to block spam

# Devices
controller_device = None
keyboard_device = None
new_device = None
system_type = None

# Paths
controller_event = None
controller_path = None
hide_path = "/dev/input/.hidden/"
keyboard_event = None
keyboard_path = None

# Configuration
button_map = {
        "button1": EVENT_SCR,
        "button2": EVENT_QAM,
        "button3": EVENT_ESC,
        "button4": EVENT_OSK,
        "button5": EVENT_HOME,
        }

def __init__():

    global keyboard_event
    global keyboard_path
    global keyboard_device
    global new_device
    global system_type
    global controller_device
    global controller_event
    global controller_path

    controller_capabilities = None

    # Identify the current device type. Kill script if not compatible.
    system_id = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
    system_cpu = subprocess.check_output("lscpu | grep \"Vendor ID\" | cut -d : -f 2 | xargs", shell=True, universal_newlines=True).strip()

    # Aya Neo from Founders edition through 2021 Pro Retro Power use the same 
    # input hardware and keycodes.
    if system_id in [
            "AYA NEO FOUNDER",
            "AYA NEO 2021",
            "AYANEO 2021",
            "AYANEO 2021 Pro",
            "AYANEO 2021 Pro Retro Power",
            ]:
        system_type = "AYA_GEN1"

    # Aya Neo NEXT and after use new keycodes and have fewer buttons.
    elif system_id in [
            "NEXT",
            "NEXT Pro",
            "NEXT Advance",
            "AYANEO NEXT",
            "AYANEO NEXT Pro",
            "AYANEO NEXT Advance",
            "AIR",
            "AIR Pro",
            ]:
        system_type = "AYA_GEN2"

    # ONE XPLAYER devices have incomplete DMI data so we need addtional information.
    #TODO: FInd better data to ID systems as there may be some differences in buttons.
    elif system_id in [
            "ONE XPLAYER",
            ]:
            
            system_type = "OXP"

    elif system_id in [
            "Win600"
            ]:
            system_type = "WIN600"

    # Block devices that aren't supported as this could cause issues.
    else:
        print(system_id, "is not currently supported by this tool. Open an issue on \
GitHub at https://github.com/ShadowBlip/aya-neo-fixes if this is a bug. If possible, \
please run the capture-system.py utility found on the GitHub repository and upload \
that file with your issue.")
        exit(1)

    # Identify system input event devices.
    attempts = 0
    while attempts < 3:
        try:
            devices_original = [InputDevice(path) for path in list_devices()]
        # Some funky stuff happens sometimes when booting. Give it another shot.
        except OSError:
            attempts += 1
            sleep(1)
            continue

        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in devices_original:

            # Xbox 360 Controller
            if device.name in CONTROLLER_NAME_LIST and device.phys in CONTROLLER_ADDRESS_LIST:
                controller_path = device.path
                controller_device = InputDevice(controller_path)
                controller_capabilities = controller_device.capabilities()
                controller_device.grab()

            # Keyboard Device
            elif device.name in KEYBOARD_NAME_LIST and device.phys in KEYBOARD_ADDRESS_LIST:
                keyboard_path = device.path
                keyboard_device = InputDevice(keyboard_path)
                keyboard_device.grab()

        # Sometimes the service loads before all input devices have full initialized. Try a few times.
        if not controller_path or not keyboard_path:
            attempts += 1
            sleep(1)
        else:
            break

    # Catch if devices weren't found.
    if not controller_device or not keyboard_device:
        print("Keyboard and/or X-Box 360 controller not found.\n \
If this service has previously been started, try rebooting.\n \
Exiting...")
        exit(1)

    # Create the virtual controller.
    new_device = UInput.from_device(
            controller_device,
            keyboard_device,
            name='Handheld Controller',
            bustype=3,
            vendor=int('045e', base=16),
            product=int('028e', base=16),
            version=110)

    # Move the reference to the original controllers to hide them from the user/steam.
    os.makedirs(hide_path, exist_ok=True)
    keyboard_event = p(keyboard_path).name
    move(keyboard_path, hide_path+keyboard_event)
    controller_event = p(controller_path).name
    move(controller_path, hide_path+controller_event)


# Captures keyboard events and translates them to virtual device events.
async def capture_keyboard_events(device):

    # Get access to global variables. These are globalized because the function
    # is instanciated twice and need to persist accross both instances.
    global event_queue
    global button_map

    # Button map shortcuts for easy reference.
    button1 = button_map["button1"]
    button2 = button_map["button2"]
    button3 = button_map["button3"]
    button4 = button_map["button4"]
    button5 = button_map["button5"]
    last_button = None

    # Capture events for the given device.
    async for seed_event in device.async_read_loop():

        # Loop variables
        active = device.active_keys()
        events = []
        this_button = None
        button_on = seed_event.value
        
        # Debugging variables
        #if active != []:
        #   print("Active Keys:", device.active_keys(verbose=True), "Seed Value", seed_event.value, "Seed Code:", seed_event.code, "Seed Type:", seed_event.type, "Button pressed", button_on)

        # Automatically pass default keycodes we dont intend to replace.
        if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
            events.append(seed_event)
        match system_type:

            case "AYA_GEN1":
                # BUTTON 1 (Default: Screenshot) WIN button
                if active == [125] and button_on == 1 and button1 not in event_queue:
                    event_queue.append(button1)
                elif active == [] and seed_event.code == 125 and button_on == 0 and button1 in event_queue:
                    this_button = button1

                # BUTTON 2 (Default: QAM) TM Button
                if active == [97, 100, 111] and button_on == 1 and button2 not in event_queue:
                    event_queue.append(button2)
                elif active == [] and seed_event.code in [97, 100, 111] and button_on == 0 and button2 in event_queue:
                    this_button = button2

                # BUTTON 3 (Default: ESC) ESC Button
                if active == [1] and seed_event.code == 1 and button_on == 1 and button3 not in event_queue:
                    event_queue.append(button3)
                elif active == [] and seed_event.code == 1 and button_on == 0 and button3 in event_queue:
                    this_button = button3

                # BUTTON 3 SECOND STATE (Default: TBD) Long hold ESC Reserved for Gyro enable
                #elif seed_event.code == 1 and button_on == 2 and button3 in event_queue:
                #    this_button = button4
                #    event_queue.remove(button3)
                #    event_queue.append(button4)

                # BUTTON 4 (Default: OSK) KB Button
                if active == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
                    event_queue.append(button4)
                elif active == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
                    this_button = button4

            case "AYA_GEN2":
                # BUTTON 2 (Default: QAM) Small button
                if active in [[40, 133], [32, 125]] and button_on == 1 and button2 not in event_queue:
                    event_queue.append(button2)
                elif active == [] and seed_event.code in [32, 40, 125, 133] and button_on == 0 and button2 in event_queue:
                    this_button = button2

                # BUTTON 5 (Default: Home) Big button
                if active in [[96, 105, 133], [88, 97, 125]] and button_on == 1 and button5 not in event_queue:
                    event_queue.append(button5)
                elif active == [] and seed_event.code in [88, 96, 97, 105, 125, 133] and button_on == 0 and button5 in event_queue:
                    this_button = button5

            case "OXP":
                # BUTTON 1 (Default: Screenshot) Short press orange + |||||
                if active == [99, 125] and button_on == 1 and button1 not in event_queue:
                    event_queue.append(button1)
                elif active == [] and seed_event.code in [99, 125] and button_on == 0 and button1 in event_queue:
                    this_button = button1

                # BUTTON 2 (Default: QAM) Short press orange
                if active == [32, 125] and button_on == 1 and button2 not in event_queue:
                    event_queue.append(button2)
                elif active == [] and seed_event.code in [32, 125] and button_on == 0 and button2 in event_queue:
                    this_button = button2

                # BUTTON 4 (Default: OSK) Short press KB
                if active == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
                    event_queue.append(button4)
                elif active == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
                    this_button = button4

                # BUTTON 5 (Default: Home) Long press orange
                if active == [34, 125] and button_on == 1 and button5 not in event_queue:
                    event_queue.append(button5)
                elif active == [] and seed_event.code in [34, 125] and button_on == 0 and button5 in event_queue:
                    this_button = button5

                # UNUSED [97, 100, 111]  ORANGE + KB Reserved for gyro enable

            case "WIN600":
                # BUTTON 2 (Default: QAM) Windows Key
                if active == [125] and button_on == 1 and button2 not in event_queue:
                    event_queue.append(button2)
                elif active == [] and seed_event.code == 125 and button_on == 0 and button2 in event_queue:
                    this_button = button2

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
            await emit_events(events)


# Captures the controller_device events and passes them through.
async def capture_controller_events(device):
    async for event in device.async_read_loop():
        await emit_events([event])


async def emit_events(events: list):
    if len(events) == 1:
        new_device.write_event(events[0])
        new_device.syn()
    elif len(events) > 1:
        for event in events:
            if event:
                new_device.write_event(event)
                new_device.syn()
                await asyncio.sleep(0.09)


# Gracefull shutdown.
async def restore(loop):

    print('Receved exit signal. Restoring Devices.')

    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(hide_path+keyboard_event, keyboard_path)
    except FileNotFoundError:
        pass
    try:
        move(hide_path+controller_event, controller_path)
    except FileNotFoundError:
        pass

    # Kill all tasks. They are infinite loops so we will wait forver.
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    loop.stop()
    print("Device restore complete. Stopping...")


# Main loop
def main():

    # Run asyncio loop to capture all events.
    loop = asyncio.get_event_loop()
    loop.create_future()

    # Attach the event loop of each device to the asyncio loop.
    asyncio.ensure_future(capture_controller_events(controller_device))
    asyncio.ensure_future(capture_keyboard_events(keyboard_device))

    # Establish signaling to handle gracefull shutdown.
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(restore(loop)))

    try:
        loop.run_forever()
    except Exception as e:
        print("Hit exception condition:\n", e)
    finally:
        loop.stop()

if __name__ == "__main__":
    __init__()
    main()
