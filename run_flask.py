import base64
from io import BytesIO

from flask import Flask
from matplotlib.figure import Figure
import csv
from datetime import datetime, timedelta
from matplotlib import dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

app = Flask(__name__)

import numpy as np

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


@app.route("/")
def hello():
    x =[]
    y = []
    with open('temperature.log', newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for row in data:
            x.append(datetime.strptime(row[0],"%H:%M:%S.%f"))
            y.append(float(row[1]))

    y = rolling_average(y, 9)
    
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

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)