import base64
from io import BytesIO

from flask import Flask
from matplotlib.figure import Figure
import csv
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def hello():
    x =[]
    y = []
    with open('temperature.csv', newline='') as csvfile:
        data = list(csv.reader(csvfile))
        for row in data:
            x.append(datetime.strptime(row[0],"%H:%M:%S"))
            y.append(float(row[1]))

    # Generate the figure **without using pyplot**.
    fig = Figure()
    ax = fig.subplots()
    ax.plot(x, y, color = 'g', linestyle = 'dashed',
         marker = 'o',label = "Weather Data")
    ax.xticks(rotation = 25)
    ax.xlabel('Dates')
    ax.ylabel('Temperature(°C)')
    ax.title('Weather Report', fontsize = 20)
    ax.grid()

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"<img src='data:image/png;base64,{data}'/>"

if __name__ == '__main__':
    app.run()