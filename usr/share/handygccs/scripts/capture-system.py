#!/sbin/python3
# Capture System
# Copyright 2022 Derek J. Clark <derekjohn dot clark at gmail dot com>
# Produces an output file that caputres relevant system data that can be uploaded
# to github when reporting a new device.

import asyncio
import signal

from evdev import InputDevice, list_devices

# Declare global variables
all_devices = None
captured_keys = []
keybd = None
sys_id = None
xb360 = None


def capture_system():
    
    global all_devices
    global keybd
    global sys_id
    global xb360

    kb_path = None
    xb_path = None

    # Identify the current device type. Kill script if not compatible.
    sys_id = open("/sys/devices/virtual/dmi/id/product_name", "r").read().strip()


    # Identify system input event devices.
    devices = [InputDevice(path) for path in list_devices()]
    for device in devices:
        
        # Xbox 360 Controller
        if device.name in ['Microsoft X-Box 360 pad', 'Generic X-Box pad', 'OneXPlayer Gamepad',]:
            xb_path = device.path

        # Keyboard Device
        elif device.name == 'AT Translated Set 2 keyboard':
            kb_path = device.path
    
    # Catch if devices weren't found.
    if not xb_path or kb_path:
        all_devices = devices

    # Grab the built-in devices.
    if kb_path:
        keybd = InputDevice(kb_path)
    if xb_path:
        xb360 = InputDevice(xb_path)

async def capture_events(device):
    
    global captured_keys
    current = []

    # Capture events for the given device.
    async for event in device.async_read_loop():

        # We use active keys instead of ev1.code as we will override ev1 and
        # we don't want to trigger additional/different events when doing that
        active = device.active_keys()
        if active != []:    
            print(current, active, event)
        if event.value == 1 and current != active:
            current = active
        elif event.value == 0 and current not in captured_keys and current != []:
            print("Identified new keymap: ", current) 
            captured_keys.append(current)
            current = []


def save_capture():
    
    global all_devices
    global captured_keys
    global keybd
    global sys_id
    global xb360

    with open('capture_file.txt', 'w') as f:
        
        # System ID
        f.write('System ID:\n')
        f.write(sys_id)
        f.write('\n\n')

        # Controller
        f.write('X-Box 360 Device:\n')
        if xb360:
            f.write(xb360.name)
            f.write(' | ')
            f.write(xb360.phys)
            f.write(' | ')
            f.write('bustype: ')
            f.write(str(xb360.info.bustype))
            f.write(' vendor: ')
            f.write(str(xb360.info.vendor))
            f.write(' product: ')
            f.write(str(xb360.info.product))
            f.write(' version: ')
            f.write(str(xb360.info.version))
        f.write('\n\n')

        # Keyboard
        f.write('keyboard Device:\n')
        if keybd:
            f.write(keybd.name)
            f.write(' | ')
            f.write(keybd.phys)
            f.write(' | ')
            f.write('bustype: ')
            f.write(str(keybd.info.bustype))
            f.write(' vendor: ')
            f.write(str(keybd.info.vendor))
            f.write(' product: ')
            f.write(str(keybd.info.product))
            f.write(' version: ')
            f.write(str(keybd.info.version))
        f.write('\n\n')

        # All Devices:
        f.write('All Devices:')
        if all_devices:
            for d in all_devices:
                f.write('\n')
                f.write(d.name)
                f.write(' | ')
                f.write(d.phys)
                f.write(' | ')
                f.write('bustype: ')
                f.write(str(d.info.bustype))
                f.write(' vendor: ')
                f.write(str(d.info.vendor))
                f.write(' product: ')
                f.write(str(d.info.product))
                f.write(' version: ')
                f.write(str(d.info.version))
        f.write('\n\n')

        # Captured Keys
        f.write('Captured Keymaps:\n')
        for keymap in captured_keys:
            f.write(str(keymap))
            f.write('\n')
    print('Capture complete. Please upload the file titled "capture_file.txt" in \
a new GitHub issue to https://github.com/ShadowBlip/HandyGCCS/issues and any \
additional information you have.')


def main(killer):
    print('Gathering system info...')
    capture_system()
    
    if xb360 and keybd:
        print('Successfully identified compatible controllers. Press each \
non-functioning button in succession. When complete press ctrl+c to end capture.')
    else:
        print('Unable to identify compatible controller. Additional steps may be \
required after uploading your capture file to fully integrate your device.')
        killer.alive = False 
        return

    # Run asyncio loop to capture all events
    asyncio.ensure_future(capture_events(xb360))
    asyncio.ensure_future(capture_events(keybd))
        
    loop = asyncio.get_event_loop()
    loop.run_forever()


class GracefulKiller:
    alive = True

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        self.alive = False
        save_capture()
        exit(0)

if __name__ == "__main__":
    print('Scanning system and creating device profile.')
    killer = GracefulKiller()
    while killer.alive:
        main(killer)
    save_capture()
    exit(0)
