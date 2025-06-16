#!/usr/bin/env python
"""
LEGACY SCRIPT: Not actively maintained.
Original purpose: To run a simple Bokeh dashboard displaying real-time temperature
readings from a single MCP9600 thermocouple sensor.

This script initializes an MCP9600 sensor and uses Bokeh to create a live-updating
line graph of the temperature. The x-axis represents time, and the y-axis
represents the temperature read from the sensor.

Note: This script is designed for a specific, older setup and may require
adjustments or specific library versions (e.g., Bokeh 2.4.3 as mentioned in
the legacy README) to run correctly. It is superseded by the Dash application
in the main project directory.
"""
import mcp9600
from datetime import datetime
from bokeh.driving import count
from bokeh.plotting import curdoc, figure # curdoc is used to add content to the Bokeh document
from bokeh.models import ColumnDataSource # For streaming data
# from bokeh.layouts import column, gridplot, row # Layout utilities (commented out as not used)

# Initialize the MCP9600 sensor.
# IMPORTANT: This assumes a default I2C address (often 0x60 or 0x67) and thermocouple type (e.g., 'K').
# For reliability, explicitly set these if known for the original setup:
# Example:
# sensor_mcp = mcp9600.MCP9600(i2c_addr=0x66) # Replace 0x66 with your sensor's actual I2C address
# sensor_mcp.set_thermocouple_type('K')     # Replace 'K' with your thermocouple type if different
sensor_mcp = mcp9600.MCP9600() # Original line: m = mcp9600.MCP9600()

# Create a ColumnDataSource for streaming data to the plot.
# This allows the plot to update efficiently with new data points.
data_source_stream = ColumnDataSource(dict(time=[], smoker_temp=[])) # Original line: source = ColumnDataSource(...)

# Create the Bokeh figure (the plot object)
temperature_plot_fig = figure( # Original line: p = figure(...)
    title="Smoker Temperature (Legacy Dashboard)",
    x_axis_label='Time',
    y_axis_label='Temperature (°C)', # Assuming Celsius, common for these sensors
    tools="xpan,xwheel_zoom,ywheel_zoom,reset", # Interactive tools for the plot
    x_axis_type="datetime",      # X-axis will display datetime objects
    y_axis_location="right",     # Position the Y-axis on the right
    toolbar_location="left",     # Position the toolbar on the left
    width=1000,                  # Plot width in pixels
    height=400                   # Plot height in pixels
)

# Configure the x-axis to automatically follow the latest data point.
temperature_plot_fig.x_range.follow = "end"
# To make the follow behavior smoother over an interval (e.g., 5000ms):
# temperature_plot_fig.x_range.follow_interval = 5000 # Original commented: #p.x_range.follow_interval = 50
temperature_plot_fig.x_range.range_padding = 0 # No extra padding on the x-axis range

# Add a line glyph to the plot. This defines how the data will be rendered.
temperature_plot_fig.line(
    x='time',                    # Column name for x-coordinates from data_source_stream
    y='smoker_temp',             # Column name for y-coordinates from data_source_stream
    source=data_source_stream,   # The data source to use
    alpha=0.8,                   # Line transparency
    line_width=3,                # Line thickness
    color='red',                 # Line color
)

@count() # Bokeh decorator to provide an incrementing counter 'time_step_count' to the update function
def update_plot_data(time_step_count): # Original line: def update(t):
    """
    Callback function to update the plot data periodically.

    This function is called by Bokeh at regular intervals. It reads the current
    temperature from the sensor and streams this new data point to the
    ColumnDataSource, which in turn updates the plot.

    Args:
        time_step_count (int): An internal counter provided by @count decorator (useful for debugging or step-based logic, but unused here).
    """
    current_datetime = datetime.now()  # Use full datetime object for x-axis compatibility with x_axis_type="datetime"
                                     # Original line used: time = datetime.now().time() which is not ideal for datetime axis.

    current_smoker_temp = None # Initialize to None
    try:
        # Attempt to read temperature from the sensor
        current_smoker_temp = sensor_mcp.get_hot_junction_temperature()
    except OSError as e:
        # Handle potential I2C communication errors
        print(f"Error reading sensor (OSError) in legacy/run_dashboard.py: {e}. Recording as NaN.")
        current_smoker_temp = float('nan') # Use NaN for missing data
    except Exception as e:
        # Handle other potential errors from the sensor library
        print(f"An unexpected error occurred while reading sensor in legacy/run_dashboard.py: {e}. Recording as NaN.")
        current_smoker_temp = float('nan')

    # Prepare the new data point as a dictionary matching ColumnDataSource structure
    new_data_point = dict(time=[current_datetime], smoker_temp=[current_smoker_temp])

    # Stream the new data to the source.
    # 'rollover=300' limits the data source to the last 300 points, preventing memory issues.
    # This was not in the original script but is good practice for long-running plots.
    data_source_stream.stream(new_data_point, rollover=300)

# Add the configured plot to the current Bokeh document (web page).
curdoc().add_root(temperature_plot_fig) # Original line: curdoc().add_root(p)

# Schedule the 'update_plot_data' function to be called every 1000 milliseconds (1 second).
curdoc().add_periodic_callback(update_plot_data, 1000) # Original line: curdoc().add_periodic_callback(update, 1000)

# Set the title of the HTML page for the Bokeh application.
curdoc().title = "Legacy Smoker Temperature Dashboard" # Original line: curdoc().title = "Smoker Temperature"
