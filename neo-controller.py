#!/sbin/python3
# Aya Neo Controller
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

from evdev import InputDevice, InputEvent, UInput, ecodes as e, categorize, list_devices
from pathlib import PurePath as p
from shutil import move
from time import sleep

# Declare global variables
# Supported system type
sys_type = None # 2021 or NEXT supported

# Track button on/off (prevents spam presses)
esc_pressed = False # ESC button (GEN1)
home_pressed = False # Steam/xbox/playsation button (GEN2)
kb_pressed = False # OSK Button (GEN1)
tm_pressed = False # Quick Aciton Menu button (GEN1, GEN2)
win_pressed = False # Dock Button (GEN1)

# Devices
keybd = None
ui = None
xb360 = None

# Paths
hide_path = "/dev/input/.hidden/"
kb_event = None
kb_path = None
xb_event = None
xb_path = None

def __init__():

    global kb_event
    global kb_path
    global keybd
    global sys_type
    global xb360
    global xb_event
    global xb_path
    global ui

    # Identify the current device type. Kill script if not compatible.
    sys_id = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()

    # All devices from Founders edition through 2021 Pro Retro Power use the same 
    # input hardware and keycodes.
    if sys_id in ["AYANEO 2021 Pro Retro Power",
            "AYA NEO 2021 Pro Retro Power",
            "AYANEO 2021 Pro",
            "AYA NEO 2021 Pro",
            "AYANEO 2021",
            "AYA NEO 2021",
            "AYANEO FOUNDERS",
            "AYA NEO FOUNDERS",
            "AYANEO FOUNDER",
            "AYA NEO FOUNDER",
            ]:
        sys_type = "GEN1"

    # NEXT uses new keycodes and has fewer buttons.
    elif sys_id in ["NEXT",
            "Next Pro",
            "AYA NEO NEXT Pro",
            "AYANEO NEXT Pro",
            ]:
        sys_type = "GEN2"

    # Block devices that aren't supported as this could cause issues.
    else:
        print(sys_id, "is not currently supported by this tool. Open an issue on \
GitHub at https://github.com/ShadowBlip/aya-neo-fixes if this is a bug. If possible, \
please run the capture-system.py utility found on the GitHub repository and upload \
that file with your issue.")
        exit(1)

    # Identify system input event devices.
    attempts = 0
    while attempts < 3:
        try:
            devices_orig = [InputDevice(path) for path in list_devices()]
        # Some funky stuff happens sometimes when booting. Give it another shot.
        except OSError:
            attempts += 1
            sleep(1)
            continue

        for device in devices_orig:

            # Xbox 360 Controller
            if device.name == 'Microsoft X-Box 360 pad' and device.phys == 'usb-0000:03:00.3-4/input0':
                xb_path = device.path

            # Keyboard Device
            elif device.name == 'AT Translated Set 2 keyboard' and device.phys == 'isa0060/serio0/input0':
                kb_path = device.path

        # Sometimes the service loads before all input devices have full initialized. Try a few times.
        if not xb_path or not kb_path:
            attempts += 1
            sleep(1)
        else:
            break

    # Catch if devices weren't found.
    if not xb_path or not kb_path:
        print("Keyboard and/or X-Box 360 controller not found.\n \
If this service has previously been started, try rebooting.\n \
Exiting...")
        exit(1)

    # Grab the built-in devices. Prevents double input.
    keybd = InputDevice(kb_path)
    keybd.grab()
    xb360 = InputDevice(xb_path)
    xb360.grab()

    # Create the virtual controller.
    ui = UInput.from_device(xb360, keybd, name='Aya Neo Controller', bustype=3, vendor=int('045e', base=16), product=int('028e', base=16), version=110)

    # Move the reference to the original controllers to hide them from the user/steam.
    os.makedirs(hide_path, exist_ok=True)
    kb_event = p(kb_path).name
    move(kb_path, hide_path+kb_event)
    xb_event = p(xb_path).name
    move(xb_path, hide_path+xb_event)


# Captures physical dvice events and translates them to virtual device events.
async def capture_events(device):

    # Get access to global variables. These are globalized because the funtion
    # is instanciated twice and need to persist accross both instances.
    global esc_pressed
    global home_pressed
    global kb_pressed
    global tm_pressed
    global win_pressed
    global sys_type

    # Capture events for the given device.
    async for event in device.async_read_loop():

        # We use active keys instead of ev1.code as we will override ev1 and
        # we don't want to trigger additional/different events when doing that
        active = device.active_keys()

        ev1 = event # pass through the current event, override if needed
        ev2 = None # optional second button (i.e. home + select or super + p)
        match sys_type:

            case "GEN1": # 2021 Models and previous.
                # TODO: shortcut changes from MODE+SELECT to MODE+NORTH when running
                # export STEAMCMD="steam -gamepadui -steampal -steamos3 -steamdeck"
                # in the user session. We will need to detect this somehow so it works.
                # on any install and session.

                # KB BUTTON. Open OSK. Works in-game in BPM but globally in gamepadui
                if active == [24, 97, 125] and not kb_pressed and ev1.value == 1:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.BTN_MODE, 1)
                    ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.BTN_NORTH, 1)
                    kb_pressed = True
                elif active == [97] and kb_pressed and ev1.value == 0:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.BTN_MODE, 0)
                    ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.BTN_NORTH, 0)
                    kb_pressed = False

                # WIN BUTTON. Map to all detected screens for docking. Not working
                # TODO: Get this working. Tried SUPER+P and SUPER+D.
                # The extra conditions handle pressing WIN while pressing KB since
                # both use code 125. Letting go of KB first still clears win_pressed
                # as key 125 is released at the system level.
                elif not win_pressed and ev1.value in [1,2] and (active == [125] or (active == [24, 97, 125] and kb_pressed)):
                    #ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_LEFTMETA, 1)
                    #ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_D, 1)
                    win_pressed = True
                elif (active in [[], [24, 97]] and win_pressed) or (active == [125] and ev1.code == 125 and win_pressed and ev1.value == 0):
                    #ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_LEFTMETA, 0)
                    #ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_D, 0)
                    win_pressed = False

                # ESC BUTTON. Unused. Passing so it functions as an "ESC" key for now.
                # Add 1 to below list if changed.
                elif ev1.code == 1 and not esc_pressed and ev1.value == 1:
                    esc_pressed = True
                elif ev1.code == 1 and esc_pressed and ev1.value == 0:
                    esc_pressed = False

                # TM BUTTON. Quick Action Menu
                elif active == [97, 100, 111] and not tm_pressed and ev1.value == 1:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_LEFTCTRL, 1)
                    ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_2, 1)
                    tm_pressed = True
                elif ev1.code in [97, 100, 111] and tm_pressed and ev1.value == 0:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_LEFTCTRL, 0)
                    ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_2, 0)
                    tm_pressed = False

            case "GEN2": # NEXT Model and beyond.
                # AYA SPACE BUTTON. -> Home Button
                if active in [[96, 105, 133], [97, 125, 88], [88, 97, 125]] and not home_pressed and ev1.value == 1:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.BTN_MODE, 1)
                    home_pressed = True
                elif ev1.code in [88, 96, 97, 105, 133] and home_pressed and ev1.value == 0:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.BTN_MODE, 0)
                    home_pressed = False

                # CONFIGURABLE BUTTON. -> Quick Action Menu.
                # NOTE: Some NEXT models use SUPER+D, Aya may be trying to use this as fullscreen docking.
                # TODO: Investigate if configuring in AYA SPACE changes these keycodes in firmware.
                elif active in [[40, 133], [32, 125]] and not tm_pressed and ev1.value == 1:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_LEFTCTRL, 1)
                    ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_2, 1)
                    tm_pressed = True
                elif ev1.code in [40, 133, 32] and tm_pressed and ev1.value == 0:
                    ev1 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_LEFTCTRL, 0)
                    ev2 = InputEvent(event.sec, event.usec, e.EV_KEY, e.KEY_2, 0)
                    tm_pressed = False

        # Kill events that we override. Keeps output clean.
        if ev1.code in [4, 24, 32, 40, 88, 96, 97, 100, 105, 111, 133] and ev1.type in [e.EV_MSC, e.EV_KEY]:
            continue # Add 1 to list if ESC used above
        elif ev1.code in [125] and ev2 == None: # Only kill KEY_LEFTMETA if its not used as a key combo.
            continue

        # Push out all events. Includes all button/joy events from controller we dont override.
        ui.write_event(ev1)
        if ev2:
            ui.write_event(ev2)
        ui.syn()


# Gracefull shutdown.
async def restore(signal, loop):

    print('Receved exit signal: '+signal.name+'. Restoring Devices.')

    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(hide_path+kb_event, kb_path)
    except FileNotFoundError:
        pass
    try:
        move(hide_path+xb_event, xb_path)
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
    # TODO: these are deprecated, research and ID new functions.
    # NOTE: asyncio api will need update to fix. Maybe supress error for clean logs?
    for device in xb360, keybd:
        asyncio.ensure_future(capture_events(device))

    loop = asyncio.get_event_loop()

    # Establish signaling to handle gracefull shutdown.
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(restore(s, loop)))

    try:
        loop.run_forever()
    finally:
        loop.close()


if __name__ == "__main__":
    __init__()
    main()
