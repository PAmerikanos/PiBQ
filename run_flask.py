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
    x =[]
    y = []
    with open('temperature.log', newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for row in data:
            x.append(datetime.strptime(row[0],"%H:%M:%S.%f"))
            y.append(float(row[1]))

    y = rolling_average(y, 9)

    return x, y

def embed_plot(fig):
    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")

    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"


@app.route("/past")
def plot_past():
    x, y = parse_temp()
    
    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()
    ax.plot_date(x, y, color = 'g')
    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    ax.tick_params(axis='x', rotation=45)
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature")
    ax.minorticks_on()
    xloc = mdates.MinuteLocator(interval = 15)
    ax.xaxis.set_major_locator(xloc)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    dt = x[0] - timedelta(minutes=x[0].minute, seconds=x[0].second)
    ax.set_xlim(left=dt)
    ax.grid(which='minor', linestyle='-', linewidth='1.0')
    fig.autofmt_xdate()

    return embed_plot(fig)


@app.route("/future")
def plot_future():
    x, y = parse_temp()

    # Display onle last 10 minutes
    x = x[-600:]
    y = y[-600:]

    # Fit an ARIMA model
    model = ARIMA(y, order=(5,1,0))
    model_fit = model.fit()

    # Predict the next five minutes (300 seconds) of temperature readings with confidence intervals
    forecast_steps = 600
    forecast_result = model_fit.get_forecast(steps=forecast_steps)
    forecast = forecast_result.predicted_mean
    confidence_intervals = forecast_result.conf_int()

    # Generate future time indices for the forecast
    last_time = x[-1]
    future_times = pd.date_range(start=last_time, periods=forecast_steps + 1, freq='S')[1:]
    
    fig = Figure(figsize=(10, 5))
    ax = fig.subplots()

    ax.plot(x, y, label='Actual Temperature', color='g')
    ax.plot(future_times, forecast, label='Predicted Temperature', color='r')
    ax.fill_between(future_times, confidence_intervals[:, 0], confidence_intervals[:, 1], color='pink', alpha=0.3)

    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    ax.tick_params(axis='x', rotation=45)
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature")
    ax.minorticks_on()
    xloc = mdates.MinuteLocator(interval = 15)
    ax.xaxis.set_major_locator(xloc)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    dt = x[0] - timedelta(minutes=x[0].minute, seconds=x[0].second)
    ax.set_xlim(left=dt)
    ax.grid(which='minor', linestyle='-', linewidth='1.0')
    fig.autofmt_xdate()
    ax.legend()

    return embed_plot(fig)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)