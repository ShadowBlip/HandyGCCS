#!/usr/bin/env python3

import logging
from pathlib import Path

logging.basicConfig(format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(message)s",
                    datefmt="%y%m%d_%H:%M:%S",
                    level=logging.DEBUG
                    )

logger = logging.getLogger(__name__)

class IMU_WM2:
    def __init__(self):
        self._dev = Path("/sys/bus/iio/devices/iio:device0")
        try:
            with open(self._dev / "name", 'r') as f:
                if f.read().rstrip() == "i2c-BMI0160:00":
                    logger.debug("BMI160 detected.")
            self._valid_gyro_rates = [x for x in self._read_reg("in_anglvel_sampling_frequency_available").split()]
            self._valid_accel_rates = [x for x in self._read_reg("in_accel_sampling_frequency_available").split()]
            self._valid_gyro_scales = [x for x in self._read_reg("in_anglvel_scale_available").split()]
            self._valid_accel_scale = [x for x in self._read_reg("in_accel_scale_available").split()]
            
                
        except (FileNotFoundError,) as err:
            logger.error("BMI160 not detect.")
    
    def _read_reg(self, reg):
        with open(self._dev / reg, 'r') as f:
            return f.read()
    
    def _write_reg(self reg, val):
        with open(self._dev / reg, 'r') as f:
            f.write(f"{val}")
    
    def get_gyro_rate(self):
        return float(self._read_reg("in_anglvel_sampling_frequency"))
    
    def set_gyro_rate(self, rate):
        if f"{rate}" in self._valid_gyro_rates:
            self._write_reg("in_anglvel_sampling_frequency", rate)
        
    def get_accel_rate(self):
        return float(self._read_reg("in_accel_sampling_frequency"))

    def set_accel_rate(self, rate):
        if f"{rate}" in self._valid_accel_rates:
            self._write_reg("in_accel_sampling_frequency", rate)
    
    def get_gyro_scale(self):
        return float(self._read_reg("in_anglvel_scale"))

    def set_gyro_scale(self, scale):
        if f"{scale}" in self._valid_gyro_scales:
            self._write_reg("in_anglvel_scale", scale)
 
    def get_accel_scale(self):
        return float(self._read_reg("in_accel_scale"))

    def set_accel_scale(self, scale):
        if f"{scale}" in self._valid_accel_scales:
            self._write_reg("in_accel_scale", scale)

    def get_gyro_accel(self):
        m = [int(self._read_reg(f"in_anglvel_{ax}_raw")) for ax in ('x', 'y', 'z')]
        m.extend([int(self._read_reg(f"in_accel_{ax}_raw")) for ax in ('x', 'y', 'z')])
        return m

if __name__ == "__main__":
    imu = IMU_WM2()
    m = imu.get_gyro_accel()
    print(m)
