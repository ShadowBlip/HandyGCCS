#!/usr/bin/env python3
# This file is part of Handheld Game Console Controller System (HandyGCCS)
# Copyright 2022-2023 Derek J. Clark <derekjohn.clark@gmail.com>

# Python Modules
import asyncio
import configparser
import os
import re
import subprocess
import sys
import traceback

## Local modules
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
import handycon.handhelds.ayn_gen3 as ayn_gen3
import handycon.handhelds.go_gen1 as go_gen1
import handycon.handhelds.gpd_gen1 as gpd_gen1
import handycon.handhelds.gpd_gen2 as gpd_gen2
import handycon.handhelds.gpd_gen3 as gpd_gen3
import handycon.handhelds.oxp_gen1 as oxp_gen1
import handycon.handhelds.oxp_gen2 as oxp_gen2
import handycon.handhelds.oxp_gen3 as oxp_gen3
import handycon.handhelds.oxp_gen4 as oxp_gen4
import handycon.handhelds.oxp_gen5 as oxp_gen5
import handycon.handhelds.oxp_gen6 as oxp_gen6
import handycon.handhelds.oxp_gen7 as oxp_gen7
from .constants import *

## Partial imports
from time import sleep

handycon = None
def set_handycon(handheld_controller):
    global handycon
    handycon = handheld_controller


# Capture the username and home path of the user who has been logged in the longest.
def get_user():
    global handycon

    handycon.logger.debug("Identifying user.")
    cmd = "who | awk '{print $1}' | sort | head -1"
    while handycon.USER is None:
        USER_LIST = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
        for get_first in USER_LIST.stdout:
            name = get_first.decode().strip()
            if name is not None:
                handycon.USER = name
            break
        sleep(1)

    handycon.logger.debug(f"USER: {handycon.USER}")
    handycon.HOME_PATH = "/home/" + handycon.USER
    handycon.logger.debug(f"HOME_PATH: {handycon.HOME_PATH}")


# Identify the current device type. Kill script if not atible.
def id_system():
    global handycon

    system_id = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()
    handycon.logger.debug(f"Found System ID: {system_id}")

    cpu_vendor = get_cpu_vendor()
    handycon.logger.debug(f"Found CPU Vendor: {cpu_vendor}")

    ## ANBERNIC Devices
    if system_id in (
            "Win600",
            ):
        handycon.system_type = "ANB_GEN1"
        anb_gen1.init_handheld(handycon)

    ## AOKZOE Devices
    elif system_id in (
        "AOKZOE A1 AR07",
        ):
        handycon.system_type = "AOK_GEN1"
        aok_gen1.init_handheld(handycon)

    elif system_id in (
        "AOKZOE A1 Pro",
        ):
        handycon.system_type = "AOK_GEN2"
        aok_gen2.init_handheld(handycon)


    ## ASUS Devices
    elif system_id in (
        "ROG Ally RC71L_RC71L",
        ):
        handycon.system_type = "ALY_GEN1"
        ally_gen1.init_handheld(handycon)

    ## Aya Neo Devices
    elif system_id in (
        "AYA NEO FOUNDER",
        "AYA NEO 2021",
        "AYANEO 2021",
        "AYANEO 2021 Pro",
        "AYANEO 2021 Pro Retro Power",
        ):
        handycon.system_type = "AYA_GEN1"
        aya_gen1.init_handheld(handycon)

    elif system_id in (
        "NEXT",
        "NEXT Pro",
        "NEXT Advance",
        "AYANEO NEXT",
        "AYANEO NEXT Pro",
        "AYANEO NEXT Advance",
        ):
        handycon.system_type = "AYA_GEN2"
        aya_gen2.init_handheld(handycon)

    elif system_id in (
        "AIR",
        "AIR Pro",
        ):
        handycon.system_type = "AYA_GEN3"
        aya_gen3.init_handheld(handycon)

    elif system_id in (
        "AYANEO 2",
        "GEEK",
        ):
        handycon.system_type = "AYA_GEN4"
        aya_gen4.init_handheld(handycon)

    elif system_id in (
        "AIR Plus",
        ):
        if cpu_vendor == "GenuineIntel":
            handycon.system_type = "AYA_GEN7"
            aya_gen7.init_handheld(handycon)
        else:
            handycon.system_type = "AYA_GEN5"
            aya_gen5.init_handheld(handycon)

    elif system_id in (
        "AYANEO 2S",
        "GEEK 1S",
        "AIR 1S",
        ):
        handycon.system_type = "AYA_GEN6"
        aya_gen6.init_handheld(handycon)

    ## Ayn Devices
    elif system_id in (
            "Loki Max",
        ):
        handycon.system_type = "AYN_GEN1"
        ayn_gen1.init_handheld(handycon)

    elif system_id in (
            "Loki Zero",
        ):
        handycon.system_type = "AYN_GEN2"
        ayn_gen2.init_handheld(handycon)

    elif system_id in (
            "Loki MiniPro",
        ):
        handycon.system_type = "AYN_GEN3"
        ayn_gen3.init_handheld(handycon)

    ## Lenovo Devices
    elif system_id in (
            "83E1", #Legion Go
        ):
        handycon.system_type = "GO_GEN1"
        go_gen1.init_handheld(handycon)

    ## GPD Devices
    # Have 2 buttons with 3 modes (left, right, both)
    elif system_id in (
        "G1618-03", #Win3
        ):
        handycon.system_type = "GPD_GEN1"
        gpd_gen1.init_handheld(handycon)

    elif system_id in (
        "G1619-04", #WinMax2
        ):
        handycon.system_type = "GPD_GEN2"
        gpd_gen2.init_handheld(handycon)

    elif system_id in (
        "G1618-04", #Win4
        ):
        handycon.system_type = "GPD_GEN3"
        gpd_gen3.init_handheld(handycon)

    ## ONEXPLAYER Devices
    # Older BIOS have incomlete DMI data and most models report as "ONE XPLAYER" or "ONEXPLAYER".
    elif system_id in (
        "ONE XPLAYER",
        "ONEXPLAYER",
        ):

        # GEN 1
        if cpu_vendor == "GenuineIntel":
            handycon.system_type = "OXP_GEN1"
            oxp_gen1.init_handheld(handycon)
        
        # GEN 2
        else:
            handycon.system_type = "OXP_GEN2"
            oxp_gen2.init_handheld(handycon)

    # GEN 3
    elif system_id in (
        "ONEXPLAYER mini A07",
        ):
        handycon.system_type = "OXP_GEN3"
        oxp_gen3.init_handheld(handycon)

    # GEN 4
    elif system_id in (
        "ONEXPLAYER Mini Pro",
        ):
        handycon.system_type = "OXP_GEN4"
        oxp_gen4.init_handheld(handycon)

    # GEN 5
    elif system_id in (
        "ONEXPLAYER 2 ARP23",
        ):
        handycon.system_type = "OXP_GEN5"
        oxp_gen5.init_handheld(handycon)

    # GEN 6
    elif system_id in (
        "ONEXPLAYER 2 PRO ARP23P",
        "ONEXPLAYER 2 PRO ARP23P EVA-01",
        ):
        handycon.system_type = "OXP_GEN6"
        oxp_gen6.init_handheld(handycon)

    # GEN 7
    elif system_id in (
        "ONEXPLAYER F1",
        ):
        handycon.system_type = "OXP_GEN7"
        oxp_gen7.init_handheld(handycon)

    # Devices that aren't supported could cause issues, exit.
    else:
        handycon.logger.error(f"{system_id} is not currently supported by this tool. Open an issue on \
ub at https://github.ShadowBlip/HandyGCCS if this is a bug. If possible, \
se run the capture-system.py utility found on the GitHub repository and upload \
the file with your issue.")
        sys.exit(0)
    handycon.logger.info(f"Identified host system as {system_id} and configured defaults for {handycon.system_type}.")


def get_cpu_vendor():
    global handycon

    cmd = "cat /proc/cpuinfo"
    all_info = subprocess.check_output(cmd, shell=True).decode().strip()
    for line in all_info.split("\n"):
        if "vendor_id" in line:
                return re.sub( ".*vendor_id.*:", "", line,1).strip()


def get_config():
    global handycon
    # Check for an existing config file and load it.
    handycon.config = configparser.ConfigParser()
    if os.path.exists(CONFIG_PATH):
        handycon.logger.info(f"Loading existing config: {CONFIG_PATH}")
        handycon.config.read(CONFIG_PATH)
        if not "power_button" in handycon.config["Button Map"]:
            handycon.logger.info("Config file out of date. Generating new config.")
            set_default_config()
            write_config()
    else:
        set_default_config()
        write_config()
    map_config()


# Match runtime variables to the config 
def map_config():
    # Assign config file values
    handycon.button_map = {
    "button1": EVENT_MAP[handycon.config["Button Map"]["button1"]],
    "button2": EVENT_MAP[handycon.config["Button Map"]["button2"]],
    "button3": EVENT_MAP[handycon.config["Button Map"]["button3"]],
    "button4": EVENT_MAP[handycon.config["Button Map"]["button4"]],
    "button5": EVENT_MAP[handycon.config["Button Map"]["button5"]],
    "button6": EVENT_MAP[handycon.config["Button Map"]["button6"]],
    "button7": EVENT_MAP[handycon.config["Button Map"]["button7"]],
    "button8": EVENT_MAP[handycon.config["Button Map"]["button8"]],
    "button9": EVENT_MAP[handycon.config["Button Map"]["button9"]],
    "button10": EVENT_MAP[handycon.config["Button Map"]["button10"]],
    "button11": EVENT_MAP[handycon.config["Button Map"]["button11"]],
    "button12": EVENT_MAP[handycon.config["Button Map"]["button12"]],
    }
    handycon.power_action = POWER_ACTION_MAP[handycon.config["Button Map"]["power_button"]][0]


# Sets the default configuration.
def set_default_config():
    global handycon
    handycon.config["Button Map"] = {
            "button1": "SCR",
            "button2": "QAM",
            "button3": "ESC",
            "button4": "OSK",
            "button5": "MODE",
            "button6": "OPEN_CHIMERA",
            "button7": "TOGGLE_PERFORMANCE",
            "button8": "MODE",
            "button9": "TOGGLE_MOUSE",
            "button10": "ALT_TAB",
            "button11": "KILL",
            "button12": "TOGGLE_GYRO",
            "power_button": "SUSPEND",
            }


# Writes current config to disk.
def write_config():
    global handycon
    # Make the HandyGCCS directory if it doesn't exist.
    if not os.path.exists(CONFIG_DIR):
        os.mkdir(CONFIG_DIR)

    with open(CONFIG_PATH, 'w') as config_file:
        handycon.config.write(config_file)
        handycon.logger.info(f"Created new config: {CONFIG_PATH}")


def steam_ifrunning_deckui(cmd):
    global handycon

    # Get the currently running Steam PID.
    steampid_path = handycon.HOME_PATH + '/.steam/steam.pid'
    try:
        with open(steampid_path) as f:
            pid = f.read().strip()
    except Exception as err:
        handycon.logger.error(f"{err} | Error getting steam PID.")
        handycon.logger.error(traceback.format_exc())
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
        handycon.logger.error(f"{err} | Error getting steam cmdline.")
        handycon.logger.error(traceback.format_exc())
        return False 

    # Use this andline to determine if Steam is running in DeckUI mode.
    # e.g. "steam://shortpowerpress" only works in DeckUI.
    is_deckui = b"-gamepadui" in steam_cmd
    if not is_deckui:
        return False

    steam_path = handycon.HOME_PATH + '/.steam/root/ubuntu12_32/steam'
    try:
        result = subprocess.run(["su", handycon.USER, "-c", f"{steam_path} -ifrunning {cmd}"])
        return result.returncode == 0
    except Exception as err:
        handycon.logger.error(f"{err} | Error sending and to Steam.")
        handycon.logger.error(traceback.format_exc())
        return False


def launch_chimera():
    global handycon

    if not handycon.HAS_CHIMERA_LAUNCHER:
        return
    subprocess.run([ "su", handycon.USER, "-c", CHIMERA_LAUNCHER_PATH ])


def is_process_running(name) -> bool:
    read_proc = os.popen("ps -Af").read()
    proc_count = read_proc.count(name)
    if proc_count > 0:
        handycon.logger.debug(f'Process {name} is running.')
        return True
    handycon.logger.debug(f'Process {name} is NOT running.')
    return False

