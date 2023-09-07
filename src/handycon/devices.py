#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

## Python Modules
import asyncio
import os
import traceback

# Local modules
import handycon.handhelds.ally_gen1 as ally_gen1
import handycon.handhelds.anb_gen1 as anb_gen1
import handycon.handhelds.aok_gen1 as aok_gen1
import handycon.handhelds.aok_gen2 as aok_gen2
import handycon.handhelds.aya_gen1 as aya_gen1
import handycon.handhelds.aya_gen2 as aya_gen2
import handycon.handhelds.aya_gen3 as aya_gen3
import handycon.handhelds.aya_gen4 as aya_gen4
import handycon.handhelds.aya_gen5 as aya_gen5
import handycon.handhelds.aya_gen6 as aya_gen6
import handycon.handhelds.aya_gen7 as aya_gen7
import handycon.handhelds.ayn_gen1 as ayn_gen1
import handycon.handhelds.ayn_gen2 as ayn_gen2
import handycon.handhelds.gpd_gen1 as gpd_gen1
import handycon.handhelds.gpd_gen2 as gpd_gen2
import handycon.handhelds.gpd_gen3 as gpd_gen3
import handycon.handhelds.oxp_gen1 as oxp_gen1
import handycon.handhelds.oxp_gen2 as oxp_gen2
import handycon.handhelds.oxp_gen3 as oxp_gen3
import handycon.handhelds.oxp_gen4 as oxp_gen4
from .constants import *

## Partial imports
from evdev import ecodes as e, ff, InputDevice, InputEvent, list_devices, UInput
from pathlib import Path
from shutil import move
from time import sleep

handycon = None

def set_handycon(handheld_controller):
    global handycon
    handycon = handheld_controller


def get_controller():
    global handycon

    # Identify system input event devices.
    handycon.logger.debug(f"Attempting to grab {handycon.GAMEPAD_NAME}.")
    try:
        devices_original = [InputDevice(path) for path in list_devices()]

    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
        handycon.logger.error(traceback.format_exc())
        sleep(DETECT_DELAY)
        return False

    # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
    for device in devices_original:
        if device.name == handycon.GAMEPAD_NAME and device.phys == handycon.GAMEPAD_ADDRESS:
            handycon.controller_path = device.path
            handycon.controller_device = InputDevice(handycon.controller_path)
            if handycon.CAPTURE_CONTROLLER:
                handycon.controller_device.grab()
                handycon.controller_event = Path(handycon.controller_path).name
                move(handycon.controller_path, str(HIDE_PATH / handycon.controller_event))
            break

    # Sometimes the service loads before all input devices have full initialized. Try a few times.
    if not handycon.controller_device:
        handycon.logger.warn("Controller device not yet found. Restarting scan.")
        sleep(DETECT_DELAY)
        return False
    else:
        handycon.logger.info(f"Found {handycon.controller_device.name}. Capturing input data.")
        return True


def get_keyboard():
    global handycon

    # Identify system input event devices.
    handycon.logger.debug(f"Attempting to grab {handycon.KEYBOARD_NAME}.")
    try:
        devices_original = [InputDevice(path) for path in list_devices()]
    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
        handycon.logger.error(traceback.format_exc())
        sleep(DETECT_DELAY)
        return False
    # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
    for device in devices_original:
        handycon.logger.debug(f"{device.name}, {device.phys}")
        if device.name == handycon.KEYBOARD_NAME and device.phys == handycon.KEYBOARD_ADDRESS:
            handycon.keyboard_path = device.path
            handycon.keyboard_device = InputDevice(handycon.keyboard_path)
            if handycon.CAPTURE_KEYBOARD:
                handycon.keyboard_device.grab()
                handycon.keyboard_event = Path(handycon.keyboard_path).name
                move(handycon.keyboard_path, str(HIDE_PATH / handycon.keyboard_event))
            break

    # Sometimes the service loads before all input devices have full initialized. Try a few times.
    if not handycon.keyboard_device:
        handycon.logger.warn("Keyboard device not yet found. Restarting scan.")
        sleep(DETECT_DELAY)
        return False
    else:
        handycon.logger.info(f"Found {handycon.keyboard_device.name}. Capturing input data.")
        return True


def get_keyboard_2():
    global handycon

    handycon.logger.debug(f"Attempting to grab {handycon.KEYBOARD_2_NAME}.")
    try:
        devices_original = [InputDevice(path) for path in list_devices()]
    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
        handycon.logger.error(traceback.format_exc())
        sleep(DETECT_DELAY)
        return False

    # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
    for device in devices_original:
        handycon.logger.debug(f"{device.name}, {device.phys}")
        if device.name == handycon.KEYBOARD_2_NAME and device.phys == handycon.KEYBOARD_2_ADDRESS:
            handycon.keyboard_2_path = device.path
            handycon.keyboard_2_device = InputDevice(handycon.keyboard_2_path)
            if handycon.CAPTURE_KEYBOARD:
                handycon.keyboard_2_device.grab()
                handycon.keyboard_2_event = Path(handycon.keyboard_2_path).name
                move(handycon.keyboard_2_path, str(HIDE_PATH / handycon.keyboard_2_event))
            break

    # Sometimes the service loads before all input devices have full initialized. Try a few times.
    if not handycon.keyboard_2_device:
        handycon.logger.warn("Keyboard device 2 not yet found. Restarting scan.")
        sleep(DETECT_DELAY)
        return False
    else:
        handycon.logger.info(f"Found {handycon.keyboard_2_device.name}. Capturing input data.")
        return True


def get_powerkey():
    global handycon

    handycon.logger.debug(f"Attempting to grab power buttons.")
    # Identify system input event devices.
    try:
        devices_original = [InputDevice(path) for path in list_devices()]
    # Some funky stuff happens sometimes when booting. Give it another shot.
    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
        handycon.logger.error(traceback.format_exc())
        sleep(DETECT_DELAY)
        return False

    # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
    for device in devices_original:

        # Power Button
        if device.name == 'Power Button' and device.phys == handycon.POWER_BUTTON_PRIMARY and not handycon.power_device:
            handycon.power_device = device
            handycon.logger.debug(f"found power device {handycon.power_device.phys}")
            if handycon.CAPTURE_POWER:
                handycon.power_device.grab()

        # Some devices have an extra power input device corresponding to the same
        # physical button that needs to be grabbed.
        if device.name == 'Power Button' and device.phys == handycon.POWER_BUTTON_SECONDARY and not handycon.power_device_2:
            handycon.power_device_2 = device
            handycon.logger.debug(f"found alternate power device {handycon.power_device_2.phys}")
            if handycon.CAPTURE_POWER:
                handycon.power_device_2.grab()

    if not handycon.power_device and not handycon.power_device_2:
        handycon.logger.warn("No Power Button found. Restarting scan.")
        sleep(DETECT_DELAY)
        return False
    else:
        if handycon.power_device:
            handycon.logger.info(f"Found {handycon.power_device.name}. Capturing input data.")
        if handycon.power_device_2:
            handycon.logger.info(f"Found {handycon.power_device_2.name}. Capturing input data.")
        return True


async def do_rumble(button=0, interval=10, length=1000, delay=0):
    global handycon

    # Prevent look crash if controller_device was taken.
    if not handycon.controller_device:
        return

    # Create the rumble effect.
    rumble = ff.Rumble(strong_magnitude=0x0000, weak_magnitude=0xffff)
    effect = ff.Effect(
        e.FF_RUMBLE,
        -1,
        0,
        ff.Trigger(button, interval),
        ff.Replay(length, delay),
        ff.EffectType(ff_rumble_effect=rumble)
    )

    # Upload and transmit the effect.
    effect_id = handycon.controller_device.upload_effect(effect)
    handycon.controller_device.write(e.EV_FF, effect_id, 1)
    await asyncio.sleep(interval / 1000)
    handycon.controller_device.erase_effect(effect_id)


# Captures keyboard events and translates them to virtual device events.
async def capture_keyboard_events():
    global handycon

    # Capture keyboard events and translate them to mapped events.
    while handycon.running:
        if handycon.keyboard_device:
            try:
                async for seed_event in handycon.keyboard_device.async_read_loop():
                    # Loop variables
                    active_keys = handycon.keyboard_device.active_keys()

                    # Debugging variables
                    handycon.logger.debug(f"Seed Value: {seed_event.value}, Seed Code: {seed_event.code}, Seed Type: {seed_event.type}.")
                    if active_keys != []:
                        handycon.logger.debug(f"Active Keys: {active_keys}")
                    else:
                        handycon.logger.debug("No active keys")
                    if handycon.event_queue != []:
                        handycon.logger.debug(f"Queued events: {handycon.event_queue}")
                    else:
                        handycon.logger.debug("No active events.")

                    # Capture keyboard events and translate them to mapped events.
                    match handycon.system_type:
                        case "ALY_GEN1":
                            await ally_gen1.process_event(seed_event, active_keys)
                        case "ANB_GEN1":
                            await anb_gen1.process_event(seed_event, active_keys)
                        case "AOK_GEN1":
                            await aok_gen1.process_event(seed_event, active_keys)
                        case "AOK_GEN2":
                            await aok_gen2.process_event(seed_event, active_keys)
                        case "AYA_GEN1":
                            await aya_gen1.process_event(seed_event, active_keys)
                        case "AYA_GEN2":
                            await aya_gen2.process_event(seed_event, active_keys)
                        case "AYA_GEN3":
                            await aya_gen3.process_event(seed_event, active_keys)
                        case "AYA_GEN4":
                            await aya_gen4.process_event(seed_event, active_keys)
                        case "AYA_GEN5":
                            await aya_gen5.process_event(seed_event, active_keys)
                        case "AYA_GEN6":
                            await aya_gen6.process_event(seed_event, active_keys)
                        case "AYA_GEN7":
                            await aya_gen7.process_event(seed_event, active_keys)
                        case "AYN_GEN1":
                            await ayn_gen1.process_event(seed_event, active_keys)
                        case "AYN_GEN2":
                            await ayn_gen2.process_event(seed_event, active_keys)
                        case "GPD_GEN1":
                            await gpd_gen1.process_event(seed_event, active_keys)
                        case "GPD_GEN2":
                            await gpd_gen2.process_event(seed_event, active_keys)
                        case "GPD_GEN3":
                            await gpd_gen3.process_event(seed_event, active_keys)
                        case "OXP_GEN1":
                            await oxp_gen1.process_event(seed_event, active_keys)
                        case "OXP_GEN2":
                            await oxp_gen2.process_event(seed_event, active_keys)
                        case "OXP_GEN3":
                            await oxp_gen3.process_event(seed_event, active_keys)
                        case "OXP_GEN4":
                            await oxp_gen4.process_event(seed_event, active_keys)

            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from {handycon.keyboard_device.name}")
                handycon.logger.error(traceback.format_exc())
                remove_device(HIDE_PATH, handycon.keyboard_event)
                handycon.keyboard_device = None
                handycon.keyboard_event = None
                handycon.keyboard_path = None
        else:
            handycon.logger.info("Attempting to grab keyboard device...")
            get_keyboard()
            await asyncio.sleep(DETECT_DELAY)


# Captures keyboard events and translates them to virtual device events.
async def capture_keyboard_2_events():
    global handycon

    # Capture keyboard events and translate them to mapped events.
    while handycon.running:
        if handycon.keyboard_2_device:
            try:
                async for seed_event_2 in handycon.keyboard_2_device.async_read_loop():
                    # Loop variables
                    active_keys_2 = handycon.keyboard_2_device.active_keys()

                    # Debugging variables
                    handycon.logger.debug(f"Seed Value: {seed_event_2.value}, Seed Code: {seed_event_2.code}, Seed Type: {seed_event_2.type}.")
                    if active_keys_2 != []:
                        handycon.logger.debug(f"Active Keys: {active_keys_2}")
                    else:
                        handycon.logger.debug("No active keys")
                    if handycon.event_queue != []:
                        handycon.logger.debug(f"Queued events: {handycon.event_queue}")
                    else:
                        handycon.logger.debug("No active events.")

                    # Capture keyboard events and translate them to mapped events.
                    match handycon.system_type:
                        case "ALY_GEN1":
                           await ally_gen1.process_event(seed_event_2, active_keys_2)

            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from {handycon.keyboard_2_device.name}")
                handycon.logger.error(traceback.format_exc())
                remove_device(HIDE_PATH, handycon.keyboard_2_event)
                handycon.keyboard_2_device = None
                handycon.keyboard_2_event = None
                handycon.keyboard_2_path = None
        else:
            handycon.logger.info("Attempting to grab keyboard device 2...")
            get_keyboard_2()
            await asyncio.sleep(DETECT_DELAY)


async def capture_controller_events():
    global handycon

    handycon.logger.debug(f"capture_controller_events, {handycon.running}")
    while handycon.running:
        if handycon.controller_device:
            try:
                async for event in handycon.controller_device.async_read_loop():
                    # Block FF events, or get infinite recursion. Up to you I guess...
                    if event.type in [e.EV_FF, e.EV_UINPUT]:
                        continue

                    # Output the event.
                    emit_event(event)
            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from {handycon.controller_device.name}.")
                handycon.logger.error(traceback.format_exc())
                remove_device(HIDE_PATH, handycon.controller_event)
                handycon.controller_device = None
                handycon.controller_event = None
                handycon.controller_path = None
        else:
            handycon.logger.info("Attempting to grab controller device...")
            get_controller()
            await asyncio.sleep(DETECT_DELAY)


# Captures power events and handles long or short press events.
async def capture_power_events():
    global handycon

    while handycon.running:
        if handycon.power_device:
            try:
                async for event in handycon.power_device.async_read_loop():
                    handycon.logger.debug(f"Got event: {event.type} | {event.code} | {event.value}")
                    if event.type == e.EV_KEY and event.code == 116: # KEY_POWER
                        if event.value == 0:
                            handle_power_action()

            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from power device.")
                handycon.logger.error(traceback.format_exc())
                handycon.power_device = None

        elif handycon.power_device_2 and not handycon.power_device:
            try:
                async for event in handycon.power_device_2.async_read_loop():
                    handycon.logger.debug(f"Got event: {event.type} | {event.code} | {event.value}")
                    if event.type == e.EV_KEY and event.code == 116: # KEY_POWER
                        if event.value == 0:
                            handle_power_action()

            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from power device.")
                handycon.logger.error(traceback.format_exc())
                handycon.power_device_2 = None

        else:
            handycon.logger.info("Attempting to grab controller device...")
            get_powerkey()
            await asyncio.sleep(DETECT_DELAY)


# Performs specific power actions based on user config.
def handle_power_action():
    handycon.logger.debug(f"Power Action: {handycon.power_action}")
    match handycon.power_action:
        case "Suspend":
            # For DeckUI Sessions
            is_deckui = handycon.steam_ifrunning_deckui("steam://shortpowerpress")

            # For BPM and Desktop sessions
            if not is_deckui:
                os.system('systemctl suspend')

        case "Hibernate":
            os.system('systemctl hibernate')

        case "Shutdown":
            is_deckui = handycon.steam_ifrunning_deckui("steam://longpowerpress")

            if not is_deckui:
                os.system('systemctl poweroff')

# Handle FF event uploads
async def capture_ff_events():
    global handycon

    ff_effect_id_set = set()

    async for event in handycon.ui_device.async_read_loop():
        if handycon.controller_device is None:
            # Slow down the loop so we don't waste millions of cycles and overheat our controller.
            await asyncio.sleep(DETECT_DELAY)
            continue

        if event.type == e.EV_FF:
            # Forward FF event to controller.
            handycon.controller_device.write(e.EV_FF, event.code, event.value)
            continue

        # Programs will submit these EV_UINPUT events to ensure the device is capable.
        # Doing this forever doesn't seem to pose a problem, and attempting to ignore
        # any of them causes the program to halt.
        if event.type != e.EV_UINPUT:
            continue

        if event.code == e.UI_FF_UPLOAD:
            # Upload to the virtual device to prevent threadlocking. This does nothing else
            upload = handycon.ui_device.begin_upload(event.value)
            effect = upload.effect

            if effect.id not in ff_effect_id_set:
                effect.id = -1 # set to -1 for kernel to allocate a new id. all other values throw an error for invalid input.

            try:
                # Upload to the actual controller.
                effect_id = handycon.controller_device.upload_effect(effect)
                effect.id = effect_id

                ff_effect_id_set.add(effect_id)

                upload.retval = 0
            except IOError as err:
                handycon.logger.error(f"{err} | Error uploading effect {effect.id}.")
                handycon.logger.error(traceback.format_exc())
                upload.retval = -1
            
            handycon.ui_device.end_upload(upload)

        elif event.code == e.UI_FF_ERASE:
            erase = handycon.ui_device.begin_erase(event.value)

            try:
                handycon.controller_device.erase_effect(erase.effect_id)
                ff_effect_id_set.remove(erase.effect_id)
                erase.retval = 0
            except IOError as err:
                handycon.logger.error(f"{err} | Error erasing effect {erase.effect_id}.")
                handycon.logger.error(traceback.format_exc())
                erase.retval = -1

            handycon.ui_device.end_erase(erase)


def restore_device(event, path):
    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(str(HIDE_PATH / event), path)
    except FileNotFoundError:
        pass


def restore_hidden():
    hidden_events = os.listdir(HIDE_PATH)
    if len(hidden_events) == 0:
        return
    for hidden_event in hidden_events:
        handycon.logger.debug(f'Restoring {hidden_event}')
        move(str(HIDE_PATH / hidden_event), "/dev/input/" + hidden_event)


def remove_device(path, event):
    try:
        os.remove(str(path / event))
    except FileNotFoundError:
        pass

# Emits passed or generated events to the virtual controller.
# This shouldn't be called directly for custom events, only to pass realtime events.
# Use emit_now and the device's event_queue.
async def emit_events(events: list):

    for event in events:
        emit_event(event)
        # Pause between multiple events, but not after the last one in the list.
        if event != events[len(events)-1]:
            await asyncio.sleep(handycon.BUTTON_DELAY)


# Emit a single event. Skips some logic checks for optimization.
def emit_event(event):
    global handycon
    handycon.logger.debug(f"Emitting event: {event}")
    handycon.ui_device.write_event(event)
    handycon.ui_device.syn()


# Generates events from an event list. Can be called directly or when looping through
# the event queue.
async def emit_now(seed_event, event_list, value):
    global handycon

    # Ignore malformed requests
    if not event_list:
        handycon.logger.error("emit_now received malfirmed event_list. No action") 
        return

    # Handle string events
    if type(event_list[0]) == str:
        if value == 0:
            handycon.logger.debug("Received string event with value 0. KEY_UP event not required. Skipping")
            return
        match event_list[0]:
            case "Open Chimera":
                handycon.logger.debug("Open Chimera")
                handycon.launch_chimera()
            case "Toggle Gyro":
                handycon.logger.debug("Toggle Gyro is not currently enabled")
            case "Toggle Mouse Mode":
                handycon.logger.debug("Toggle Mouse Mode is not currently enabled")
            case "Toggle Performance":
                handycon.logger.debug("Toggle Performance")
                await toggle_performance()
            case "Hibernate", "Suspend", "Shutdown":
                handycon.logger.error(f"Power mode {event_list[0]} set to button action. Check your configuration file.")
            case _:
                handycon.logger.warn(f"{event_list[0]} not defined.")
        return

    handycon.logger.debug(f'Event list: {event_list}')
    events = []

    if value == 0:
        for button_event in reversed(event_list):
            new_event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], value)
            events.append(new_event)
    else:
        for button_event in event_list:
            new_event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], value)
            events.append(new_event)

    size = len(events)
    if size > 1:
        await emit_events(events)
    elif size == 1:
        emit_event(events[0])


async def handle_key_down(seed_event, queued_event):
    handycon.event_queue.append(queued_event)
    if queued_event in INSTANT_EVENTS:
        await handycon.emit_now(seed_event, queued_event, 1)


async def handle_key_up(seed_event, queued_event):
    if queued_event in INSTANT_EVENTS:
        handycon.event_queue.remove(queued_event)
        await handycon.emit_now(seed_event, queued_event, 0)
    elif queued_event in QUEUED_EVENTS:
        # Create list of events to fire.
        # Handle new button presses.
        if not handycon.last_button:
            handycon.event_queue.remove(queued_event)
            handycon.last_button = queued_event
            await handycon.emit_now(seed_event, queued_event, 1)
            return

        # Clean up old button presses.
        if handycon.last_button:
            await handycon.emit_now(seed_event, handycon.last_button, 0)
            handycon.last_button = None


async def toggle_performance():
    global handycon

    if handycon.performance_mode == "--max-performance":
        handycon.performance_mode = "--power-saving"
        await do_rumble(0, 100, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await do_rumble(0, 100, 1000, 0)
    else:
        handycon.performance_mode = "--max-performance"
        await do_rumble(0, 500, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await do_rumble(0, 75, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await do_rumble(0, 75, 1000, 0)

    ryzenadj_command = f'ryzenadj {handycon.performance_mode}'
    run = os.popen(ryzenadj_command, 'r', 1).read().strip()
    handycon.logger.debug(run)

    if handycon.system_type in ["ALY_GEN1"]:
        if handycon.thermal_mode == "1":
            handycon.thermal_mode = "0"
        else:
            handycon.thermal_mode = "1"

        command = f'echo {handycon.thermal_mode} > /sys/devices/platform/asus-nb-wmi/throttle_thermal_policy'
        run = os.popen(command, 'r', 1).read().strip()
        handycon.logger.debug(f'Thermal mode set to {handycon.thermal_mode}.')


def make_controller():
    global handycon

    # Create the virtual controller.
    handycon.ui_device = UInput(
            CONTROLLER_EVENTS,
            name='Handheld Controller',
            bustype=0x3,
            vendor=0x045e,
            product=0x028e,
            version=0x110
            )
