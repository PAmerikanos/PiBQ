# RT_temperature_dashboard
Dashboard to monitor temperature readings from IoT sensor in real time.

## Setup
1. Clone Git repo: `git clone https://github.com/PAmerikanos/RT_temperature_dashboard.git`
2. Configure I2C: `raspi-config > Interface Options > I2C > Enable`
3. Install dependencies: 
    ```
    sudo apt-get update
    sudo apt-get install python-pip
    sudo apt-get install libatlas-base-dev
    sudo pip install mcp9600
    ```

## Operation
1. Connect to headless RPi: `ssh pi@192.168.1.XXX` / `pass: 0000`
2. On SmokerPi under `/Documents/RT_temperature_dashboard/` run in two terminals:
    - `log_temp.py` to record temperature in realtime to a textfile. Every run overwrites the previous.
    - `run_flask.py` to run Flask server.
3. On client device open browser at `http://192.168.1.XXX:5000/`

## References
- https://www.pi-shop.ch/thermocouple-amplifier-breakout
- https://github.com/pimoroni/mcp9600-python
