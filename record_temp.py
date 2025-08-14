#!/usr/bin/env python

import mcp9600
from datetime import datetime
import time
import os

# https://github.com/pimoroni/mcp9600-python/blob/master/REFERENCE.md#function-reference

smoker_sensor = mcp9600.MCP9600(i2c_addr=0x66)
smoker_sensor.set_thermocouple_type('K')

meat_sensor = mcp9600.MCP9600(i2c_addr=0x67)
meat_sensor.set_thermocouple_type('K')

filename = datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv"
dir_path = './temperature/'
if not os.path.exists(dir_path):
    os.makedirs(dir_path)

with open(os.path.join(dir_path, filename), 'w', encoding = 'utf-8') as f:
    while True:
        date_time = datetime.now().time()

        smoker_temp = smoker_sensor.get_hot_junction_temperature()
        meat_temp = meat_sensor.get_hot_junction_temperature()

        f.write(f"{date_time},{smoker_temp},{meat_temp}\n")
        f.flush()

        time.sleep(1.1) # So we can disregard milliseconds in the app.py code
