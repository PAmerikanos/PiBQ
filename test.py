from bokeh.plotting import curdoc, figure
import random
import time
from datetime import datetime

def update():

    with open("stream_test.csv", "r", encoding="utf-8", errors="ignore") as scraped:
        final_line = scraped.readlines()[-1]
        
    split_row = final_line.split(",")
    time = datetime.strptime(split_row[0], '%Y-%m-%d %H:%M:%S')
    temp = float(split_row[1][:-1])
    r.data_source.stream({'x': [time], 'y': [temp]})
    
p = figure()
r = p.circle([], [])
curdoc().add_root(p)
curdoc().add_periodic_callback(update, 100)
