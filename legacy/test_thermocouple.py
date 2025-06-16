#!/usr/bin/env python
"""
LEGACY SCRIPT: Not actively maintained.
Original purpose: A test utility for an MCP9600 thermocouple sensor.

This script initializes a single MCP9600 sensor, configures several temperature
alerts, and then enters an infinite loop to continuously read and print:
- Hot junction temperature
- Cold junction (ambient) temperature
- Temperature delta (hot - cold)
- Status of the configured alerts

It also clears any triggered alert immediately after detection.

Note: This script is part of a legacy system. It assumes a default I2C address
and thermocouple type for the sensor, which should be explicitly set in a
production environment. The alert configurations might be specific to a particular
test case.
The link mentioned in the original code (https://forums.pimoroni.com/t/mcp9600-breakout-pim437/13129/3)
might provide context for troubleshooting or alert behavior.
"""

# If thermocouple diplays erroneos values: https://forums.pimoroni.com/t/mcp9600-breakout-pim437/13129/3

import mcp9600
from datetime import datetime # Retained as it was in original, though used in commented code
import time

# Initialize the MCP9600 sensor.
# IMPORTANT: This script assumes a default I2C address (often 0x60 or 0x67 for MCP9600)
# and a default thermocouple type (e.g., 'K'). For reliable operation, these should be
# explicitly set according to the hardware configuration.
# Example:
# sensor = mcp9600.MCP9600(i2c_addr=0x66) # Specify correct I2C address
# sensor.set_thermocouple_type('K')       # Specify thermocouple type
sensor = mcp9600.MCP9600() # Original: m = mcp9600.MCP9600()

print("Resetting alerts (1-4)...") # Clarified print message
for alert_loop_var in range(1, 5): # Renamed x to alert_loop_var
    sensor.clear_alert(alert_loop_var) # Use new sensor variable name
    sensor.configure_alert(alert_loop_var, enable=False) # Use new sensor variable name

print("Configuring alerts...") # Clarified print message
# Alert 1: Configured to monitor hot junction (0), limit 40°C, mode 1 (comparator).
# Default behavior for mode=1 without rise_fall specified often means alert on rising temp.
sensor.configure_alert(1, monitor_junction=0, limit=40, mode=1, enable=True)
# Alert 2: Monitors hot junction, limit 40°C, mode 1, but specifically for falling temperature (rise_fall=0).
sensor.configure_alert(2, monitor_junction=0, limit=40, mode=1, enable=True, rise_fall=0)
# Alert 3: Monitors hot junction, limit 40°C, mode 1, specifically for rising temperature (rise_fall=1).
sensor.configure_alert(3, monitor_junction=0, limit=40, mode=1, enable=True, rise_fall=1)
# Alert 4 remains disabled as it's not explicitly configured to be enabled after the reset loop.

"""
# This commented-out block appears to be an earlier, simpler test loop
# focusing on reading and printing only the hot junction temperature along with a timestamp.
while True:
    smoker_temp = sensor.get_hot_junction_temperature() # Would use new sensor name
    date_time = datetime.now().time()
    print(f"{date_time},{smoker_temp}")
    #time.sleep(1) # Sleep was commented out in original
"""

print("\nStarting continuous temperature and alert monitoring...")
print("Output format: Alerts Status | Hot (T_hot °C), Cold (T_cold °C), Delta (T_delta °C)")
try:
    while True:
        # Read temperatures
        hot_junction_temp = sensor.get_hot_junction_temperature() # Renamed t to hot_junction_temp
        cold_junction_temp = sensor.get_cold_junction_temperature() # Renamed c to cold_junction_temp
        temp_delta = sensor.get_temperature_delta() # Renamed d to temp_delta

        # Check alert statuses
        # The check_alerts() method returns a list/tuple of 4 boolean values (or 0/1)
        # indicating the status of alerts 1 through 4.
        alert_statuses = sensor.check_alerts()

        triggered_alert_messages = []
        # Iterate through the alert statuses. alerts_statuses is 0-indexed.
        for i in range(len(alert_statuses)):
            if alert_statuses[i]:  # If the alert is triggered
                alert_num = i + 1 # Convert 0-indexed (0-3) to alert number (1-4)
                sensor.clear_alert(alert_num) # Clear the triggered alert
                triggered_alert_messages.append(f"Alert {alert_num} TRIGGERED & cleared")

        # Print temperatures and alert information
        temp_info = f"Hot: {hot_junction_temp:.2f}°C, Cold: {cold_junction_temp:.2f}°C, Delta: {temp_delta:.2f}°C"
        alert_info = f"Alerts: {alert_statuses}"
        if triggered_alert_messages:
            print(f"{alert_info} | {temp_info} | Notes: {'; '.join(triggered_alert_messages)}")
        else:
            print(f"{alert_info} | {temp_info}")

        time.sleep(1.0)
except KeyboardInterrupt:
    print("\nMonitoring stopped by user.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
finally:
    print("Exiting test script.")
    # Consider disabling alerts on exit as a cleanup step, especially if they were set for specific test conditions.
    # print("Disabling alerts...")
    # for alert_num_to_disable in range(1, 5):
    #     try:
    #         sensor.configure_alert(alert_num_to_disable, enable=False)
    #     except Exception as e_disable:
    #         print(f"Could not disable alert {alert_num_to_disable}: {e_disable}")