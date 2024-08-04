import csv
import base64
from io import BytesIO
from flask import Flask
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import dates as mdates
from matplotlib.ticker import AutoMinorLocator

from statsmodels.tsa.arima.model import ARIMA

app = Flask(__name__)

def rolling_average(data, window_size=3):
    """
    Compute the rolling average of a list of floats with a given window size.
    
    Parameters:
        data (list of floats): Input data.
        window_size (int): Size of the rolling window.
    
    Returns:
        list of floats: List of rolling averages.
    """
    # Convert data to NumPy array
    data_array = np.array(data)
    
    # Pad the data array at both ends to handle edges properly
    padded_data = np.pad(data_array, (window_size//2, window_size//2), mode='edge')
    
    # Create a rolling window view of the data array
    rolling_view = np.lib.stride_tricks.sliding_window_view(padded_data, window_shape=window_size)
    
    # Calculate the average along the rolling axis
    rolling_avg = np.mean(rolling_view, axis=1)
    
    return rolling_avg.tolist()


def parse_temp():
    date_time =[]
    smoker_temp = []
    meat_temp = []

    with open('temperature.log', newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for row in data:
            date_time.append(datetime.strptime(row[0],"%H:%M:%S.%f"))
            smoker_temp.append(float(row[1]))
            meat_temp.append(float(row[2]))

    smoker_temp = rolling_average(smoker_temp, 9)
    meat_temp = rolling_average(meat_temp, 9)

    return date_time, smoker_temp, meat_temp

def embed_plot(fig):
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")

    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"


@app.route("/past")
def plot_past():
    date_time, smoker_temp, meat_temp = parse_temp()
    
    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    ax.plot_date(date_time, smoker_temp, color = 'm')
    ax.plot_date(date_time, meat_temp, color = 'g')
    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    ax.tick_params(axis='x', rotation=45)
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature")
    ax.minorticks_on()
    xloc = mdates.MinuteLocator(interval = 15)
    ax.xaxis.set_major_locator(xloc)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    dt = date_time[0] - timedelta(minutes=date_time[0].minute, seconds=date_time[0].second)
    ax.set_xlim(left=dt)
    ax.grid(which='minor', linestyle='-', linewidth='1.0')
    fig.autofmt_xdate()

    return embed_plot(fig)


@app.route("/future")
def plot_future():
    date_time, smoker_temp, meat_temp = parse_temp()

    PAST_STEPS = 600
    FORECAST_STEPS = 600

    # Display onle last 10 minutes
    date_time = date_time[-PAST_STEPS:]
    smoker_temp = smoker_temp[-PAST_STEPS:]
    meat_temp = meat_temp[-PAST_STEPS:]

    # Smoker temp: Fit an ARIMA model and predict the next FORECAST_STEPS with confidence intervals
    smoker_model = ARIMA(smoker_temp, order=(5,1,0))
    smoker_model_fit = smoker_model.fit()
    smoker_forecast_result = smoker_model_fit.get_forecast(steps=FORECAST_STEPS)
    smoker_forecast = smoker_forecast_result.predicted_mean
    smoker_confidence_intervals = smoker_forecast_result.conf_int()

    # Meat temp: Fit an ARIMA model and predict the next FORECAST_STEPS with confidence intervals
    meat_model = ARIMA(meat_temp, order=(5,1,0))
    meat_model_fit = meat_model.fit()
    meat_forecast_result = meat_model_fit.get_forecast(steps=FORECAST_STEPS)
    meat_forecast = meat_forecast_result.predicted_mean
    meat_confidence_intervals = meat_forecast_result.conf_int()

    # Generate future time indices for the forecast
    last_time = date_time[-1]
    future_times = pd.date_range(start=last_time, periods=FORECAST_STEPS + 1, freq='S')[1:]
    
    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()

    # Plot smoker temps
    ax.plot(date_time, smoker_temp, label='Actual Smoker Temperature', color='m')
    ax.plot(future_times, smoker_forecast, label='Predicted Smoker Temperature', color='r')
    ax.fill_between(future_times, smoker_confidence_intervals[:, 0], smoker_confidence_intervals[:, 1], color='pink', alpha=0.3)

    # Plot meat temps
    ax.plot(date_time, meat_temp, label='Actual Meat Temperature', color='g')
    ax.plot(future_times, meat_forecast, label='Predicted Meat Temperature', color='b')
    ax.fill_between(future_times, meat_confidence_intervals[:, 0], meat_confidence_intervals[:, 1], color='cyan', alpha=0.3)

    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    ax.tick_params(axis='x', rotation=45)
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature")
    ax.minorticks_on()
    xloc = mdates.MinuteLocator(interval = 15)
    ax.xaxis.set_major_locator(xloc)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    dt = date_time[0] - timedelta(minutes=date_time[0].minute, seconds=date_time[0].second)
    ax.set_xlim(left=dt)
    ax.grid(which='minor', linestyle='-', linewidth='1.0')
    fig.autofmt_xdate()
    ax.legend()

    return embed_plot(fig)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)