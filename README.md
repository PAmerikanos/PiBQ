# RT_temperature_dashboard
Dashboard to monitor temperature readings from IoT sensor in real time.

## Setup
1. Configure I2C: `raspi-config > Interface Options > I2C > Enable`
2. Install dependencies: 
    ```
    sudo apt-get update
    sudo apt-get install python-pip
    sudo apt-get install libatlas-base-dev
    sudo pip3 install mcp9600
    sudo pip3 install matplotlib
    ```
3. Clone Git repo: `git clone https://github.com/PAmerikanos/RT_temperature_dashboard.git`

## Operation
1. Connect RPi to internet. Automatic WiFi connection set to `Pefki` SID.
2. Connect to headless RPi: `ssh pi@192.168.1.XXX` / `pass: 0000`. Check router for specific IP address.
3. On RPi uder `RT_temperature_dashboard` run in two terminals:
    - `nohup python3 log_temp.py &` to record temperature in realtime to `temperature.log` (every run overwrites the last one).
    - `nohup python3 run_flask.py &` to run the Flask server.
    
    `Nohup` allows the recording & serving to continue even if WiFi or SSH connection is lost.
    - `tail -f nohup.out` to monitor progress/nohup's output.
    - `kill <PID>` to kill either process.
3. On client device open browser at `http://192.168.1.XXX:5000/`

## References
- https://www.pi-shop.ch/thermocouple-amplifier-breakout
- https://github.com/pimoroni/mcp9600-python
