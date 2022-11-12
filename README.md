# RT_temperature_dashboard
Dashboard to monitor temperature readings from IoT sensor in real time.

## Setup:
1. Clone Git repo: `git clone https://github.com/PAmerikanos/RT_temperature_dashboard.git`
2. Install Bokeh: 
    ```
    sudo apt-get update
    sudo apt-get install python-pip
    sudo pip install bokeh
    sudo apt-get install libatlas-base-dev
    ```
3. Test Bokeh: `sudo bokeh info`


## To run:
1. Connect to headless RPi: `ssh pi@smokerpi.local` / `pass: 0000`
2. On SmokerPi initialize Bokeh server: `bokeh serve test.py --allow-websocket-origin localhost:5006 --allow-websocket-origin 192.168.1.XXX:5006 --allow-websocket-origin 192.168.1.2:5006 --show`
3. On client device open browser at `http://localhost:5006/test` or `192.168.1.XXX:5006`
