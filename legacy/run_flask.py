#!/usr/bin/env python
"""
LEGACY SCRIPT: Not actively maintained.
Original purpose: A Flask web application to visualize temperature data.

This script reads temperature data from a CSV log file ('./logs/temperature.log'),
processes it, and serves two Matplotlib plots embedded in HTML:
- '/past': Displays historical smoker and meat temperatures with a rolling average.
- '/future': Displays historical data and forecasts future temperatures using an ARIMA model.

Note: This script is part of a legacy system. It has hardcoded paths, specific
library dependencies (e.g., statsmodels for ARIMA, specific Matplotlib usage),
and may not be robust for production use. It is superseded by the Dash application
in the main project directory.
"""
import csv
import base64
from io import BytesIO
from flask import Flask
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('Agg') # Use Agg backend for Matplotlib to avoid GUI issues in a web server context
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import dates as mdates
from matplotlib.ticker import AutoMinorLocator

from statsmodels.tsa.arima.model import ARIMA

app = Flask(__name__)

# --- Constants ---
LEGACY_LOG_FILE = './logs/temperature.log'
DEFAULT_ROLLING_WINDOW = 9
# For ARIMA model in plot_future
ARIMA_ORDER = (5, 1, 0) # (p,d,q) order for ARIMA model
PAST_STEPS_FOR_FORECAST = 600 # Number of past data points to use for ARIMA model
FORECAST_STEPS_FUTURE = 600   # Number of future steps to predict

def rolling_average(data, window_size=DEFAULT_ROLLING_WINDOW):
    """
    Computes the rolling average of a list of numerical data.

    Args:
        data (list of float or int): Input numerical data.
        window_size (int): Size of the rolling window. Must be an odd number
                           for the padding logic to work symmetrically.

    Returns:
        list of float: List of rolling averages. Returns original data if window_size is too small.
    """
    if window_size < 3: # Rolling average isn't very meaningful with less than 3
        return data
    if not isinstance(data, np.ndarray):
        data_array = np.array(data, dtype=float)
    else:
        data_array = data.astype(float)

    if data_array.ndim != 1:
        raise ValueError("Input data must be a 1-dimensional array or list.")
    if data_array.size < window_size:
        # Not enough data to compute rolling average with this window size
        return data_array.tolist()

    # Pad the data array at both ends to handle edges by repeating edge values.
    # This helps in calculating averages for the start and end of the series.
    pad_width = window_size // 2
    padded_data = np.pad(data_array, (pad_width, pad_width), mode='edge')

    # Use stride tricks to create a view of the data with rolling windows.
    # This is an efficient way to perform rolling calculations without explicit loops.
    shape = padded_data.shape[:-1] + (padded_data.shape[-1] - window_size + 1, window_size)
    strides = padded_data.strides + (padded_data.strides[-1],)
    rolling_view = np.lib.stride_tricks.as_strided(padded_data, shape=shape, strides=strides)

    # Calculate the mean across each window.
    rolling_avg = np.mean(rolling_view, axis=1)

    return rolling_avg.tolist()


def parse_temp_data_from_log(log_file_path=LEGACY_LOG_FILE):
    """
    Parses temperature data from the specified CSV log file.

    Args:
        log_file_path (str): Path to the CSV log file. The file is expected
                             to have rows with format: "HH:MM:SS.ffffff,smoker_temp,meat_temp".

    Returns:
        tuple: (list of datetime, list of float, list of float) for
               date_time, smoker_temp, and meat_temp.
               Returns empty lists if the file is not found or is empty.
    """
    date_times = []
    smoker_temps = []
    meat_temps = []

    try:
        with open(log_file_path, newline='', encoding='utf-8') as csvfile:
            data_reader = csv.reader(csvfile)
            for row in data_reader:
                if len(row) == 3: # Ensure row has expected number of columns
                    try:
                        date_times.append(datetime.strptime(row[0], "%H:%M:%S.%f"))
                        smoker_temps.append(float(row[1]))
                        meat_temps.append(float(row[2]))
                    except ValueError as ve:
                        print(f"Warning: Skipping malformed row in {log_file_path}: {row} - {ve}")
                        continue
                else:
                    print(f"Warning: Skipping row with unexpected number of columns in {log_file_path}: {row}")
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_file_path}")
        return [], [], []
    except Exception as e:
        print(f"Error reading log file {log_file_path}: {e}")
        return [], [], []

    if not date_times: # If no data was successfully parsed
        return [], [], []

    # Apply rolling average to smooth out the temperature readings
    smoker_temps_smoothed = rolling_average(smoker_temps)
    meat_temps_smoothed = rolling_average(meat_temps)

    return date_times, smoker_temps_smoothed, meat_temps_smoothed

def embed_plot_to_html(figure_obj):
    """
    Embeds a Matplotlib figure into an HTML img tag using base64 encoding.

    Args:
        figure_obj (matplotlib.figure.Figure): The Matplotlib figure to embed.

    Returns:
        str: An HTML string containing the embedded plot as an image.
    """
    # Save the figure to a temporary buffer as a PNG image.
    buf = BytesIO()
    figure_obj.savefig(buf, format="png")
    plt.close(figure_obj) # Close the figure to free memory

    # Encode the PNG image data to base64.
    img_data_base64 = base64.b64encode(buf.getvalue()).decode("ascii")

    # Return an HTML img tag with the embedded image data.
    return f"<img src='data:image/png;base64,{img_data_base64}'/>"


@app.route("/past")
def plot_past_temperatures():
    """
    Flask route to display a plot of past (historical) temperature data.
    Reads data using parse_temp_data_from_log and renders it as a Matplotlib plot.
    """
    date_time_list, smoker_temp_list, meat_temp_list = parse_temp_data_from_log()

    if not date_time_list:
        return "<html><body><h3>Error: No data could be loaded or parsed to display the past temperatures plot.</h3></body></html>"

    fig = Figure(figsize=(12, 6)) # Slightly larger figure size
    ax = fig.subplots()
    ax.plot(date_time_list, smoker_temp_list, label='Smoker Temperature (Smoothed)', color='magenta')
    ax.plot(date_time_list, meat_temp_list, label='Meat Temperature (Smoothed)', color='green')

    # Formatting the x-axis to display time nicely
    time_format = mdates.DateFormatter('%H:%M') # Display time as HH:MM
    ax.xaxis.set_major_formatter(time_format)

    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (°C)") # Assuming Celsius
    ax.set_ylim(bottom=0) # Temperature generally won't go below 0 for smoking

    ax.minorticks_on() # Enable minor ticks for finer grid lines
    # Set major ticks to be every 20 minutes
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=20))
    ax.xaxis.set_minor_locator(AutoMinorLocator()) # Automatically determine minor tick locations

    # Adjust x-axis limits if data is available
    if date_time_list:
        first_time = date_time_list[0]
        # Start x-axis from the beginning of the hour of the first data point
        dt_start_hour = first_time.replace(minute=0, second=0, microsecond=0)
        ax.set_xlim(left=dt_start_hour)

    # Rotate x-axis labels for better readability
    ax.tick_params(axis='x', labelrotation=45, labelsize=8) # Rotated and smaller font

    ax.grid(which='both', linestyle='--', linewidth=0.5) # Add grid lines for both major and minor ticks
    ax.legend()
    fig.tight_layout() # Adjust plot to prevent labels from being cut off

    return embed_plot_to_html(fig)


@app.route("/future")
def plot_future_temperatures_with_forecast():
    """
    Flask route to display a plot of historical data and forecasted future temperatures.
    Uses an ARIMA model for forecasting.
    """
    date_time_list, smoker_temp_list, meat_temp_list = parse_temp_data_from_log()

    if not date_time_list or len(date_time_list) < PAST_STEPS_FOR_FORECAST:
        return (
            "<html><body><h3>Error: Not enough historical data to generate a forecast. "
            f"Need at least {PAST_STEPS_FOR_FORECAST} data points after smoothing. "
            f"Currently have {len(date_time_list)}.</h3></body></html>"
        )

    # Use only the most recent data points for forecasting, as defined by PAST_STEPS_FOR_FORECAST
    recent_date_time = date_time_list[-PAST_STEPS_FOR_FORECAST:]
    recent_smoker_temp = smoker_temp_list[-PAST_STEPS_FOR_FORECAST:]
    recent_meat_temp = meat_temp_list[-PAST_STEPS_FOR_FORECAST:]

    smoker_forecast, smoker_conf_int = None, None
    meat_forecast, meat_conf_int = None, None

    try:
        # Smoker temp: Fit an ARIMA model and predict
        smoker_model = ARIMA(recent_smoker_temp, order=ARIMA_ORDER)
        smoker_model_fit = smoker_model.fit()
        smoker_forecast_result = smoker_model_fit.get_forecast(steps=FORECAST_STEPS_FUTURE)
        smoker_forecast = smoker_forecast_result.predicted_mean
        smoker_conf_int = smoker_forecast_result.conf_int()
    except Exception as e:
        print(f"Error fitting/forecasting smoker temperature ARIMA model: {e}")
        # Continue without smoker forecast if model fails

    try:
        # Meat temp: Fit an ARIMA model and predict
        meat_model = ARIMA(recent_meat_temp, order=ARIMA_ORDER)
        meat_model_fit = meat_model.fit()
        meat_forecast_result = meat_model_fit.get_forecast(steps=FORECAST_STEPS_FUTURE)
        meat_forecast = meat_forecast_result.predicted_mean
        meat_conf_int = meat_forecast_result.conf_int()
    except Exception as e:
        print(f"Error fitting/forecasting meat temperature ARIMA model: {e}")
        # Continue without meat forecast if model fails

    # Generate future time indices for the forecast
    last_historical_time = recent_date_time[-1]
    future_times_index = pd.date_range(start=last_historical_time, periods=FORECAST_STEPS_FUTURE + 1, freq='S')[1:]

    fig = Figure(figsize=(12, 7)) # Slightly taller for forecasts
    ax = fig.subplots()

    # Plot historical smoker temps
    ax.plot(recent_date_time, recent_smoker_temp, label='Smoker Temp (Recent History)', color='magenta')
    if smoker_forecast is not None and smoker_conf_int is not None:
        ax.plot(future_times_index, smoker_forecast, label='Smoker Temp (Predicted)', color='red', linestyle='--')
        ax.fill_between(future_times_index, smoker_conf_int[:, 0], smoker_conf_int[:, 1], color='pink', alpha=0.3, label='Smoker 95% CI')

    # Plot historical meat temps
    ax.plot(recent_date_time, recent_meat_temp, label='Meat Temp (Recent History)', color='green')
    if meat_forecast is not None and meat_conf_int is not None:
        ax.plot(future_times_index, meat_forecast, label='Meat Temp (Predicted)', color='blue', linestyle='--')
        ax.fill_between(future_times_index, meat_conf_int[:, 0], meat_conf_int[:, 1], color='cyan', alpha=0.3, label='Meat 95% CI')

    # Formatting the x-axis
    time_format = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(time_format)
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (°C)")
    ax.set_ylim(bottom=0)
    ax.minorticks_on()
    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30)) # Wider interval for forecast plot
    ax.xaxis.set_minor_locator(AutoMinorLocator())

    if recent_date_time:
        first_recent_time = recent_date_time[0]
        dt_start_hour_recent = first_recent_time.replace(minute=0, second=0, microsecond=0)
        ax.set_xlim(left=dt_start_hour_recent) # Start x-axis from beginning of hour of recent data

    ax.tick_params(axis='x', labelrotation=45, labelsize=8)
    ax.grid(which='both', linestyle='--', linewidth=0.5)
    ax.legend(fontsize=8) # Smaller legend font
    fig.tight_layout()

    return embed_plot_to_html(fig)


if __name__ == '__main__':
    print(f"Legacy Flask application starting. Open http://localhost:5000/past or http://localhost:5000/future")
    # Note: debug=True is not recommended for production environments.
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
