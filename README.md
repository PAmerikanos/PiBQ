# RT_temperature_dashboard
Dashboard to monitor temperature readings from IoT sensor in real time.

## Setup:
1. Clone Git repo: `git clone https://github.com/PAmerikanos/RT_temperature_dashboard.git`
2. Configure I2C: `raspi-config > Interface Options > I2C > Enable`
3. Install Bokeh: 
    ```
    sudo apt-get update
    sudo apt-get install python-pip
    sudo pip install bokeh
    sudo apt-get install libatlas-base-dev
    sudo pip install mcp9600
    ```
3. Test Bokeh: `sudo bokeh info`


## To run:
1. Connect to headless RPi: `ssh pi@smokerpi.local` / `pass: 0000`
2. On SmokerPi under `/RT_temperature_dashboard/` initialize Bokeh server: `sudo bokeh serve run_dashboard.py --allow-websocket-origin localhost:5006 --allow-websocket-origin 192.168.1.XXX:5006 --allow-websocket-origin 192.168.1.YYY:5006 --show`
3. On client device open browser at `http://localhost:5006/test` or `192.168.1.XXX:5006`


### References:
- https://hub.gke2.mybinder.org/user/bokeh-bokeh-notebooks-5nbk1wx7/notebooks/tutorial/11%20-%20Running%20Bokeh%20Applications.ipynb
- https://github.com/bokeh/bokeh/blob/2.3.3/examples/app/ohlc/main.py
- https://atomar94.github.io/real-time-streaming-plots-with-python-and-bokeh/
- https://stackoverflow.com/questions/43101497/how-do-stream-data-to-a-bokeh-plot-in-jupyter-with-a-high-refresh-rate#43126481
- https://docs.bokeh.org/en/latest/docs/user_guide/data.html
- https://stackoverflow.com/a/60711068
- https://docs.bokeh.org/en/latest/docs/reference/command/subcommands/serve.html#network-configuration
