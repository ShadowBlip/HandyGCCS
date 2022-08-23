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
import subprocess
import warnings

from evdev import InputDevice, InputEvent, UInput, ecodes as e, list_devices, ff, AbsInfo
from pathlib import PurePath as p
from shutil import move
from time import sleep, time

warnings.filterwarnings("ignore", category=DeprecationWarning)
# Declare global variables

# Constants
EVENT_OSK = [[e.EV_KEY, e.BTN_MODE], [e.EV_KEY, e.BTN_NORTH]]
EVENT_ESC = [[e.EV_MSC, e.MSC_SCAN], [e.EV_KEY, e.KEY_ESC]]
EVENT_QAM = [[e.EV_KEY, e.BTN_MODE], [e.EV_KEY, e.BTN_SOUTH]]
EVENT_SCR = [[e.EV_KEY, e.BTN_MODE], [e.EV_KEY, e.BTN_TR]]
EVENT_HOME = [[e.EV_KEY, e.BTN_MODE]]

CONTROLLER_EVENTS = {
    e.EV_KEY: [
        e.KEY_ESC,
        e.KEY_1,
        e.KEY_2,
        e.KEY_3,
        e.KEY_4,
        e.KEY_5,
        e.KEY_6,
        e.KEY_7,
        e.KEY_8,
        e.KEY_9,
        e.KEY_0,
        e.KEY_MINUS,
        e.KEY_EQUAL,
        e.KEY_BACKSPACE,
        e.KEY_TAB,
        e.KEY_Q,
        e.KEY_W,
        e.KEY_E,
        e.KEY_R,
        e.KEY_T,
        e.KEY_Y,
        e.KEY_U,
        e.KEY_I,
        e.KEY_O,
        e.KEY_P,
        e.KEY_LEFTBRACE,
        e.KEY_RIGHTBRACE,
        e.KEY_ENTER,
        e.KEY_LEFTCTRL,
        e.KEY_A,
        e.KEY_S,
        e.KEY_D,
        e.KEY_F,
        e.KEY_G,
        e.KEY_H,
        e.KEY_J,
        e.KEY_K,
        e.KEY_L,
        e.KEY_SEMICOLON,
        e.KEY_APOSTROPHE,
        e.KEY_GRAVE,
        e.KEY_LEFTSHIFT,
        e.KEY_BACKSLASH,
        e.KEY_Z,
        e.KEY_X,
        e.KEY_C,
        e.KEY_V,
        e.KEY_B,
        e.KEY_N,
        e.KEY_M,
        e.KEY_COMMA,
        e.KEY_DOT,
        e.KEY_SLASH,
        e.KEY_RIGHTSHIFT,
        e.KEY_KPASTERISK,
        e.KEY_LEFTALT,
        e.KEY_SPACE,
        e.KEY_CAPSLOCK,
        e.KEY_F1,
        e.KEY_F2,
        e.KEY_F3,
        e.KEY_F4,
        e.KEY_F5,
        e.KEY_F6,
        e.KEY_F7,
        e.KEY_F8,
        e.KEY_F9,
        e.KEY_F10,
        e.KEY_NUMLOCK,
        e.KEY_SCROLLLOCK,
        e.KEY_KP7,
        e.KEY_KP8,
        e.KEY_KP9,
        e.KEY_KPMINUS,
        e.KEY_KP4,
        e.KEY_KP5,
        e.KEY_KP6,
        e.KEY_KPPLUS,
        e.KEY_KP1,
        e.KEY_KP2,
        e.KEY_KP3,
        e.KEY_KP0,
        e.KEY_KPDOT,
        e.KEY_ZENKAKUHANKAKU,
        e.KEY_102ND,
        e.KEY_F11,
        e.KEY_F12,
        e.KEY_RO,
        e.KEY_KATAKANA,
        e.KEY_HIRAGANA,
        e.KEY_HENKAN,
        e.KEY_KATAKANAHIRAGANA,
        e.KEY_MUHENKAN,
        e.KEY_KPJPCOMMA,
        e.KEY_KPENTER,
        e.KEY_RIGHTCTRL,
        e.KEY_KPSLASH,
        e.KEY_SYSRQ,
        e.KEY_RIGHTALT,
        e.KEY_HOME,
        e.KEY_UP,
        e.KEY_PAGEUP,
        e.KEY_LEFT,
        e.KEY_RIGHT,
        e.KEY_END,
        e.KEY_DOWN,
        e.KEY_PAGEDOWN,
        e.KEY_INSERT,
        e.KEY_DELETE,
        e.KEY_MACRO,
        e.KEY_MUTE,
        e.KEY_VOLUMEDOWN,
        e.KEY_VOLUMEUP,
        e.KEY_POWER,
        e.KEY_KPEQUAL,
        e.KEY_KPPLUSMINUS,
        e.KEY_PAUSE,
        e.KEY_KPCOMMA,
        e.KEY_HANGUEL,
        e.KEY_HANJA,
        e.KEY_YEN,
        e.KEY_LEFTMETA,
        e.KEY_RIGHTMETA,
        e.KEY_COMPOSE,
        e.KEY_STOP,
        e.KEY_CALC,
        e.KEY_SLEEP,
        e.KEY_WAKEUP,
        e.KEY_MAIL,
        e.KEY_BOOKMARKS,
        e.KEY_COMPUTER,
        e.KEY_BACK,
        e.KEY_FORWARD,
        e.KEY_NEXTSONG,
        e.KEY_PLAYPAUSE,
        e.KEY_PREVIOUSSONG,
        e.KEY_STOPCD,
        e.KEY_HOMEPAGE,
        e.KEY_REFRESH,
        e.KEY_F13,
        e.KEY_F14,
        e.KEY_F15,
        e.KEY_SEARCH,
        e.KEY_MEDIA,
        e.BTN_SOUTH,
        e.BTN_EAST,
        e.BTN_NORTH,
        e.BTN_WEST,
        e.BTN_TL,
        e.BTN_TR,
        e.BTN_SELECT,
        e.BTN_START,
        e.BTN_MODE,
        e.BTN_THUMBL,
        e.BTN_THUMBR,
    ],
    e.EV_ABS: [
        (e.ABS_X, AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_Y, AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_Z, AbsInfo(0, 0, 255, 0, 0, 0)),
        (e.ABS_RX, AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_RY, AbsInfo(0, -32768, 32767, 16, 128, 0)),
        (e.ABS_RZ, AbsInfo(0, 0, 255, 0, 0, 0)),
        (e.ABS_HAT0X, AbsInfo(0, -1, 1, 0, 0, 0)),
        (e.ABS_HAT0Y, AbsInfo(0, -1, 1, 0, 0, 0)),
    ],
    e.EV_MSC: [
        e.MSC_SCAN,
    ],
    e.EV_LED: [
        e.LED_NUML,
        e.LED_CAPSL,
        e.LED_SCROLLL,
    ],
    e.EV_FF: [
        e.FF_RUMBLE,
        e.FF_PERIODIC,
        e.FF_SQUARE,
        e.FF_TRIANGLE,
        e.FF_SINE,
        e.FF_GAIN,
    ],
}

JOY_MIN = -32767
JOY_MAX = 32767

HIDE_PATH = "/dev/input/.hidden/"
USER = None
cmd = "who | awk '{print $1}' | sort | head -1"
while USER == None:
    USER_LIST = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
    for get_first in USER_LIST.stdout:
        name = get_first.decode().strip()
        if name is not None:
            USER = name
        break
    sleep(.1)
HOME_PATH = "/home/"+USER

# Functionality Variables
event_queue = [] # Stores incoming button presses to block spam
controller_events = [] # Stores incoming events if gyro aim is enabled.
running = True
shutdown = False

# Devices
controller_device = None
gyro_device = None
keyboard_device = None
ui_device = None
power_device = None
system_type = None
last_time = time()

try :
    from BMI160_i2c import Driver
except ModuleNotFoundError:
        print("BMI160_i2c Module was not found. Install with `python3 -m pip install BMI160-i2c`. Skipping gyro device.")
        gyro_device = False
# Paths
controller_event = None
controller_path = None
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
gyro_enabled = False
gyro_sensitivity = 50

def __init__():

    global controller_device
    global HIDE_PATH
    global keyboard_device
    global power_device

    id_system()
    os.makedirs(HIDE_PATH, exist_ok=True)
    make_controller()

def id_system():
    global system_type

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

    # ONE XPLAYER devices. Original BIOS have incomplete DMI data and all models report as
    # "ONE XPLAYER". OXP have provided new DMI data via BIOS updates.
    elif system_id in [
            "ONE XPLAYER",
            "ONEXPLAYER 1 T08",
            "ONEXPLAYER 1S A08",
            "ONEXPLAYER 1S T08",
            "ONEXPLAYER mini A07",
            "ONEXPLAYER mini GA72",
            "ONEXPLAYER mini GT72",
            "ONEXPLAYER GUNDAM GA72",
            "ONEXPLAYER 2 ARP23",
            ]:

            system_type = "OXP"

    # Block devices that aren't supported as this could cause issues.
    else:
        print(system_id, "is not currently supported by this tool. Open an issue on \
GitHub at https://github.com/ShadowBlip/aya-neo-fixes if this is a bug. If possible, \
please run the capture-system.py utility found on the GitHub repository and upload \
that file with your issue.")
        exit(1)

def get_controller():
    global controller_device
    global controller_event
    global controller_path
    global HIDE_PATH

    # Identify system input event devices.
    attempts = 0
    while attempts < 3:
        try:
            devices_original = [InputDevice(path) for path in list_devices()]
        # Some funky stuff happens sometimes when booting. Give it another shot.
        except Exception as err:
            attempts += 1
            sleep(.25)
            continue

        controller_names = [
                'Microsoft X-Box 360 pad',
                'Generic X-Box pad',
                ]
        controller_phys =[
                'usb-0000:03:00.3-4/input0',
                'usb-0000:04:00.3-4/input0',
                'usb-0000:00:14.0-9/input0',
                ]

        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in devices_original:
            if device.name in controller_names and device.phys in controller_phys:
                controller_path = device.path
                controller_device = InputDevice(controller_path)
                controller_device.grab()
                controller_event = p(controller_path).name
                move(controller_path, HIDE_PATH+controller_event)
                break

        # Sometimes the service loads before all input devices have full initialized. Try a few times.
        if not controller_device:
            print("Unable to find controller device. Attempt", attempts, "of 3.")
            attempts += 1
            sleep(.25)
        else:
            print("Found", controller_device.name+".", "Capturing input data.")
            break

def get_keyboard():
    global keyboard_device
    global keyboard_event
    global keyboard_path
    global HIDE_PATH

    # Identify system input event devices.
    attempts = 0
    while attempts < 3:
        try:
            devices_original = [InputDevice(path) for path in list_devices()]
        # Some funky stuff happens sometimes when booting. Give it another shot.
        except Exception as err:
            attempts += 1
            sleep(.25)
            continue

        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in devices_original:
            if device.name == 'AT Translated Set 2 keyboard' and device.phys == 'isa0060/serio0/input0':
                keyboard_path = device.path
                keyboard_device = InputDevice(keyboard_path)
                keyboard_device.grab()
                keyboard_event = p(keyboard_path).name
                move(keyboard_path, HIDE_PATH+keyboard_event)
                break

        # Sometimes the service loads before all input devices have full initialized. Try a few times.
        if not keyboard_device:
            print("Unable to find keyboard device. Attempt", attempts, "of 3.")
            attempts += 1
            sleep(.25)
        else:
            print("Found", keyboard_device.name+".", "Capturing input data.")
            break

def get_powerkey():
    global power_device

    # Identify system input event devices.
    attempts = 0
    while attempts < 3:
        try:
            devices_original = [InputDevice(path) for path in list_devices()]
        # Some funky stuff happens sometimes when booting. Give it another shot.
        except Exception as err:
            attempts += 1
            sleep(.25)
            continue

        # Grab the built-in devices. This will give us exclusive acces to the devices and their capabilities.
        for device in devices_original:

            # Power Button
            if device.name == 'Power Button' and device.phys == "LNXPWRBN/button/input0":
                power_device = device
                power_device.grab()
                break

        if not power_device:
            attempts += 1
            sleep(.25)
        else:
            print("Found", power_device.name+".", "Capturing input data.")
            break

def get_gyro():
    global gyro_device
    # Make a gyro_device, if it exists.
    try:
        gyro_device = Driver(0x68)
        print("Found gyro device. Gyro support enabled.")

    except (FileNotFoundError, NameError, BrokenPipeError, OSError) as err:
        print("Gyro device not initialized. Ensure bmi160_i2c and i2c_dev modules are loaded, and all python dependencies are met. Skipping gyro device setup.\n", err)
        gyro_device=False

def make_controller():
    global ui_device

    # Create the virtual controller.
    ui_device = UInput(
            CONTROLLER_EVENTS,
            name='Handheld Controller',
            bustype=int('3', base=16),
            vendor=int('045e', base=16),
            product=int('028e', base=16),
            version=int('110', base=16)
            )

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
    await asyncio.sleep(interval/1000)
    controller_device.erase_effect(effect_id)

# Captures keyboard events and translates them to virtual device events.
async def capture_keyboard_events():

    # Get access to global variables. These are globalized because the function
    # is instanciated twice and need to persist accross both instances.
    global button_map
    global event_queue
    global gyro_device
    global gyro_enabled
    global keyboard_device
    global shutdown

    # Button map shortcuts for easy reference.
    button1 = button_map["button1"]
    button2 = button_map["button2"]
    button3 = button_map["button3"]
    button4 = button_map["button4"]
    button5 = button_map["button5"]
    last_button = None

    # Capture keyboard events and translate them to mapped events.
    while running:
        if keyboard_device:
            try:
                async for seed_event in keyboard_device.async_read_loop():

                    # Loop variables
                    active = keyboard_device.active_keys()
                    events = []
                    this_button = None
                    button_on = seed_event.value

                    # Debugging variables
                    #if active != []:
                    #   print("Active Keys:", keyboard_device.active_keys(verbose=True), "Seed Value", seed_event.value, "Seed Code:", seed_event.code, "Seed Type:", seed_event.type, "Button pressed", button_on)
                    # Automatically pass default keycodes we dont intend to replace.
                    if seed_event.code in [e.KEY_VOLUMEDOWN, e.KEY_VOLUMEUP]:
                        events.append(seed_event)
                    match system_type:

                        case "AYA_GEN1":
                            # BUTTON 1 (Default: Screenshot) WIN button
                            if active == [125] and button_on == 1 and button1 not in event_queue and shutdown == False:
                                event_queue.append(button1)
                            elif active == [] and seed_event.code == 125 and button_on == 0 and button1 in event_queue:
                                this_button = button1

                            # BUTTON 2 (Default: QAM) TM Button
                            if active == [97, 100, 111] and button_on == 1 and button2 not in event_queue:
                                event_queue.append(button2)
                            elif active == [] and seed_event.code in [97, 100, 111] and button_on == 0 and button2 in event_queue:
                                this_button = button2
                                await do_rumble(0, 150, 1000, 0)

                            # BUTTON 3 (Default: ESC) ESC Button
                            if active == [1] and seed_event.code == 1 and button_on == 1 and button3 not in event_queue:
                                event_queue.append(button3)
                            elif active == [] and seed_event.code == 1 and button_on == 0 and button3 in event_queue:
                                this_button = button3
                            # BUTTON 3 SECOND STATE (Default: Toggle Gyro)
                            elif seed_event.code == 1 and button_on == 2 and button3 in event_queue and gyro_device:
                                event_queue.remove(button3)
                                gyro_enabled = not gyro_enabled
                                if gyro_enabled:
                                    await do_rumble(0, 250, 1000, 0)
                                else:
                                    await do_rumble(0, 100, 1000, 0)
                                    await asyncio.sleep(.2)
                                    await do_rumble(0, 100, 1000, 0)

                            # BUTTON 4 (Default: OSK) KB Button
                            if active == [24, 97, 125] and button_on == 1 and button4 not in event_queue:
                                event_queue.append(button4)
                            elif active == [] and seed_event.code in [24, 97, 125] and button_on == 0 and button4 in event_queue:
                                this_button = button4

                            # Handle L_META from power button
                            elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
                                shutdown = False

                        case "AYA_GEN2":
                            # BUTTON 1 (Default: Screenshot) LC Button
                            if active == [87, 97, 125] and button_on == 1 and button1 not in event_queue and shutdown == False:
                                event_queue.append(button1)
                            elif active == [] and seed_event.code in [87, 97, 125] and button_on == 0 and button1 in event_queue:
                                this_button = button1

                            # BUTTON 2 (Default: QAM) Small button
                            if active in [[40, 133], [32, 125]] and button_on == 1 and button2 not in event_queue:
                                event_queue.append(button2)
                            elif active == [] and seed_event.code in [32, 40, 125, 133] and button_on == 0 and button2 in event_queue:
                                this_button = button2
                                await do_rumble(0, 150, 1000, 0)

                            # BUTTON 3 (Default: Toggle Gyro) RC + LC Buttons
                            if active == [68, 87, 97, 125] and button_on == 1 and button3 not in event_queue and gyro_device:
                                event_queue.append(button3)
                                if button1 in event_queue:
                                    event_queue.remove(button1)
                                if button4 in event_queue:
                                    event_queue.remove(button4)

                            elif active == [] and seed_event.code in [68, 87, 97, 125] and button_on == 0 and button3 in event_queue and gyro_device:
                                event_queue.remove(button3)
                                gyro_enabled = not gyro_enabled
                                if gyro_enabled:
                                    await do_rumble(0, 250, 1000, 0)
                                else:
                                    await do_rumble(0, 100, 1000, 0)
                                    await asyncio.sleep(.2)
                                    await do_rumble(0, 100, 1000, 0)

                            # BUTTON 4 (Default: OSK) RC Button
                            if active == [68, 97, 125] and button_on == 1 and button4 not in event_queue:
                                event_queue.append(button4)
                            elif active == [] and seed_event.code in [68, 97, 125] and button_on == 0 and button4 in event_queue:
                                this_button = button4

                            # BUTTON 5 (Default: Home) Big button
                            if active in [[96, 105, 133], [88, 97, 125]] and button_on == 1 and button5 not in event_queue:
                                event_queue.append(button5)
                            elif active == [] and seed_event.code in [88, 96, 97, 105, 125, 133] and button_on == 0 and button5 in event_queue:
                                this_button = button5

                            # Handle L_META from power button
                            elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
                                shutdown = False

                        case "OXP":
                            # BUTTON 1 (Default: Not used, dangerous fan activity!) Short press orange + |||||
                            if active == [99, 125] and button_on == 1 and button1 not in event_queue:
                                pass
                            elif active == [] and seed_event.code in [99, 125] and button_on == 0 and button1 in event_queue:
                                pass

                            # BUTTON 2 (Default: QAM) Short press orange
                            if active == [32, 125] and button_on == 1 and button2 not in event_queue:
                                event_queue.append(button2)
                            elif active == [] and seed_event.code in [32, 125] and button_on == 0 and button2 in event_queue:
                                this_button = button2
                                await do_rumble(0, 150, 1000, 0)

                            # BUTTON 3 (Default: Toggle Gyro) Short press orange + KB
                            if active == [97, 100, 111] and button_on == 1 and button3 not in event_queue and gyro_device:
                                event_queue.append(button3)
                            elif active == [] and seed_event.code in [100, 111] and button_on == 0 and button3 in event_queue and gyro_device:
                                event_queue.remove(button3)
                                gyro_enabled = not gyro_enabled
                                if gyro_enabled:
                                    await do_rumble(0, 250, 1000, 0)
                                else:
                                    await do_rumble(0, 100, 1000, 0)
                                    await asyncio.sleep(.2)
                                    await do_rumble(0, 100, 1000, 0)

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

                            # Handle L_META from power button
                            elif active == [] and seed_event.code == 125 and button_on == 0 and  event_queue == [] and shutdown == True:
                                shutdown = False

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

            except Exception as err:
                print("Error reading events from", keyboard_device.name+".", err)
                restore_keyboard()
                keyboard_device = None
                keyboard_event = None
                keyboard_path = None
        else:
            print("Keyboard lost. Attempting to grab device...")
            get_keyboard()
            await asyncio.sleep(.25)

# Captures the controller_device events and passes them through.
async def capture_controller_events():
    global controller_device
    global controller_events

    while running:
        if controller_device:
            try:
                async for event in controller_device.async_read_loop():
                    # If gyro is enabled, queue all events so the gyro event handler can manage them.
                    if gyro_enabled:
                        if event.type not in [e.EV_FF, e.EV_UINPUT]:
                            controller_events.append(event)

                    # If gyro isn't enabled, emit the event. Also block FF events, or get infinite recursion. Up to you I guess...
                    else:
                        if event.type not in [e.EV_FF, e.EV_UINPUT]:
                            await emit_events([event])
            except Exception as err:
                print("Error reading events from", controller_device.name+".", err)
                restore_controller()
                controller_device = None
                controller_event = None
                controller_path = None
        else:
            print("Controller lost. Attempting to grab device...")
            get_controller()
            await asyncio.sleep(.25)

async def capture_gyro_events():

    global controller_events
    global gyro_device
    global gyro_enabled

    # Holding the last value allows us to maintain motion while a joystick is held.
    last_x_val = 0
    last_y_val = 0

    while running:
        # Only run this loop if gyro is enabled
        if gyro_device:
            if gyro_enabled:
                # Check if there is a controller event and modify it, otherwise pass the event:
                if controller_events != []:
                    for event in controller_events:
                        if event.type == e.EV_FF:
                            continue
                        adjusted_val = None
                        seed_event = event
                        controller_events.remove(event)

                        # We only modify RX/RY ABS events.
                        if seed_event.type == e.EV_ABS and seed_event.code == e.ABS_RX:
                            angular_velocity_x = float(gyro_device.getRotationX()[0] / 32768.0 * 2000)
                            adjusted_val = max(min(int(angular_velocity_x * gyro_sensitivity) + event.value, JOY_MAX), JOY_MIN)
                            event = InputEvent(seed_event.sec, seed_event.usec, seed_event.type, seed_event.code, adjusted_val)
                            last_x_val = adjusted_val
                        if event.type == e.EV_ABS and event.code == e.ABS_RY:
                            angular_velocity_y = float(gyro_device.getRotationY()[0] / 32768.0 * 2000)
                            adjusted_val = max(min(int(angular_velocity_y * gyro_sensitivity) + event.value, JOY_MAX), JOY_MIN)
                            last_y_val = adjusted_val
                        if adjusted_val:
                            event = InputEvent(seed_event.sec, seed_event.usec, seed_event.type, seed_event.code, adjusted_val)

                        # Output all events.
                        await emit_events([event])

                # If no input events we can just add an event with no modifying.
                else:
                    angular_velocity_x = float(gyro_device.getRotationX()[0] / 32768.0 * 2000)
                    adjusted_x = max(min(int(angular_velocity_x * gyro_sensitivity) + last_x_val, JOY_MAX), JOY_MIN)
                    x_event = InputEvent(0, 0, e.EV_ABS, e.ABS_RX, adjusted_x)
                    angular_velocity_y = float(gyro_device.getRotationY()[0] / 32768.0 * 2000)
                    adjusted_y = max(min(int(angular_velocity_y * gyro_sensitivity) + last_y_val, JOY_MAX), JOY_MIN)
                    y_event = InputEvent(0, 0, e.EV_ABS, e.ABS_RY, adjusted_y)
                    await emit_events([x_event, y_event])

                await asyncio.sleep(0.01)
            else:
                # Slow down the loop so we don't waste millions of cycles and overheat our controller.
                await asyncio.sleep(.5)
        else:
            if gyro_device == None:
                get_gyro()
            elif gyro_device == False:
                break

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
                                cmd = 'su {} -c "{}/.steam/root/ubuntu12_32/steam -ifrunning steam://longpowerpress"'.format(USER, HOME_PATH)
                                os.system(cmd)

                            else:
                                # For DeckUI Sessions
                                cmd = 'su {} -c "{}/.steam/root/ubuntu12_32/steam -ifrunning steam://shortpowerpress"'.format(USER, HOME_PATH)
                                os.system(cmd)

                                # For BPM and Desktop sessions
                                await asyncio.sleep(1)
                                os.system('systemctl suspend')

                    if active_keys == [125]:
                        await do_rumble(0, 150, 1000, 0)
            
            except Exception as err:
                print("Error reading events from power device", err)
                power_device = None
        else:
            print("Attempting to grab power device...")
            get_powerkey()
            await asyncio.sleep(.25)


# Handle FF event uploads
async def capture_ff_events():
    async for event in ui_device.async_read_loop():

        # Calculate our frametime so we can sleep the maximum possible without affecting framerate.
        global last_time

        time_now = time()
        time_delta = time_now - last_time
        last_time = time_now

        # Create upper bounds so we don't hang the system on slow frames
        if time_delta > 0.03:
            time_delta = 0.03

        # Programs will submit these EV_UINPUT events to ensure the device is capable.
        # Doing this forever doesn't seem to pose a problem, and attempting to ignore
        # any of them causes the program to halt.
        if event.type != e.EV_UINPUT:
            continue

        if event.code == e.UI_FF_UPLOAD:
            # Upload to the virtual device to prevent threadlocking. This does nothing else
            upload = ui_device.begin_upload(event.value)
            upload.retval = 0
            effect = upload.effect
            ui_device.end_upload(upload)

            # Don't crash if there is no controller.
            if not controller_device:
                continue

            # Upload to the actual controller.
            effect.id = -1 # all other values throw an error for invalid input.
            effect_id = controller_device.upload_effect(effect)
            controller_device.write(e.EV_FF, effect_id, 1)
            await asyncio.sleep(time_delta)
            controller_device.erase_effect(effect_id)

        elif event.code == e.UI_FF_ERASE:
            effect_id = ui_device.begin_erase(event.value)
            effect_id.retval = 0
            ui_device.end_erase(effect_id)

# Emits passed or generated events to the virtual controller.
async def emit_events(events: list):
    if len(events) == 1:
        ui_device.write_event(events[0])
        ui_device.syn()
    elif len(events) > 1:
        for event in events:
            if event:
                ui_device.write_event(event)
                ui_device.syn()
                await asyncio.sleep(0.09)

# Gracefull shutdown.
async def restore_all(loop):

    print('Receved exit signal. Restoring Devices.')
    running = False

    if controller_device:
        controller_device.ungrab()
        restore_controller()
    if keyboard_device:
        keyboard_device.ungrab()
        restore_keyboard()

    # Kill all tasks. They are infinite loops so we will wait forver.
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    loop.stop()
    print("Device restore complete. Handheld Game Console Controller Service Stopped...")

def restore_keyboard():
    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(HIDE_PATH+keyboard_event, keyboard_path)
    except FileNotFoundError:
        pass

def restore_controller():
    # Both devices threads will attempt this, so ignore if they have been moved.
    try:
        move(HIDE_PATH+controller_event, controller_path)
    except FileNotFoundError:
        pass

# Main loop
def main():

    # Attach the event loop of each device to the asyncio loop.
    asyncio.ensure_future(capture_controller_events())
    asyncio.ensure_future(capture_keyboard_events())
    asyncio.ensure_future(capture_ff_events())
    asyncio.ensure_future(capture_power_events())
    asyncio.ensure_future(capture_gyro_events())

    # Run asyncio loop to capture all events.
    loop = asyncio.get_event_loop()

    # Establish signaling to handle gracefull shutdown.
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT, signal.SIGQUIT)
    for s in signals:
        loop.add_signal_handler(s, lambda s=s: asyncio.create_task(restore_all(loop)))

    try:
        loop.run_forever()
    except Exception as e:
        print("Hit exception condition:\n", e)
    finally:
        loop.stop()

if __name__ == "__main__":
    __init__()
    main()
