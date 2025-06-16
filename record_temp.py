#!/usr/bin/env python
"""
Records temperature data from two MCP9600 thermocouple sensors to a CSV file.

This script initializes two MCP9600 sensors, one for monitoring smoker temperature
and another for meat temperature, via I2C communication. It continuously reads
temperatures from these sensors every second and appends the data, along with
a timestamp, to a CSV file stored in a 'temperature' subdirectory.

The CSV file is named with the date and time of the script's execution start.
Each row in the CSV file contains: time, smoker_temperature, meat_temperature.

Dependencies:
- pimoroni-mcp9600: Python library for the MCP9600 thermocouple amplifier.
  (https://github.com/pimoroni/mcp9600-python)

Make sure the I2C interface is enabled on your system (e.g., Raspberry Pi)
and the MCP9600 sensors are connected to the correct I2C addresses.
"""

import mcp9600
from datetime import datetime
import time
import os

# --- Configuration Constants ---
SMOKER_SENSOR_I2C_ADDR = 0x66  # I2C address for the smoker temperature sensor
MEAT_SENSOR_I2C_ADDR = 0x67    # I2C address for the meat temperature sensor
THERMOCOUPLE_TYPE = 'K'        # Type of thermocouple being used (e.g., 'K', 'J', 'T')
DATA_OUTPUT_DIR = './temperature/' # Directory to store temperature CSV files
LOGGING_INTERVAL_SECONDS = 1   # Time interval in seconds between readings

def initialize_sensor(i2c_address, thermocouple_type_str):
    """Initializes an MCP9600 sensor at the given I2C address and sets thermocouple type."""
    sensor = mcp9600.MCP9600(i2c_addr=i2c_address)
    sensor.set_thermocouple_type(thermocouple_type_str)
    return sensor

def main():
    """Main function to initialize sensors and record temperature data."""
    print(f"Initializing smoker sensor at I2C address {hex(SMOKER_SENSOR_I2C_ADDR)}...")
    smoker_sensor = initialize_sensor(SMOKER_SENSOR_I2C_ADDR, THERMOCOUPLE_TYPE)
    print(f"Initializing meat sensor at I2C address {hex(MEAT_SENSOR_I2C_ADDR)}...")
    meat_sensor = initialize_sensor(MEAT_SENSOR_I2C_ADDR, THERMOCOUPLE_TYPE)

    # Create the data directory if it doesn't exist
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
        print(f"Created data directory: {DATA_OUTPUT_DIR}")

    # Generate a unique filename based on the current date and time
    csv_filename = datetime.now().strftime('%Y%m%d_%H%M%S') + ".csv"
    full_file_path = os.path.join(DATA_OUTPUT_DIR, csv_filename)

    print(f"Starting temperature recording. Data will be saved to: {full_file_path}")
    print("Press Ctrl+C to stop recording.")

    with open(full_file_path, 'w', encoding='utf-8') as data_file:
        # Write header row (optional, but good for clarity)
        # data_file.write("time,smoker_temp_c,meat_temp_c\n")

        try:
            while True:
                current_time_str = datetime.now().time().strftime('%H:%M:%S.%f')[:-3] # HH:MM:SS.milliseconds

                try:
                    smoker_temp_c = smoker_sensor.get_hot_junction_temperature()
                except Exception as e:
                    print(f"Error reading smoker sensor: {e}")
                    smoker_temp_c = "NaN" # Record NaN if sensor read fails

                try:
                    meat_temp_c = meat_sensor.get_hot_junction_temperature()
                except Exception as e:
                    print(f"Error reading meat sensor: {e}")
                    meat_temp_c = "NaN" # Record NaN if sensor read fails

                # Write data to CSV
                data_file.write(f"{current_time_str},{smoker_temp_c},{meat_temp_c}\n")
                data_file.flush()  # Ensure data is written to disk immediately

                # Wait for the specified interval
                time.sleep(LOGGING_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nRecording stopped by user.")
        finally:
            print(f"Data saved to {full_file_path}")

if __name__ == '__main__':
    main()
