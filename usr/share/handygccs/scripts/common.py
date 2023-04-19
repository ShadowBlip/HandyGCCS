#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

import asyncio
import configparser
import logging
import os
import re
import subprocess
import sys

from constants import *
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff
from pathlib import Path
from shutil import move
from time import sleep

logging.basicConfig(format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(message)s",
                    datefmt="%y%m%d_%H:%M:%S",
                    level=logging.INFO
                    )

logger = logging.getLogger(__name__)

# Identify the current device type. Kill script if not compatible.
def id_system():

    system_id = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
    cpu_vendor = get_cpu_vendor()
    logger.debug(f"Found CPU Vendor: {cpu_vendor}")

    ## Aya Neo Devices
    if system_id in (
        "AYA NEO FOUNDER",
        "AYA NEO 2021",
        "AYANEO 2021",
        "AYANEO 2021 Pro",
        "AYANEO 2021 Pro Retro Power",
        ):
        system_type = "AYA_GEN1"
        from aya_gen1 import *

    elif system_id in (
        "NEXT",
        "NEXT Pro",
        "NEXT Advance",
        "AYANEO NEXT",
        "AYANEO NEXT Pro",
        "AYANEO NEXT Advance",
        ):
        system_type = "AYA_GEN2"

    elif system_id in (
        "AIR",
        "AIR Pro",
        ):
        system_type = "AYA_GEN3"
    
    elif system_id in (
        "AYANEO 2",
        "GEEK",
        ):
        system_type = "AYA_GEN4"


    ## ONEXPLAYER and AOKZOE devices.
    # BIOS have incomplete DMI data and most models report as "ONE XPLAYER" or "ONEXPLAYER".
    elif system_id in (
        "ONE XPLAYER",
        "ONEXPLAYER",
        "ONEXPLAYER mini A07",
        ):
        if cpu_vendor == "GenuineIntel":
            system_type = "OXP_GEN1"
        else:
            system_type = "OXP_GEN2"

    elif system_id in (
        "ONEXPLAYER Mini Pro",
        "AOKZOE A1 AR07"
        ):
        system_type = "OXP_GEN3"

    ## GPD Devices.
    # Have 2 buttons with 3 modes (left, right, both)
    elif system_id in (
        "G1618-03", #Win3
        ):
        system_type = "GPD_GEN1"

    elif system_id in (
        "G1618-04", #WinMax2
        ):
        system_type = "GPD_GEN2"

    elif system_id in (
        "G1619-04", #Win4
        ):
        system_type = "GPD_GEN3"

    ## ANBERNIC Devices
    elif system_id in (
            "Win600",
            ):
        system_type = "ABN_GEN1"

    # Block devices that aren't supported as this could cause issues.
    else:
        logger.error(f"{system_id} is not currently supported by this tool. Open an issue on \
GitHub at https://github.com/ShadowBlip/aya-neo-fixes if this is a bug. If possible, \
please run the capture-system.py utility found on the GitHub repository and upload \
that file with your issue.")
        sys.exit(0)

    logger.info(f"Identified host system as {system_id} and configured defaults for {system_type}.")

def get_cpu_vendor():
    command = "cat /proc/cpuinfo"
    all_info = subprocess.check_output(command, shell=True).decode().strip()
    for line in all_info.split("\n"):
        if "vendor_id" in line:
                return re.sub( ".*vendor_id.*:", "", line,1).strip()

def get_config():
    global button_map
    global gyro_sensitivity

    config = configparser.ConfigParser()

    # Check for an existing config file and load it.
    config_dir = "/etc/handygccs/"
    config_path = config_dir+"handygccs.conf"
    if os.path.exists(config_path):
        logger.info(f"Loading existing config: {config_path}")
        config.read(config_path)
    else:
        # Make the HandyGCCS directory if it doesn't exist.
        if not os.path.exists(config_dir):
            os.mkdir(config_dir)

        # Write a basic config file.
        config["Button Map"] = {
                "button1": "SCR",
                "button2": "QAM",
                "button3": "ESC",
                "button4": "OSK",
                "button5": "MODE",
                }
        config["Gyro"] = {"sensitivity": "20"}
        with open(config_path, 'w') as config_file:
            config.write(config_file)
            logger.info(f"Created new config: {config_path}")

    # Assign config file values
    button_map = {
    "button1": EVENT_MAP[config["Button Map"]["button1"]],
    "button2": EVENT_MAP[config["Button Map"]["button2"]],
    "button3": EVENT_MAP[config["Button Map"]["button3"]],
    "button4": EVENT_MAP[config["Button Map"]["button4"]],
    "button5": EVENT_MAP[config["Button Map"]["button5"]],
    }
    gyro_sensitivity = int(config["Gyro"]["sensitivity"])

def make_controller():
    global ui_device

    # Create the virtual controller.
    ui_device = UInput(
            CONTROLLER_EVENTS,
            name='Handheld Controller',
            bustype=0x3,
            vendor=0x045e,
            product=0x028e,
            version=0x110
            )

def get_controller():
    global CAPTURE_CONTROLLER
    global GAMEPAD_ADDRESS
    global GAMEPAD_NAME
    global controller_device
    global controller_event
    global controller_path

    # Identify system input event devices.
    try:
        devices_original = [InputDevice(path) for path in list_devices()]

    except Exception as err:
        logger.error("Error when scanning event devices. Restarting scan.")
        sleep(DETECT_DELAY)
        return False

    # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
    for device in devices_original:
        if device.name == GAMEPAD_NAME and device.phys == GAMEPAD_ADDRESS:
            controller_path = device.path
            controller_device = InputDevice(controller_path)
            if CAPTURE_CONTROLLER:
                controller_device.grab()
                controller_event = Path(controller_path).name
                move(controller_path, str(HIDE_PATH / controller_event))
            break

    # Sometimes the service loads before all input devices have full initialized. Try a few times.
    if not controller_device:
        logger.warn("Controller device not yet found. Restarting scan.")
        sleep(DETECT_DELAY)
        return False
    else:
        logger.info(f"Found {controller_device.name}. Capturing input data.")
        return True

def get_keyboard():
    global CAPTURE_KEYBOARD
    global KEYBOARD_ADDRESS
    global KEYBOARD_NAME
    global keyboard_device
    global keyboard_event
    global keyboard_path
    global system_type

    try:
        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in [InputDevice(path) for path in list_devices()]:
            logger.debug(f"{device.name}, {device.phys}")
            if device.name == KEYBOARD_NAME and device.phys == KEYBOARD_ADDRESS:
                keyboard_path = device.path
                keyboard_device = InputDevice(keyboard_path)

            if CAPTURE_KEYBOARD and keyboard_device:
                keyboard_device.grab()
                keyboard_event = Path(keyboard_path).name
                move(keyboard_path, str(HIDE_PATH / keyboard_event))
                break

        # Sometimes the service loads before all input devices have full initialized. Try a few times.
        if not keyboard_device:
            logger.warn("Keyboard device not yet found. Restarting scan.")
            sleep(DETECT_DELAY)
            return False
        else:
            logger.info(f"Found {keyboard_device.name}. Capturing input data.")
            return True

    # Some funky stuff happens sometimes when booting. Give it another shot.
    except Exception as err:
        logger.error("Error when scanning event devices. Restarting scan.")
        sleep(DETECT_DELAY)
        return False

def get_powerkey():
    global CAPTURE_POWER
    global POWER_BUTTON_PRIMARY
    global POWER_BUTTON_SECONDARY
    global power_device
    global power_device_extra

    # Identify system input event devices.
    try:
        devices_original = [InputDevice(path) for path in list_devices()]
    # Some funky stuff happens sometimes when booting. Give it another shot.
    except Exception as err:
        logger.error("Error when scanning event devices. Restarting scan.")
        sleep(DETECT_DELAY)
        return False

    # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
    for device in devices_original:

        # Power Button
        if device.name == 'Power Button' and device.phys == POWER_BUTTON_PRIMARY:
            power_device = device
            if CAPTURE_POWER:
                power_device.grab()

        # Some devices (e.g. AYANEO GEEK) have an extra power input device corresponding to the same
        # physical button that needs to be grabbed.
        if device.name == 'Power Button' and device.phys == POWER_BUTTON_SECONDARY:
            power_device_extra = device
            if CAPTURE_POWER:
                power_device_extra.grab()

    if not power_device:
        logger.warn("Power Button device not yet found. Restarting scan.")
        sleep(DETECT_DELAY)
        return False
    else:
        logger.info(f"Found {power_device.name}. Capturing input data.")
        return True

def get_gyro():
    global GYRO_I2C_ADDR
    global GYRO_I2C_BUS
    global gyro_device

    if not GYRO_I2C_BUS or not GYRO_I2C_ADDR:
        logger.info(f"Gyro device not configured for this system. Skipping gyro device setup.")
        gyro_device = False
        return

    # Make a gyro_device, if it exists.
    try:
        from BMI160_i2c import Driver
        gyro_device = Driver(addr=GYRO_I2C_ADDR, bus=GYRO_I2C_BUS)
        logger.info("Found gyro device. Gyro support enabled.")
    except ModuleNotFoundError as err:
        logger.error(f"{err} | Gyro device not initialized. Skipping gyro device setup.")
        gyro_device = False
    except (BrokenPipeError, FileNotFoundError, NameError, OSError) as err:
        logger.error(f"{err} | Gyro device not initialized. Ensure bmi160_i2c and i2c_dev modules are loaded. Skipping gyro device setup.")
        gyro_device = False

async def do_rumble(button=0, interval=10, length=1000, delay=0):
    global controller_device

    # Prevent look crash if controller_device was taken.
    if not controller_device:
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
    effect_id = controller_device.upload_effect(effect)
    controller_device.write(e.EV_FF, effect_id, 1)
    await asyncio.sleep(interval / 1000)
    controller_device.erase_effect(effect_id)

async def capture_controller_events():
    global controller_device
    global controller_events
    global gyro_device
    global last_x_val
    global last_y_val

    while running:
        if controller_device:
            try:
                async for event in controller_device.async_read_loop():
                    # Block FF events, or get infinite recursion. Up to you I guess...
                    if event.type in [e.EV_FF, e.EV_UINPUT]:
                        continue
                     
                    # If gyro is enabled, queue all events so the gyro event handler can manage them.
                    if gyro_device is not None and gyro_enabled:
                        adjusted_val = None

                        # We only modify RX/RY ABS events.
                        if event.type == e.EV_ABS and event.code == e.ABS_RX:
                            # Record last_x_val before adjustment. 
                            # If right stick returns to the original position there is always an event that sets last_x_val back to zero. 
                            last_x_val = event.value
                            angular_velocity_x = float(gyro_device.getRotationX()[0] / 32768.0 * 2000)
                            adjusted_val = max(min(int(angular_velocity_x * gyro_sensitivity) + event.value, JOY_MAX), JOY_MIN)
                        if event.type == e.EV_ABS and event.code == e.ABS_RY:
                            # Record last_y_val before adjustment. 
                            # If right stick returns to the original position there is always an event that sets last_y_val back to zero. 
                            last_y_val = event.value
                            angular_velocity_y = float(gyro_device.getRotationY()[0] / 32768.0 * 2000)
                            adjusted_val = max(min(int(angular_velocity_y * gyro_sensitivity) + event.value, JOY_MAX), JOY_MIN)

                        if adjusted_val:
                            # Overwrite the event.
                            event = InputEvent(event.sec, event.usec, event.type, event.code, adjusted_val)

                    # Output the event.
                    await emit_events([event])
            except Exception as err:
                logger.error(f"{err} | Error reading events from {controller_device.name}.")
                restore_controller()
                controller_device = None
                controller_event = None
                controller_path = None
        else:
            logger.info("Attempting to grab controller device...")
            get_controller()
            await asyncio.sleep(DETECT_DELAY)

async def capture_gyro_events():
    global controller_events
    global gyro_device
    global gyro_enabled
    global last_x_val
    global last_y_val

    while running:
        # Only run this loop if gyro is enabled
        if gyro_device:
            if gyro_enabled:
                # Periodically output the EV_ABS events according to the gyro readings.
                angular_velocity_x = float(gyro_device.getRotationX()[0] / 32768.0 * 2000)
                adjusted_x = max(min(int(angular_velocity_x * gyro_sensitivity) + last_x_val, JOY_MAX), JOY_MIN)
                x_event = InputEvent(0, 0, e.EV_ABS, e.ABS_RX, adjusted_x)
                angular_velocity_y = float(gyro_device.getRotationY()[0] / 32768.0 * 2000)
                adjusted_y = max(min(int(angular_velocity_y * gyro_sensitivity) + last_y_val, JOY_MAX), JOY_MIN)
                y_event = InputEvent(0, 0, e.EV_ABS, e.ABS_RY, adjusted_y)

                await emit_events([x_event])
                await emit_events([y_event])
                await asyncio.sleep(0.01)

            else:
                # Slow down the loop so we don't waste millions of cycles and overheat our controller.
                await asyncio.sleep(.5)
        else:
            if gyro_device == None:
                get_gyro()
            elif gyro_device == False:
                break

def steam_ifrunning_deckui(cmd):
    # Get the currently running Steam PID.
    steampid_path = HOME_PATH / '.steam/steam.pid'
    try:
        with open(steampid_path) as f:
            pid = f.read().strip()
    except Exception as err:
        logger.error(f"{err} | Error getting steam PID.")
        return False

    # Get the commandline for the Steam process by checking /proc.
    steam_cmd_path = f"/proc/{pid}/cmdline"
    if not os.path.exists(steam_cmd_path):
        # Steam not running.
        return False

    try:
        with open(steam_cmd_path, "rb") as f:
            steam_cmd = f.read()
    except Exception as err:
        logger.error(f"{err} | Error getting steam cmdline.")
        return False

    # Use this commandline to determine if Steam is running in DeckUI mode.
    # e.g. "steam://shortpowerpress" only works in DeckUI.
    is_deckui = b"-gamepadui" in steam_cmd
    if not is_deckui:
        return False

    steam_path = HOME_PATH / '.steam/root/ubuntu12_32/steam'
    try:
        result = subprocess.run(["su", USER, "-c", f"{steam_path} -ifrunning {cmd}"])
        return result.returncode == 0
    except Exception as err:
        logger.error(f"{err} | Error sending command to Steam.")
        return False

# Captures power events and handles long or short press events.
async def capture_power_events():
    global HOME_PATH
    global USER

    global power_device
    global shutdown
    
    while running:
        if power_device:
            try:
                async for event in power_device.async_read_loop():
                    active_keys = keyboard_device.active_keys()
                    if event.type == e.EV_KEY and event.code == 116: # KEY_POWER
                        if event.value == 0:
                            if active_keys == [125]:
                                # For DeckUI Sessions
                                shutdown = True
                                steam_ifrunning_deckui("steam://longpowerpress")
                            else:
                                # For DeckUI Sessions
                                is_deckui = steam_ifrunning_deckui("steam://shortpowerpress")
                                if not is_deckui:
                                    # For BPM and Desktop sessions
                                    os.system('systemctl suspend')

                    if active_keys == [125]:
                        await do_rumble(0, 150, 1000, 0)
            
            except Exception as err:
                logger.error(f"{err} | Error reading events from power device.")
                power_device = None
        else:
            logger.info("Attempting to grab power device...")
            get_powerkey()
            await asyncio.sleep(DETECT_DELAY)


# Handle FF event uploads
async def capture_ff_events():
    ff_effect_id_set = set()

    async for event in ui_device.async_read_loop():
        if controller_device is None:
            # Slow down the loop so we don't waste millions of cycles and overheat our controller.
            await asyncio.sleep(.5)
            continue

        if event.type == e.EV_FF:
            # Forward FF event to controller.
            controller_device.write(e.EV_FF, event.code, event.value)
            continue

        # Programs will submit these EV_UINPUT events to ensure the device is capable.
        # Doing this forever doesn't seem to pose a problem, and attempting to ignore
        # any of them causes the program to halt.
        if event.type != e.EV_UINPUT:
            continue

        if event.code == e.UI_FF_UPLOAD:
            # Upload to the virtual device to prevent threadlocking. This does nothing else
            upload = ui_device.begin_upload(event.value)
            effect = upload.effect

            if effect.id not in ff_effect_id_set:
                effect.id = -1 # set to -1 for kernel to allocate a new id. all other values throw an error for invalid input.

            try:
                # Upload to the actual controller.
                effect_id = controller_device.upload_effect(effect)
                effect.id = effect_id

                ff_effect_id_set.add(effect_id)

                upload.retval = 0
            except IOError as err:
                logger.error(f"{err} | Error uploading effect {effect.id}.")
                upload.retval = -1
            
            ui_device.end_upload(upload)

        elif event.code == e.UI_FF_ERASE:
            erase = ui_device.begin_erase(event.value)

            try:
                controller_device.erase_effect(erase.effect_id)
                ff_effect_id_set.remove(erase.effect_id)
                erase.retval = 0
            except IOError as err:
                logger.error(f"{err} | Error erasing effect {erase.effect_id}.")
                erase.retval = -1

            ui_device.end_erase(erase)

# Emits passed or generated events to the virtual controller.
async def emit_events(events: list):
    if len(events) == 1:
        ui_device.write_event(events[0])
        ui_device.syn()

    elif len(events) > 1:
        for event in events:
            ui_device.write_event(event)
            ui_device.syn()
            await asyncio.sleep(BUTTON_DELAY)

# RYZENADJ
async def toggle_performance():
    global performance_mode
    global protocol
    global transport

    if not transport:
        return

    if performance_mode == "--max-performance":
        performance_mode = "--power-saving"
        await do_rumble(0, 75, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await do_rumble(0, 75, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await do_rumble(0, 75, 1000, 0)
    else:
        performance_mode = "--max-performance"
        await do_rumble(0, 500, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await do_rumble(0, 75, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await do_rumble(0, 75, 1000, 0)

    transport.write(bytes(performance_mode, 'utf-8'))
    transport.close()
    transport = None
    protocol = None

async def ryzenadj_control(loop):
    global transport
    global protocol

    while running:
        # Wait for a server to be launched
        if not os.path.exists(server_address):
            await asyncio.sleep(RYZENADJ_DELAY)
            continue

        # Wait for a connection to the server
        if not transport or not protocol:
            try:
                transport, protocol = await loop.create_unix_connection(asyncio.Protocol, path=server_address)
                logger.debug(f"got {transport}, {protocol}")
            except ConnectionRefusedError:
                logger.debug('Could not connect to RyzenaAdj Control')
                await asyncio.sleep(RYZENADJ_DELAY)
                continue
        await asyncio.sleep(RYZENADJ_DELAY)

def launch_chimera():
    if not HAS_CHIMERA_LAUNCHER:
        return
    subprocess.run([ "su", USER, "-c", CHIMERA_LAUNCHER_PATH ])

# Gracefull shutdown.
async def restore_all(loop):
    logger.info("Receved exit signal. Restoring devices.")
    running = False

    if controller_device:
        try:
            controller_device.ungrab()
        except IOError as err:
            logger.warn(f"{err} | Device wasn't grabbed.")
        restore_controller()
    if keyboard_device:
        try:
            keyboard_device.ungrab()
        except IOError as err:
            logger.warn(f"{err} | Device wasn't grabbed.")
        restore_keyboard()
    if power_device and CAPTURE_POWER:
        try:
            power_device.ungrab()
        except IOError as err:
            logger.warn(f"{err} | Device wasn't grabbed.")
    if power_device_extra and CAPTURE_POWER:
        try:
            power_device_extra.ungrab()
        except IOError as err:
            logger.warn(f"{err} | Device wasn't grabbed.")
    logger.info("Devices restored.")

    # Kill all tasks. They are infinite loops so we will wait forver.
    for task in [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    loop.stop()
    logger.info("Handheld Game Console Controller Service stopped.")

def restore_keyboard():
    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(str(HIDE_PATH / keyboard_event), keyboard_path)
    except FileNotFoundError:
        pass

def restore_controller():
    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(str(HIDE_PATH / controller_event), controller_path)
    except FileNotFoundError:
        pass
