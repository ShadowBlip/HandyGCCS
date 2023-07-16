#!/usr/bin/env python3
# This file is part of Handheld Game Console Controlelr System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

## Python Modules
import asyncio
import os

# Local modules
import handycon.handhelds.ally_gen1 as ally_gen1
import handycon.handhelds.anb_gen1 as anb_gen1
import handycon.handhelds.aya_gen1 as aya_gen1
import handycon.handhelds.aya_gen2 as aya_gen2
import handycon.handhelds.aya_gen3 as aya_gen3
import handycon.handhelds.aya_gen4 as aya_gen4
import handycon.handhelds.aya_gen5 as aya_gen5
import handycon.handhelds.aya_gen6 as aya_gen6
import handycon.handhelds.ayn_gen1 as ayn_gen1
import handycon.handhelds.gpd_gen1 as gpd_gen1
import handycon.handhelds.gpd_gen2 as gpd_gen2
import handycon.handhelds.gpd_gen3 as gpd_gen3
import handycon.handhelds.oxp_gen1 as oxp_gen1
import handycon.handhelds.oxp_gen2 as oxp_gen2
import handycon.handhelds.oxp_gen3 as oxp_gen3
import handycon.handhelds.oxp_gen4 as oxp_gen4
from .constants import *

## Partial imports
from evdev import InputDevice, ecodes as e, list_devices, ff
from pathlib import Path
from shutil import move
from time import sleep

handycon = None

def set_handycon(handheld_controller):
    handycon = handheld_controller


def get_controller():
    handycon.logger.debug(f"Attempting to grab {handycon.GAMEPAD_NAME}.")
    # Identify system input event devices.
    try:
        devices_original = [InputDevice(path) for path in list_devices()]

    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
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
    handycon.logger.debug(f"Attempting to grab {handycon.KEYBOARD_NAME}.")
    try:
        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in [InputDevice(path) for path in list_devices()]:
            handycon.logger.debug(f"{device.name}, {device.phys}")
            if device.name == handycon.KEYBOARD_NAME and device.phys == handycon.KEYBOARD_ADDRESS:
                handycon.keyboard_path = device.path
                handycon.keyboard_device = InputDevice(.keyboard_path)
                if handycon.CAPTURE_KEYBOARD:
                    handycon.keyboard_device.grab()
                    handycon.keyboard_event = Path(handycon..keyboard_path).name
                    move(.keyboard_path, str(HIDE_PATH / handycon.keyboard_event))
                break

        # Sometimes the service loads before all input devices have full initialized. Try a few times.
        if not handycon.keyboard_device:
            handycon.logger.warn("Keyboard device not yet found. Restarting scan.")
            sleep(DETECT_DELAY)
            return False
        else:
            handycon.logger.info(f"Found {handycon.keyboard_device.name}. Capturing input data.")
            return True

    # Some funky stuff happens sometimes when booting. Give it another shot.
    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
        sleep(DETECT_DELAY)
        return False


def get_keyboard_2():
    handycon.logger.debug(f"Attempting to grab {handycon.KEYBOARD_2_NAME}.")
    try:
        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in [InputDevice(path) for path in list_devices()]:
            handycon.logger.debug(f"{device.name}, {device.phys}")
            if device.name == handycon.KEYBOARD_2_NAME and device.phys == handycon.KEYBOARD_2_ADDRESS:
                handycon.keyboard_2_path = device.path
                handycon.keyboard_2_device = InputDevice(handycon.keyboard_2_path)
                if handycon.CAPTURE_KEYBOARD:
                    handycon.keyboard_2_device.grab()
                    handycon.keyboard_2_event = Path(.keyboard_2_path).name
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

    # Some funky stuff happens sometimes when booting. Give it another shot.
    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
        sleep(DETECT_DELAY)
        return False


def get_powerkey():
    handycon.logger.debug(f"Attempting to grab power buttons.")
    # Identify system input event devices.
    try:
        devices_original = [InputDevice(path) for path in list_devices()]
    # Some funky stuff happens sometimes when booting. Give it another shot.
    except Exception as err:
        handycon.logger.error("Error when scanning event devices. Restarting scan.")
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


async def do_rumble(, button=0, interval=10, length=1000, delay=0):
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
                        case "ANB_GEN1":
                            await anb_gen1.process_event(seed_event, active_keys)
                        case "ALY_GEN1":
                            await ally_gen1.process_event(seed_event, active_keys)
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
                        case "AYN_GEN1":
                            await ayn_gen1.process_event(seed_event, active_keys)
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

            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from {handycon.keyboard_device.name}")
                handycon.restore_keyboard()
                handycon.keyboard_device = None
                handycon.keyboard_event = None
                handycon.keyboard_path = None
        else:
            handycon.logger.info("Attempting to grab keyboard device...")
            handycon.get_keyboard()
            await asyncio.sleep(DETECT_DELAY)


# Captures keyboard events and translates them to virtual device events.
async def capture_keyboard_2_events():
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
                handycon.restore_keyboard_2()
                handycon.keyboard_2_device = None
                handycon.keyboard_2_event = None
                handycon.keyboard_2_path = None
        else:
            handycon.logger.info("Attempting to grab keyboard device 2...")
            handycon.get_keyboard_2()
            await asyncio.sleep(DETECT_DELAY)


async def capture_controller_events():
    handycon.logger.debug(f"capture_controller_events, {handycon.running}")
    while handycon.running:
        if handycon.controller_device:
            try:
                async for event in handycon.controller_device.async_read_loop():
                    # Block FF events, or get infinite recursion. Up to you I guess...
                    if event.type in [e.EV_FF, e.EV_UINPUT]:
                        continue

                    # Output the event.
                    await handycon.emit_events([event])
            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from {handycon.controller_device.name}.")
                handycon.restore_controller()
                handycon.controller_device = None
                handycon.controller_event = None
                handycon.controller_path = None
        else:
            handycon.logger.info("Attempting to grab controller device...")
            handycon.get_controller()
            await asyncio.sleep(DETECT_DELAY)


# Captures power events and handles long or short press events.
async def capture_power_events():
    while handycon.running:
        if handycon.power_device:
            try:
                async for event in handycon.power_device.async_read_loop():
                    handycon.logger.debug(f"Got event: {event.type} | {event.code} | {event.value}")
                    if event.type == e.EV_KEY and event.code == 116: # KEY_POWER
                        if event.value == 0:
                            # For DeckUI Sessions
                            is_deckui = handycon.steam_ifrunning_deckui("steam://shortpowerpress")

                            # For BPM and Desktop sessions
                            if not is_deckui:
                                os.system('systemctl suspend')

            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from power device.")
                handycon.power_device = None

        elif handycon.power_device_2 and not handycon.power_device:
            try:
                async for event in handycon.power_device_2.async_read_loop():
                    handycon.logger.debug(f"Got event: {event.type} | {event.code} | {event.value}")
                    if event.type == e.EV_KEY and event.code == 116: # KEY_POWER
                        if event.value == 0:
                            # For DeckUI Sessions
                            is_deckui = handycon.steam_ifrunning_deckui("steam://shortpowerpress")

                            # For BPM and Desktop sessions
                            if not is_deckui:
                                os.system('systemctl suspend')

            except Exception as err:
                handycon.logger.error(f"{err} | Error reading events from power device.")
                handycon.power_device_2 = None

        else:
            handycon.logger.info("Attempting to grab controller device...")
            handycon.get_powerkey()
            await asyncio.sleep(DETECT_DELAY)


# Handle FF event uploads
async def capture_ff_events():
    ff_effect_id_set = set()

    async for event in handycon.ui_device.async_read_loop():
        if handycon.controller_device is None:
            # Slow down the loop so we don't waste millions of cycles and overheat our controller.
            await asyncio.sleep(.5)
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
                erase.retval = -1

            handycon.ui_device.end_erase(erase)


def restore_device(event, path):
    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(str(HIDE_PATH / event), path)
    except FileNotFoundError:
        pass

# Emits passed or generated events to the virtual controller.
async def emit_events(self, events: list):
    for event in events:
        self.logger.debug(f"Emitting event: {event}")
        self.ui_device.write_event(event)
        self.ui_device.syn()
        # Pause between multiple events, but not after the last one in the list.
        if event != events[len(events)-1]:
            await asyncio.sleep(self.BUTTON_DELAY)


# Generates events from an event list to immediately emit, bypassing queue.
async def emit_now(self, seed_event, event_list, value):

    # Ignore malformed requests
    if not event_list:
        self.logger.error("emit_now received malfirmed event_list. No action") 
        return

    # Handle string events
    if type(event_list[0]) == str:
        if value == 0:
            self.logger.debug("Received string event with value 0. KEY_UP event not required. Skipping")
            return
        match event_list[0]:
            case "RyzenAdj Toggle":
                self.logger.debug("RyzenAdj Toggle")
                await self.toggle_performance()
            case "Open Chimera":
                self.logger.debug("Open Chimera")
                self.launch_chimera()
            case "Toggle Gyro":
                self.logger.debug("Toggle Gyro is not currently enabled")
            case _:
                self.logger.debug(f"{event_list[0]} not defined.")
        return

    self.logger.debug(f'Event list: {event_list}')
    events = []

    if value == 0:
        for button_event in reversed(event_list):
            new_event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], value)
            events.append(new_event)
    else:
        for button_event in event_list:
            new_event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], value)
            events.append(new_event)

    if events != []:


def make_controller():
    # Create the virtual controller.
    handycon.ui_device = UInput(
            CONTROLLER_EVENTS,
            name='Handheld Controller',
            bustype=0x3,
            vendor=0x045e,
            product=0x028e,
            version=0x110
            )


