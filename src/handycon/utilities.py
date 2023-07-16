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

## Local modules
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
    cpu_vendor = handycon.get_cpu_vendor()
    handycon.logger.debug(f"Found CPU Vendor: {cpu_vendor}")

    ## ANBERNIC Devices
    if system_id in (
            "Win600",
            ):
        handycon.system_type = "ANB_GEN1"
        anb_gen1.init_handheld()

    ## ASUS Devices
    elif system_id in (
        "ROG Ally RC71L_RC71L",
        ):
        handycon.system_type = "ALY_GEN1"
        ally_gen1.init_handheld()

    ## Aya Neo Devices
    elif system_id in (
        "AYA NEO FOUNDER",
        "AYA NEO 2021",
        "AYANEO 2021",
        "AYANEO 2021 Pro",
        "AYANEO 2021 Pro Retro Power",
        ):
        handycon.system_type = "AYA_GEN1"
        aya_gen1.init_handheld()

    elif system_id in (
        "NEXT",
        "NEXT Pro",
        "NEXT Advance",
        "AYANEO NEXT",
        "AYANEO NEXT Pro",
        "AYANEO NEXT Advance",
        ):
        handycon.system_type = "AYA_GEN2"
        aya_gen2.init_handheld()

    elif system_id in (
        "AIR",
        "AIR Pro",
        ):
        handycon.system_type = "AYA_GEN3"
        aya_gen3.init_handheld()

    elif system_id in (
        "AYANEO 2",
        "GEEK",
        ):
        handycon.system_type = "AYA_GEN4"
        aya_gen4.init_handheld()

    elif system_id in (
        "AIR Plus",
        ):
        handycon.system_type = "AYA_GEN5"
        aya_gen5.init_handheld()

    elif system_id in (
        "AYANEO 2S",
        "GEEK 1S",
        ):
        handycon.system_type = "AYA_GEN6"
        aya_gen6.init_handheld()

    ## Ayn Devices
    elif system_id in (
            "Loki Max",
        ):
        handycon.system_type = "AYN_GEN1"
        ayn_gen1.init_handheld()

    ## GPD Devices.
    # Have 2 buttons with 3 modes (left, right, both)
    elif system_id in (
        "G1618-03", #Win3
        ):
        handycon.system_type = "GPD_GEN1"
        gpd_gen1.init_handheld()

    elif system_id in (
        "G1618-04", #WinMax2
        ):
        handycon.system_type = "GPD_GEN2"
        gpd_gen2.init_handheld()

    elif system_id in (
        "G1619-04", #Win4
        ):
        handycon.system_type = "GPD_GEN3"
        gpd_gen3.init_handheld()

## ONEXPLAYER and AOKZOE devices.
    # BIOS have inlete DMI data and most models report as "ONE XPLAYER" or "ONEXPLAYER".
    elif system_id in (
        "ONE XPLAYER",
        "ONEXPLAYER",
        ):
        if cpu_vendor == "GenuineIntel":
            handycon.system_type = "OXP_GEN1"
            oxp_gen1.init_handheld()
        else:
            handycon.system_type = "OXP_GEN2"
            oxp_gen2.init_handheld()

    elif system_id in (
        "ONEXPLAYER mini A07",
        ):
        handycon.system_type = "OXP_GEN3"
        oxp_gen3.init_handheld()

    elif system_id in (
        "ONEXPLAYER Mini Pro",
        "AOKZOE A1 AR07",
        "AOKZOE A1 Pro",
        ):
        handycon.system_type = "OXP_GEN4"
        oxp_gen4.init_handheld()

    # Block devices that aren't supported as this could cause issues.
    else:
        handycon.logger.error(f"{system_id} is not currently supported by this tool. Open an issue on \
ub at https://github.ShadowBlip/HandyGCCS if this is a bug. If possible, \
se run the capture-system.py utility found on the GitHub repository and upload \
 file with your issue.")
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
    config = configparser.ConfigParser()
    config_dir = "/etc/handygccs/"
    config_path = config_dir+"handygccs.conf"
    if os.path.exists(config_path):
        handycon.logger.info(f"Loading existing config: {config_path}")
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
        with open(config_path, 'w') as config_file:
            config.write(config_file)
            handycon.logger.info(f"Created new config: {config_path}")

    # Assign config file values
    handycon.button_map = {
    "button1": EVENT_MAP[config["Button Map"]["button1"]],
    "button2": EVENT_MAP[config["Button Map"]["button2"]],
    "button3": EVENT_MAP[config["Button Map"]["button3"]],
    "button4": EVENT_MAP[config["Button Map"]["button4"]],
    "button5": EVENT_MAP[config["Button Map"]["button5"]],
    }


async def toggle_performance():
    global handycon

    if handycon.performance_mode == "--max-performance":
        handycon.performance_mode = "--power-saving"
        await handycon.do_rumble(0, 100, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await handycon.do_rumble(0, 100, 1000, 0)
    else:
        handycon.performance_mode = "--max-performance"
        await handycon.do_rumble(0, 500, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await handycon.do_rumble(0, 75, 1000, 0)
        await asyncio.sleep(FF_DELAY)
        await handycon.do_rumble(0, 75, 1000, 0)

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
        handycon.logger.debug(f'Thermal mode set to {thermal_mode}.')


def steam_ifrunning_deckui(cmd):
    global handycon

    # Get the currently running Steam PID.
    steampid_path = handycon.HOME_PATH + '/.steam/steam.pid'
    try:
        with open(steampid_path) as f:
            pid = f.read().strip()
    except Exception as err:
        handycon.logger.error(f"{err} | Error getting steam PID.")
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
        return False


def launch_chimera():
    global handycon

    if not handycon.HAS_CHIMERA_LAUNCHER:
        return
    subprocess.run([ "su", handycon.USER, "-c", CHIMERA_LAUNCHER_PATH ])
