#!/usr/bin/env python
import mcp9600
from bokeh.plotting import curdoc, figure
import time
from datetime import datetime

# bokeh serve test.py --allow-websocket-origin localhost:5006 --allow-websocket-origin 192.168.1.7:5006 --allow-websocket-origin 192.168.1.2:5006 --show

m = mcp9600.MCP9600()

def update():

    time = str(datetime.now().time())
    smoker_temp = m.get_hot_junction_temperature()
    #ambient_temp = m.get_cold_junction_temperature()
    r.data_source.stream({'x': [time], 'y': [smoker_temp]})
    
p = figure(title="Smoker Temperature", x_axis_label='Time', y_axis_label='Temperature', x_axis_type="datetime", /
           plot_width=900, plot_height=1600, tools="xpan,xwheel_zoom,xbox_zoom,reset")
p.xaxis.major_label_orientation = "vertical"
r = p.circle([], [])
curdoc().add_root(p)
curdoc().add_periodic_callback(update, 1000)

# https://hub.gke2.mybinder.org/user/bokeh-bokeh-notebooks-5nbk1wx7/notebooks/tutorial/11%20-%20Running%20Bokeh%20Applications.ipynb
# https://github.com/bokeh/bokeh/blob/2.3.3/examples/app/ohlc/main.py
# https://atomar94.github.io/real-time-streaming-plots-with-python-and-bokeh/
# https://stackoverflow.com/questions/43101497/how-do-stream-data-to-a-bokeh-plot-in-jupyter-with-a-high-refresh-rate#43126481
# https://docs.bokeh.org/en/latest/docs/user_guide/data.html
# https://stackoverflow.com/a/60711068
# https://docs.bokeh.org/en/latest/docs/reference/command/subcommands/serve.html#network-configuration
