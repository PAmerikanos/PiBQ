# RT_temperature_dashboard
Dashboard to monitor temperature readings from IoT sensor in real time.

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
    
    python3.11 -m venv rt_plotly
    source rt_plotly/bin/activate

    pip install mcp9600 dash pandas statsmodels
    ```
4. Set up git repo:
    ```
    git clone https://github.com/PAmerikanos/RT_temperature_dashboard.git
    cd RT_temperature_dashboard/
    chmod +x execute.sh
    ```
5. Set up crontab for automatic execution:
    In `crontab -e` add the following line:
    ```
    @reboot ~/RT_temperature_dashboard/execute.sh
    ```

**CAUTION:** Do not run VSCode server on the RPi for development as it overloads the device and freezes it.

## Operation
1. Turn RPi on and connect it to the Internet. Automatic WiFi connection is set to `Pefki` SSID. The temperature recording and Flask server will initiate upon boot.
2. On client device open browser at `http://192.168.1.XXX:8050`

## Troubleshooting
From computer within the LAN connect to RPi using SSH: `ssh pi@192.168.1.XXX` / `pass: 0000`.

`Nohup` allows the recording & serving to continue even if WiFi or SSH connection is lost.
- `tail -f nohup.out` to monitor progress/nohup's output.
- `kill <PID>` to kill either process.

## References
- https://www.pi-shop.ch/thermocouple-amplifier-breakout
- https://github.com/pimoroni/mcp9600-python
