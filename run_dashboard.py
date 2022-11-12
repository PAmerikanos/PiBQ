#!/usr/bin/env python
import mcp9600
from bokeh.plotting import curdoc, figure
import time
from datetime import datetime

m = mcp9600.MCP9600()

def update():

    time = str(datetime.now().time())
    smoker_temp = m.get_hot_junction_temperature()
    #ambient_temp = m.get_cold_junction_temperature()
    r.data_source.stream({'x': [time], 'y': [smoker_temp]})
    
p = figure(title="Smoker Temperature", x_axis_label='Time', y_axis_label='Temperature', x_axis_type="datetime", plot_width=900, plot_height=1600, tools="xpan,xwheel_zoom,xbox_zoom,reset")
p.xaxis.major_label_orientation = "vertical"
r = p.circle([], [])
curdoc().add_root(p)
curdoc().add_periodic_callback(update, 1000)
