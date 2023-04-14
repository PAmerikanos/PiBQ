#!/usr/bin/env python

import mcp9600
from datetime import datetime
import time
import csv

m = mcp9600.MCP9600()

with open('temperature.log', 'w') as f:
    writer = csv.writer(f)

    while True:
        smoker_temp = m.get_hot_junction_temperature()
        date_time = datetime.now().time()
        writer.writerow([date_time, smoker_temp])
        writer.flush()
        time.sleep(1)
