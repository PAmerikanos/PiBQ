#!/usr/bin/env python
import mcp9600
from datetime import datetime
from bokeh.driving import count
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource
from bokeh.layouts import column, gridplot, row

m = mcp9600.MCP9600()
source = ColumnDataSource(dict(time=[], smoker_temp=[]))

p = figure(title="Smoker Temperature", x_axis_label='Time', y_axis_label='Temperature', tools="xpan,xwheel_zoom,ywheel_zoom,reset", x_axis_type="datetime", y_axis_location="right", toolbar_location="left", plot_width=1000)
p.x_range.follow = "end"
#p.x_range.follow_interval = 50
p.x_range.range_padding = 0
p.line(x='time', y='smoker_temp', alpha=0.8, line_width=3, color='red', source=source)

@count()
def update(t):
    time = datetime.now().time()
    smoker_temp = m.get_hot_junction_temperature()
    new_data = dict(time=[time], smoker_temp=[smoker_temp])
    source.stream(new_data)

#curdoc().add_root(column(gridplot([[p]], toolbar_location="left", plot_width=1000)))
curdoc().add_root(p)
curdoc().add_periodic_callback(update, 1000)
curdoc().title = "Smoker Temperature"
