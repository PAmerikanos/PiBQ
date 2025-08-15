# PiBQ
BBQ monitoring dashboard

## Setup
1. Configure I2C: `raspi-config > Interface Options > I2C > Enable`
2. Add to `/boot/firmware/config.txt`:
    ```
    dtparam=i2c_arm=on,i2c_arm_baudrate=9600
    ```
    If thermocouple diplays erroneous values:
    - https://forums.pimoroni.com/t/mcp9600-breakout-pim437/13129/3
    - https://www.raspberrypi-spy.co.uk/2018/02/change-raspberry-pi-i2c-bus-speed/
3. Install dependencies: 
    ```
    sudo apt update
    sudo apt install python3.11 python3.11-venv python3.11-dev -y
    
    python3.11 -m venv pibq
    source pibq/bin/activate

    pip install -r requirements.txt
    ```
4. Set up git repo:
    ```
    git clone https://github.com/PAmerikanos/PiBQ.git
    cd PiBQ/
    ```
5. Set up systemd services for automatic execution:
    ```
    sudo chmod +x install-services.sh
    sudo ./install-services.sh
    sudo systemctl start pibq-recorder
    sudo systemctl start pibq-dashboard
    ```

**CAUTION:** Do not run VSCode server on the RPi for development as it overloads the device and freezes it.

## Operation
1. Turn RPi on and connect it to the Internet. Automatic WiFi connection is set to `Pefki` SSID. The temperature recording and Flask server will initiate upon boot.
2. Locate RPi IP using the WiFi router's network manager.
3. On client device open browser at `http://192.168.XXX.XXX:8000` as found above.

## Features
- **Real-time Temperature Monitoring**: Live display of smoker and meat temperatures
- **Smart Forecasting**: Simple trend-based temperature prediction with confidence bands
- **Steady-State Detection**: Automatically adjusts predictions for stable temperatures
- **Customizable Settings**: Adjustable target temperatures, forecast windows, and smoothing
- **Historical Data**: View multiple sessions and analyze cooking patterns
- **Mobile-Friendly**: Responsive design for monitoring on mobile devices
- **Auto-refresh**: Dashboard updates every 60 seconds automatically

## Troubleshooting
From computer within the LAN connect to RPi using SSH: `ssh pi@192.168.XXX.XXX` / `pass: 0000`.

Check service status & logs:
```
sudo systemctl status pibq-recorder
sudo systemctl status pibq-dashboard
```

Restart PiBQ services with `sudo systemctl daemon-reload`.

## ToDo
- ✅ Fix: Improve prediction model (Implemented simple trend forecasting with steady-state detection)
- Fix: Check why smoker/meat probes show a 2°C offset.
- Add: Temperature alerts and notifications
- Add: Cooking phase detection and time estimates

## References
- https://www.pi-shop.ch/thermocouple-amplifier-breakout
- https://github.com/pimoroni/mcp9600-python
