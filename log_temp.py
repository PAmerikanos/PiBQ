#!/usr/bin/env python

import mcp9600
from datetime import datetime
import time
import csv

m = mcp9600.MCP9600()

with open('temperature.log', 'w', encoding = 'utf-8') as f:
    while True:
        smoker_temp = m.get_hot_junction_temperature()
        date_time = datetime.now().time()
        f.write(f"{date_time},{smoker_temp}\n")
        f.flush()
        time.sleep(2)
