#!/usr/bin/env python3
# HandyGCCS HandyCon
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot 
# This will create a virtual UInput device and pull data from the built-in
# controller and "keyboard". Right side buttons are keyboard buttons that
# send macros (i.e. CTRL/ALT/DEL). We capture those events and send button
# presses that Steam understands.

# Python Modules
import asyncio
import configparser
import logging
import os
import re
import signal
import subprocess
import sys
import warnings

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

# Partial imports
from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff
from pathlib import Path
from shutil import move
from time import sleep


warnings.filterwarnings("ignore", category=DeprecationWarning)
class HandheldController:
    # Logging
    logging.basicConfig(format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(message)s",
                        datefmt="%y%m%d_%H:%M:%S",
                        level=logging.DEBUG
                        )
    logger= logging.getLogger(__name__)
    
    # Session Variables
    button_map = {}
    event_queue = [] # Stores inng button presses to block spam
    #gyro_enabled = False
    #gyro_sensitivity = 0
    last_button = None
    last_x_val = 0
    last_y_val = 0
    running = False
    shutdown = False
    
    # Handheld Config
    BUTTON_DELAY = 0.00
    CAPTURE_CONTROLLER = False
    CAPTURE_KEYBOARD = False
    CAPTURE_POWER = False
    GAMEPAD_ADDRESS = ''
    GAMEPAD_NAME = ''
    GYRO_I2C_ADDR = 0x00
    GYRO_I2C_BUS = 0
    KEYBOARD_ADDRESS = ''
    KEYBOARD_NAME = ''
    KEYBOARD_2_ADDRESS = ''
    KEYBOARD_2_NAME = ''
    POWER_BUTTON_PRIMARY = "LNXPWRBN/button/input0"
    POWER_BUTTON_SECONDARY = "PNP0C0C/button/input0"
    
    # Enviroment Variables
    HAS_CHIMERA_LAUNCHER = False
    USER = None
    HOME_PATH = None
    
    # UInput Devices
    controller_device = None
    #gyro_device = None
    keyboard_device = None
    keyboard_2_device = None
    power_device = None
    power_device_2 = None
    
    # Paths
    controller_event = None
    controller_path = None
    keyboard_event = None
    keyboard_path = None
    keyboard_2_event = None
    keyboard_2_path = None
    
    # RyzenAdj settings
    performance_mode = "--power-saving"
    protocol = None
    RYZENADJ_DELAY = 0.5
    selected_performance = None
    transport = None
    
    def __init__(self):
        self.running = True
        self.logger.info("Starting Handhend Game Console Controller Service...") 
        self.get_user()
        self.HAS_CHIMERA_LAUNCHER=os.path.isfile(CHIMERA_LAUNCHER_PATH)
        self.id_system()
        Path(HIDE_PATH).mkdir(parents=True, exist_ok=True)
        self.get_config()
        self.make_controller()
    
        # Run asyncio loop to capture all events.
        self.loop = asyncio.get_event_loop()
    
        # Attach the event loop of each device to the asyncio loop.
        asyncio.ensure_future(self.capture_controller_events())
        #asyncio.ensure_future(self.capture_gyro_events())
        asyncio.ensure_future(self.capture_ff_events())
        asyncio.ensure_future(self.capture_keyboard_events())
        asyncio.ensure_future(self.capture_power_events())
        asyncio.ensure_future(self.ryzenadj_control())
        self.logger.info("Handheld Game Console Controller Service started.")
    
        # Establish signaling to handle gracefull shutdown.
        for s in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT):
            self.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(self.restore_all()))
    
        try:
            self.loop.run_forever()
            exit_code = 0
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt.")
            exit_code = 1
        except Exception as err:
            self.logger.error(f"{err} | Hit exception condition.")
            exit_code = 2
        finally:
            self.loop.stop()
            sys.exit(exit_code)

    # Capture the username and home path of the user who has been logged in the longest.
    def get_user(self):
        self.logger.debug("Identifying user.")
        cmd = "who | awk '{print $1}' | sort | head -1"
        while self.USER is None:
            USER_LIST = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
            for get_first in USER_LIST.stdout:
                name = get_first.decode().strip()
                if name is not None:
                    self.USER = name
                break
            sleep(1)

        self.logger.debug(f"USER: {self.USER}")
        self.HOME_PATH = "/home/" + self.USER
        self.logger.debug(f"HOME_PATH: {self.HOME_PATH}")


    # Identify the current device type. Kill script if not atible.
    def id_system(self):

        system_id = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
        cpu_vendor = self.get_cpu_vendor()
        self.logger.debug(f"Found CPU Vendor: {cpu_vendor}")

        ## ANBERNIC Devices
        if system_id in (
                "Win600",
                ):
            self.system_type = "ANB_GEN1"
            anb_gen1.init_handheld(self)

        ## ASUS Devices
        elif system_id in (
            "ROG Ally RC71L_RC71L",
            ):
            self.system_type = "ALY_GEN1"
            ally_gen1.init_handheld(self)

        ## Aya Neo Devices
        elif system_id in (
            "AYA NEO FOUNDER",
            "AYA NEO 2021",
            "AYANEO 2021",
            "AYANEO 2021 Pro",
            "AYANEO 2021 Pro Retro Power",
            ):
            self.system_type = "AYA_GEN1"
            aya_gen1.init_handheld(self)

        elif system_id in (
            "NEXT",
            "NEXT Pro",
            "NEXT Advance",
            "AYANEO NEXT",
            "AYANEO NEXT Pro",
            "AYANEO NEXT Advance",
            ):
            self.system_type = "AYA_GEN2"
            aya_gen2.init_handheld(self)

        elif system_id in (
            "AIR",
            "AIR Pro",
            ):
            self.system_type = "AYA_GEN3"
            aya_gen3.init_handheld(self)

        elif system_id in (
            "AYANEO 2",
            "GEEK",
            ):
            self.system_type = "AYA_GEN4"
            aya_gen4.init_handheld(self)

        elif system_id in (
            "AIR Plus",
            ):
            self.system_type = "AYA_GEN5"
            aya_gen5.init_handheld(self)
    
        elif system_id in (
            "AYANEO 2S",
            "GEEK 1S",
            ):
            self.system_type = "AYA_GEN6"
            aya_gen6.init_handheld(self)

        ## Ayn Devices
        elif system_id in (
                "Loki Max",
            ):
            self.system_type = "AYN_GEN1"
            ayn_gen1.init_handheld(self)

        ## GPD Devices.
        # Have 2 buttons with 3 modes (left, right, both)
        elif system_id in (
            "G1618-03", #Win3
            ):
            self.system_type = "GPD_GEN1"
            gpd_gen1.init_handheld(self)
    
        elif system_id in (
            "G1618-04", #WinMax2
            ):
            self.system_type = "GPD_GEN2"
            gpd_gen2.init_handheld(self)
    
        elif system_id in (
            "G1619-04", #Win4
            ):
            self.system_type = "GPD_GEN3"
            gpd_gen3.init_handheld(self)

    ## ONEXPLAYER and AOKZOE devices.
        # BIOS have inlete DMI data and most models report as "ONE XPLAYER" or "ONEXPLAYER".
        elif system_id in (
            "ONE XPLAYER",
            "ONEXPLAYER",
            ):
            if cpu_vendor == "GenuineIntel":
                self.system_type = "OXP_GEN1"
                oxp_gen1.init_handheld(self)
            else:
                self.system_type = "OXP_GEN2"
                oxp_gen2.init_handheld(self)

        elif system_id in (
            "ONEXPLAYER mini A07",
            ):
            self.system_type = "OXP_GEN3"
            oxp_gen3.init_handheld(self)

        elif system_id in (
            "ONEXPLAYER Mini Pro",
            "AOKZOE A1 AR07",
            "AOKZOE A1 Pro",
            ):
            self.system_type = "OXP_GEN4"
            oxp_gen4.init_handheld(self)

        # Block devices that aren't supported as this could cause issues.
        else:
            self.logger.error(f"{system_id} is not currently supported by this tool. Open an issue on \
    GitHub at https://github.ShadowBlip/aya-neo-fixes if this is a bug. If possible, \
    please run the capture-system.py utility found on the GitHub repository and upload \
    that file with your issue.")
            sys.exit(0)
        self.logger.info(f"Identified host system as {system_id} and configured defaults for {self.system_type}.")
    
    
    def get_cpu_vendor(self):
        cmd = "cat /proc/cpuinfo"
        all_info = subprocess.check_output(cmd, shell=True).decode().strip()
        for line in all_info.split("\n"):
            if "vendor_id" in line:
                    return re.sub( ".*vendor_id.*:", "", line,1).strip()
    
    
    def get_config(self):
    
        config = configparser.ConfigParser()
    
        # Check for an existing config file and load it.
        config_dir = "/etc/handygccs/"
        config_path = config_dir+"handygccs.conf"
        if os.path.exists(config_path):
            self.logger.info(f"Loading existing config: {config_path}")
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
                self.logger.info(f"Created new config: {config_path}")
    
        # Assign config file values
        self.button_map = {
        "button1": EVENT_MAP[config["Button Map"]["button1"]],
        "button2": EVENT_MAP[config["Button Map"]["button2"]],
        "button3": EVENT_MAP[config["Button Map"]["button3"]],
        "button4": EVENT_MAP[config["Button Map"]["button4"]],
        "button5": EVENT_MAP[config["Button Map"]["button5"]],
        }
        #self.gyro_sensitivity = int(config["Gyro"]["sensitivity"])
    
    
    def make_controller(self):
        # Create the virtual controller.
        self.ui_device = UInput(
                CONTROLLER_EVENTS,
                name='Handheld Controller',
                bustype=0x3,
                vendor=0x045e,
                product=0x028e,
                version=0x110
                )


    def get_controller(self):
        self.logger.debug(f"Attempting to grab {self.GAMEPAD_NAME}.")
        # Identify system input event devices.
        try:
            devices_original = [InputDevice(path) for path in list_devices()]
    
        except Exception as err:
            self.logger.error("Error when scanning event devices. Restarting scan.")
            sleep(DETECT_DELAY)
            return False
    
        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in devices_original:
            if device.name == self.GAMEPAD_NAME and device.phys == self.GAMEPAD_ADDRESS:
                self.controller_path = device.path
                self.controller_device = InputDevice(self.controller_path)
                if self.CAPTURE_CONTROLLER:
                    self.controller_device.grab()
                    self.controller_event = Path(self.controller_path).name
                    move(self.controller_path, str(HIDE_PATH / self.controller_event))
                break
    
        # Sometimes the service loads before all input devices have full initialized. Try a few times.
        if not self.controller_device:
            self.logger.warn("Controller device not yet found. Restarting scan.")
            sleep(DETECT_DELAY)
            return False
        else:
            self.logger.info(f"Found {self.controller_device.name}. Capturing input data.")
            return True
    
    
    def get_keyboard(self):
        self.logger.debug(f"Attempting to grab {self.KEYBOARD_NAME}.")
        try:
            # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
            for device in [InputDevice(path) for path in list_devices()]:
                self.logger.debug(f"{device.name}, {device.phys}")
                if device.name == self.KEYBOARD_NAME and device.phys == self.KEYBOARD_ADDRESS:
                    self.keyboard_path = device.path
                    self.keyboard_device = InputDevice(self.keyboard_path)
                    if self.CAPTURE_KEYBOARD:
                        self.keyboard_device.grab()
                        self.keyboard_event = Path(self.keyboard_path).name
                        move(self.keyboard_path, str(HIDE_PATH / self.keyboard_event))
                    break

            # Sometimes the service loads before all input devices have full initialized. Try a few times.
            if not self.keyboard_device:
                self.logger.warn("Keyboard device not yet found. Restarting scan.")
                sleep(DETECT_DELAY)
                return False
            else:
                self.logger.info(f"Found {self.keyboard_device.name}. Capturing input data.")
                return True

        # Some funky stuff happens sometimes when booting. Give it another shot.
        except Exception as err:
            self.logger.error("Error when scanning event devices. Restarting scan.")
            sleep(DETECT_DELAY)
            return False


    def get_keyboard_2(self):
        self.logger.debug(f"Attempting to grab {self.KEYBOARD_2_NAME}.")
        try:
            # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
            for device in [InputDevice(path) for path in list_devices()]:
                self.logger.debug(f"{device.name}, {device.phys}")
                if device.name == self.KEYBOARD_2_NAME and device.phys == self.KEYBOARD_2_ADDRESS:
                    self.keyboard_2_path = device.path
                    self.keyboard_2_device = InputDevice(self.keyboard_2_path)
                    if self.CAPTURE_KEYBOARD:
                        self.keyboard_2_device.grab()
                        self.keyboard_2_event = Path(self.keyboard_2_path).name
                        move(self.keyboard_2_path, str(HIDE_PATH / self.keyboard_2_event))
                    break

            # Sometimes the service loads before all input devices have full initialized. Try a few times.
            if not self.keyboard_2_device:
                self.logger.warn("Keyboard device 2 not yet found. Restarting scan.")
                sleep(DETECT_DELAY)
                return False
            else:
                self.logger.info(f"Found {self.keyboard_2_device.name}. Capturing input data.")
                return True

        # Some funky stuff happens sometimes when booting. Give it another shot.
        except Exception as err:
            self.logger.error("Error when scanning event devices. Restarting scan.")
            sleep(DETECT_DELAY)
            return False
    
    
    def get_powerkey(self):
        self.logger.debug(f"Attempting to grab power button.")
        # Identify system input event devices.
        try:
            devices_original = [InputDevice(path) for path in list_devices()]
        # Some funky stuff happens sometimes when booting. Give it another shot.
        except Exception as err:
            self.logger.error("Error when scanning event devices. Restarting scan.")
            sleep(DETECT_DELAY)
            return False
    
        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in devices_original:
    
            # Power Button
            if device.name == 'Power Button' and device.phys == self.POWER_BUTTON_PRIMARY:
                self.power_device = device
                self.logger.debug(f"found power device {self.power_device.phys}")
                if self.CAPTURE_POWER:
                    self.power_device.grab()
    
            # Some devices (e.g. AYANEO GEEK) have an extra power input device corresponding to the same
            # physical button that needs to be grabbed.
            if device.name == 'Power Button' and device.phys == self.POWER_BUTTON_SECONDARY:
                self.power_device_2 = device
                self.logger.debug(f"found alternate power device {self.power_device_2.phys}")
                if self.CAPTURE_POWER:
                    self.power_device_2.grab()
    
        if not self.power_device and not self.power_device_2:
            self.logger.warn("No Power Button found. Restarting scan.")
            sleep(DETECT_DELAY)
            return False
        else:
            if self.power_device:
                self.logger.info(f"Found {self.power_device.name}. Capturing input data.")
            if self.power_device_2:
                self.logger.info(f"Found {self.power_device_2.name}. Capturing input data.")
            return True
    
    
    async def do_rumble(self, button=0, interval=10, length=1000, delay=0):
        # Prevent look crash if controller_device was taken.
        if not self.controller_device:
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
        effect_id = self.controller_device.upload_effect(effect)
        self.controller_device.write(e.EV_FF, effect_id, 1)
        await asyncio.sleep(interval / 1000)
        self.controller_device.erase_effect(effect_id)
    
    
    # Captures keyboard events and translates them to virtual device events.
    async def capture_keyboard_events(self):
        # Get access to global variables. These are globalized because the function
        # is instanciated twice and need to persist accross both instances.

        # Capture keyboard events and translate them to mapped events.
        while self.running:
            if self.keyboard_device:
                try:
                    async for seed_event in self.keyboard_device.async_read_loop():
                        # Loop variables
                        active_keys = self.keyboard_device.active_keys()
    
                        # Debugging variables
                        self.logger.debug(f"Seed Value: {seed_event.value}, Seed Code: {seed_event.code}, Seed Type: {seed_event.type}.")
                        if active_keys != []:
                            self.logger.debug(f"Active Keys: {active_keys}")
                        else:
                            self.logger.debug("No active keys")
                        if self.event_queue != []:
                            self.logger.debug(f"Queued events: {self.event_queue}")
                        else:
                            self.logger.debug("No active events.")
    
                        # Capture keyboard events and translate them to mapped events.
                        match self.system_type:
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
                    self.logger.error(f"{err} | Error reading events from {self.keyboard_device.name}")
                    self.restore_keyboard()
                    self.keyboard_device = None
                    self.keyboard_event = None
                    self.keyboard_path = None
            else:
                self.logger.info("Attempting to grab keyboard device...")
                self.get_keyboard()
                await asyncio.sleep(DETECT_DELAY)

            if self.KEYBOARD_2_NAME == '' or self.KEYBOARD_2_ADDRESS == '':
                continue

            if self.keyboard_2_device:
                try:
                    async for seed_event_2 in self.keyboard_2_device.async_read_loop():
                        # Loop variables
                        active_keys_2 = self.keyboard_2_device.active_keys()
    
                        # Debugging variables
                        self.logger.debug(f"Seed Value: {seed_event_2.value}, Seed Code: {seed_event_2.code}, Seed Type: {seed_event_2.type}.")
                        if active_keys_2 != []:
                            self.logger.debug(f"Active Keys: {active_keys_2}")
                        else:
                            self.logger.debug("No active keys")
                        if self.event_queue != []:
                            self.logger.debug(f"Queued events: {self.event_queue}")
                        else:
                            self.logger.debug("No active events.")
    
                        # Capture keyboard events and translate them to mapped events.
                        match self.system_type:
                            case "ALY_GEN1":
                               await ally_gen1.process_event(seed_event_2, active_keys_2)
    
                except Exception as err:
                    self.logger.error(f"{err} | Error reading events from {self.keyboard_2_device.name}")
                    self.restore_keyboard_2()
                    self.keyboard_2_device = None
                    self.keyboard_2_event = None
                    self.keyboard_2_path = None
            else:
                self.logger.info("Attempting to grab keyboard device 2...")
                self.get_keyboard_2()
                await asyncio.sleep(DETECT_DELAY)
    
    
    async def capture_controller_events(self):
        self.logger.debug(f"capture_controller_events, {self.running}")
        while self.running:
            if self.controller_device:
                try:
                    async for event in self.controller_device.async_read_loop():
                        # Block FF events, or get infinite recursion. Up to you I guess...
                        if event.type in [e.EV_FF, e.EV_UINPUT]:
                            continue
                        #self.logger.debug(f"Got event: {event}")
                        # If gyro is enabled, queue all events so the gyro event handler can manage them.
                        #if self.gyro_device is not None and self.gyro_enabled:
                        #    adjusted_val = None
    
                        #    # We only modify RX/RY ABS events.
                        #    if event.type == e.EV_ABS and event.code == e.ABS_RX:
                        #        # Record last_x_val before adjustment. 
                        #        # If right stick returns to the original position there is always an event that sets last_x_val back to zero. 
                        #        self.last_x_val = event.value
                        #        angular_velocity_x = float(self.gyro_device.getRotationX()[0] / 32768.0 * 2000)
                        #        adjusted_val = max(min(int(angular_velocity_x * self.gyro_sensitivity) + event.value, JOY_MAX), JOY_MIN)
                        #    if event.type == e.EV_ABS and event.code == e.ABS_RY:
                        #        # Record last_y_val before adjustment. 
                        #        # If right stick returns to the original position there is always an event that sets last_y_val back to zero. 
                        #        self.last_y_val = event.value
                        #        angular_velocity_y = float(self.gyro_device.getRotationY()[0] / 32768.0 * 2000)
                        #        adjusted_val = max(min(int(angular_velocity_y * self.gyro_sensitivity) + event.value, JOY_MAX), JOY_MIN)
    
                        #    if adjusted_val:
                        #        # Overwrite the event.
                        #        event = InputEvent(event.sec, event.usec, event.type, event.code, adjusted_val)
    
                        # Output the event.
                        await self.emit_events([event])
                except Exception as err:
                    self.logger.error(f"{err} | Error reading events from {self.controller_device.name}.")
                    self.restore_controller()
                    self.controller_device = None
                    self.controller_event = None
                    self.controller_path = None
            else:
                self.logger.info("Attempting to grab controller device...")
                self.get_controller()
                await asyncio.sleep(DETECT_DELAY)
    
    
    # Captures gyro events and translates them to joystick events.
    # TODO: Add mouse mode.
    #async def capture_gyro_events(self):
    #    self.logger.debug(f"capture_gyro_events, {self.running}")
    #    while self.running:
    #        # Only run this loop if gyro is enabled
    #        if self.gyro_device: 
    #            if self.gyro_enabled:
    #                # Periodically output the EV_ABS events according to the gyro readings.
    #                angular_velocity_x = float(self.gyro_device.getRotationX()[0] / 32768.0 * 2000)
    #                adjusted_x = max(min(int(angular_velocity_x * self.gyro_sensitivity) + self.last_x_val, JOY_MAX), JOY_MIN)
    #                x_event = InputEvent(0, 0, e.EV_ABS, e.ABS_RX, adjusted_x)
    #                angular_velocity_y = float(self.gyro_device.getRotationY()[0] / 32768.0 * 2000)
    #                adjusted_y = max(min(int(angular_velocity_y * self.gyro_sensitivity) + self.last_y_val, JOY_MAX), JOY_MIN)
    #                y_event = InputEvent(0, 0, e.EV_ABS, e.ABS_RY, adjusted_y)
    #
    #                await self.emit_events([x_event])
    #                await self.emit_events([y_event])
    #                await asyncio.sleep(0.01)
    #
    #            else:
    #                # Slow down the loop so we don't waste millions of cycles and overheat our controller.
    #                await asyncio.sleep(0.5)
    #
    #        else:
    #            if self.gyro_device == None:
    #                self.get_gyro()
    #            
    #            elif self.gyro_device == False:
    #                break
    
    
    # Captures power events and handles long or short press events.
    async def capture_power_events(self):
        while self.running:
            if self.power_device:
                try:
                    async for event in self.power_device.async_read_loop():
                        self.logger.debug(f"Got event: {event.type} | {event.code} | {event.value}")
                        #active_keys = keyboard_device.active_keys()
                        if event.type == e.EV_KEY and event.code == 116: # KEY_POWER
                            if event.value == 0:
                                #if active_keys == [125]: # KEY_LEFTMETA
                                #    # For DeckUI Sessions
                                #    shutdown = True
                                #    steam_ifrunning_deckui("steam://longpowerpress")
                                #else:
                                    # For DeckUI Sessions
                                is_deckui = self.steam_ifrunning_deckui("steam://shortpowerpress")
                                if not is_deckui:
                                    # For BPM and Desktop sessions
                                    os.system('systemctl suspend')
    
                        #if active_keys == [125]:
                        #    await do_rumble(0, 150, 1000, 0)
                
                except Exception as err:
                    self.logger.error(f"{err} | Error reading events from power device.")
                    self.power_device = None
            else:
                self.logger.info("Attempting to grab power device...")
                self.get_powerkey()
                await asyncio.sleep(DETECT_DELAY)
    
    
    # Handle FF event uploads
    async def capture_ff_events(self):
        ff_effect_id_set = set()
    
        async for event in self.ui_device.async_read_loop():
            if self.controller_device is None:
                # Slow down the loop so we don't waste millions of cycles and overheat our controller.
                await asyncio.sleep(.5)
                continue
    
            if event.type == e.EV_FF:
                # Forward FF event to controller.
                self.controller_device.write(e.EV_FF, event.code, event.value)
                continue
    
            # Programs will submit these EV_UINPUT events to ensure the device is capable.
            # Doing this forever doesn't seem to pose a problem, and attempting to ignore
            # any of them causes the program to halt.
            if event.type != e.EV_UINPUT:
                continue
    
            if event.code == e.UI_FF_UPLOAD:
                # Upload to the virtual device to prevent threadlocking. This does nothing else
                upload = self.ui_device.begin_upload(event.value)
                effect = upload.effect
    
                if effect.id not in ff_effect_id_set:
                    effect.id = -1 # set to -1 for kernel to allocate a new id. all other values throw an error for invalid input.
    
                try:
                    # Upload to the actual controller.
                    effect_id = self.controller_device.upload_effect(effect)
                    effect.id = effect_id
    
                    ff_effect_id_set.add(effect_id)
    
                    upload.retval = 0
                except IOError as err:
                    self.logger.error(f"{err} | Error uploading effect {effect.id}.")
                    upload.retval = -1
                
                self.ui_device.end_upload(upload)
    
            elif event.code == e.UI_FF_ERASE:
                erase = self.ui_device.begin_erase(event.value)
    
                try:
                    self.controller_device.erase_effect(erase.effect_id)
                    ff_effect_id_set.remove(erase.effect_id)
                    erase.retval = 0
                except IOError as err:
                    self.logger.error(f"{err} | Error erasing effect {erase.effect_id}.")
                    erase.retval = -1
    
                self.ui_device.end_erase(erase)
    
    
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
        if type(event_list[0]) == str and value == 0:
            self.logger.debug("Received string event with value 0. KEY_UP event not required. Skipping")
            return

        self.logger.debug(f'Event list: {event_list}')
        events = []

        if value == 0:
            for button_event in reversed(event_list):
                new_event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], value)
                events.append(new_event)
        else:
            for button_event in event_list:
                match button_event:
                    case "RyzenAdj Toggle":
                        self.logger.debug("RyzenAdj Toggle")
                        await self.toggle_performance()
                    case "Open Chimera":
                        self.logger.debug("Open Chimera")
                        self.launch_chimera()
                    case _:
                        new_event = InputEvent(seed_event.sec, seed_event.usec, button_event[0], button_event[1], value)
                        events.append(new_event)

        if events != []:
            await self.emit_events(events)
    
    
    # Toggles enable/disable gyro input and do FF event to notify user of status.
    #async def toggle_gyro(self):
    #    self.gyro_enabled = not self.gyro_enabled
    #    if self.gyro_enabled:
    #        await self.do_rumble(0, 250, 1000, 0)
    #    else:
    #        await self.do_rumble(0, 100, 1000, 0)
    #        await asyncio.sleep(FF_DELAY)
    #        await self.do_rumble(0, 100, 1000, 0)
    
    
    # RYZENADJ
    async def toggle_performance(self):
        if not self.transport:
            return
    
        if self.performance_mode == "--max-performance":
            self.performance_mode = "--power-saving"
            await self.do_rumble(0, 75, 1000, 0)
            await asyncio.sleep(FF_DELAY)
            await self.do_rumble(0, 75, 1000, 0)
            await asyncio.sleep(FF_DELAY)
            await self.do_rumble(0, 75, 1000, 0)
        else:
            self.performance_mode = "--max-performance"
            await self.do_rumble(0, 500, 1000, 0)
            await asyncio.sleep(FF_DELAY)
            await self.do_rumble(0, 75, 1000, 0)
            await asyncio.sleep(FF_DELAY)
            await self.do_rumble(0, 75, 1000, 0)
    
        self.transport.write(bytes(self.performance_mode, 'utf-8'))
        self.transport.close()
        self.transport = None
        self.protocol = None
    
    
    async def ryzenadj_control(self):
        while self.running:
            # Wait for a server to be launched
            if not os.path.exists(server_address):
                await asyncio.sleep(self.RYZENADJ_DELAY)
                continue
    
            # Wait for a connection to the server
            if not self.transport or not self.protocol:
                try:
                    self.transport, self.protocol = await self.loop.create_unix_connection(asyncio.Protocol, path=server_address)
                    self.logger.debug(f"got {self.transport}, {self.protocol}")
                except ConnectionRefusedError:
                    self.logger.debug('Could not connect to RyzenaAdj Control')
                    await asyncio.sleep(self.RYZENADJ_DELAY)
                    continue
            await asyncio.sleep(self.RYZENADJ_DELAY)
    
    
    def steam_ifrunning_deckui(self, cmd):
        # Get the currently running Steam PID.
        steampid_path = self.HOME_PATH + '/.steam/steam.pid'
        try:
            with open(steampid_path) as f:
                pid = f.read().strip()
        except Exception as err:
            self.logger.error(f"{err} | Error getting steam PID.")
            return False
    
        # Get the andline for the Steam process by checking /proc.
        steam_cmd_path = f"/proc/{pid}/cmdline"
        if not os.path.exists(steam_cmd_path):
            # Steam not running.
            return False
    
        try:
            with open(steam_cmd_path, "rb") as f:
                steam_cmd = f.read()
        except Exception as err:
            self.logger.error(f"{err} | Error getting steam cmdline.")
            return False
    
        # Use this andline to determine if Steam is running in DeckUI mode.
        # e.g. "steam://shortpowerpress" only works in DeckUI.
        is_deckui = b"-gamepadui" in steam_cmd
        if not is_deckui:
            return False
    
        steam_path = self.HOME_PATH + '/.steam/root/ubuntu12_32/steam'
        try:
            result = subprocess.run(["su", self.USER, "-c", f"{steam_path} -ifrunning {cmd}"])
            return result.returncode == 0
        except Exception as err:
            self.logger.error(f"{err} | Error sending and to Steam.")
            return False
    
    
    def launch_chimera(self):
        if not self.HAS_CHIMERA_LAUNCHER:
            return
        subprocess.run([ "su", self.USER, "-c", CHIMERA_LAUNCHER_PATH ])
    
    
    # Gracefull shutdown.
    async def restore_all(self):
        self.logger.info("Receved exit signal. Restoring devices.")
        self.running = False
    
        if self.controller_device:
            try:
                self.controller_device.ungrab()
            except IOError as err:
                self.logger.warn(f"{err} | Device wasn't grabbed.")
            self.restore_controller()
        if self.keyboard_device:
            try:
                self.keyboard_device.ungrab()
            except IOError as err:
                self.logger.warn(f"{err} | Device wasn't grabbed.")
            self.restore_keyboard()
        if self.power_device and self.CAPTURE_POWER:
            try:
                self.power_device.ungrab()
            except IOError as err:
                self.logger.warn(f"{err} | Device wasn't grabbed.")
        if self.power_device_2 and self.CAPTURE_POWER:
            try:
                self.power_device_2.ungrab()
            except IOError as err:
                self.logger.warn(f"{err} | Device wasn't grabbed.")
        self.logger.info("Devices restored.")
    
        # Kill all tasks. They are infinite loops so we will wait forver.
        for task in [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.loop.stop()
        self.logger.info("Handheld Game Console Controller Service stopped.")
    
    
    def restore_keyboard(self):
        # Both devices threads will attempt this, so ignore if they have been moved.
        try:
            move(str(HIDE_PATH / self.keyboard_event), self.keyboard_path)
        except FileNotFoundError:
            pass
    
    
    def restore_keyboard_2(self):
        # Both devices threads will attempt this, so ignore if they have been moved.
        try:
            move(str(HIDE_PATH / self.keyboard_2_event), self.keyboard_2_path)
        except FileNotFoundError:
            pass
    
    
    def restore_controller(self):
        # Both devices threads will attempt this, so ignore if they have been moved.
        try:
            move(str(HIDE_PATH / self.controller_event), self.controller_path)
        except FileNotFoundError:
            pass

def main():
    handycon = HandheldController()

