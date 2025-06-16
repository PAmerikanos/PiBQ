# Real-Time Temperature Dashboard

This project provides a web-based dashboard to monitor and visualize real-time temperature readings from MCP9600 thermocouple sensors connected to a Raspberry Pi. It also includes functionality to forecast future temperature trends.

## Core Components
*   **`record_temp.py`**: A Python script that continuously reads data from two MCP9600 thermocouple sensors (e.g., for a smoker and meat) and logs it to daily CSV files in the `./temperature/` directory.
*   **`app.py`**: A Dash (Plotly) web application that visualizes the collected temperature data, displays historical trends, and provides temperature forecasts.
*   **`execute.sh`**: A shell script designed to run `record_temp.py` and `app.py` automatically on boot (e.g., when configured with crontab).
*   **`legacy/`**: This directory contains older, unmaintained code (e.g., previous Bokeh/Flask versions of the dashboard). See `legacy/README.md` for more details. Use with caution.

## Hardware Setup (Raspberry Pi)

1.  **Enable I2C Interface**:
    *   Run `sudo raspi-config`.
    *   Navigate to `Interface Options` > `I2C`.
    *   Select `Enable`.

2.  **Configure I2C Bus Speed (Optional, for specific troubleshooting)**:
    *   Edit `/boot/firmware/config.txt` (or `/boot/config.txt` on older Raspberry Pi OS versions).
    *   Add or modify the following line. A baudrate of `9600` is slow and might be for specific sensor behavior; standard is often `100000` or `400000`. Adjust if necessary, but `9600` was in the original notes.
        ```
        dtparam=i2c_arm=on,i2c_arm_baudrate=9600
        ```
    *   Refer to these links if you encounter issues with sensor readings (as noted in original documentation):
        *   [Pimoroni Forum: MCP9600 erroneous values](https://forums.pimoroni.com/t/mcp9600-breakout-pim437/13129/3)
        *   [Raspberry Pi Spy: Change I2C Bus Speed](https://www.raspberrypi-spy.co.uk/2018/02/change-raspberry-pi-i2c-bus-speed/)

## Software Setup

1.  **Clone Repository**:
    ```bash
    git clone https://github.com/PAmerikanos/RT_temperature_dashboard.git
    cd RT_temperature_dashboard
    ```

2.  **Install System Dependencies (Example for Python 3.11)**:
    ```bash
    sudo apt update
    sudo apt install python3.11 python3.11-venv python3.11-dev -y
    # Adjust Python version if needed. Python 3.7+ is generally recommended for Dash.
    ```

3.  **Create and Activate Virtual Environment**:
    ```bash
    python3.11 -m venv rt_plotly
    # This creates a virtual environment named 'rt_plotly'
    source rt_plotly/bin/activate
    # Activate the environment. You'll need to do this every time you open a new terminal session to work on the project.
    ```

4.  **Install Python Libraries**:
    With the virtual environment activated, run:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Make `execute.sh` Executable**:
    ```bash
    chmod +x execute.sh
    ```

6.  **Create Log/Data Directories**:
    The `execute.sh` script and `app.py`/`record_temp.py` expect certain directories.
    ```bash
    mkdir -p ./logs
    mkdir -p ./temperature
    # Note: record_temp.py and app.py also attempt to create ./temperature/ if it doesn't exist.
    ```

## Running the Application

There are two main ways to run the application:

### 1. Manual Execution

*   **Start Data Recording**:
    Open a terminal, navigate to the project directory, activate the virtual environment (`source rt_plotly/bin/activate`), and run:
    ```bash
    # Ensure I2C is configured and sensors are connected
    sudo python3 record_temp.py
    # Use 'sudo' if required by the mcp9600 library for I2C access on your system.
    # This will start logging data to ./temperature/YYYYMMDD_HHMMSS.csv
    ```
    Keep this script running in a terminal or use a tool like `screen` or `tmux` to run it in the background.

*   **Start the Dashboard Application**:
    Open another terminal, navigate to the project directory, activate the virtual environment, and run:
    ```bash
    python3 app.py
    ```
    The dashboard should then be accessible in a web browser at `http://<RaspberryPi_IP_Address>:8050` (e.g., `http://192.168.1.XXX:8050`). Replace `<RaspberryPi_IP_Address>` with the actual IP address of your Raspberry Pi.

### 2. Automatic Execution on Boot (using `execute.sh` and crontab)

The `execute.sh` script is designed to start both `record_temp.py` and `app.py` in the background using `nohup`. This is suitable for a headless setup.

*   **Review `execute.sh`**: Ensure paths within `execute.sh` (e.g., `/home/pi/RT_temperature_dashboard`, path to `activate`) match your setup.
*   **Configure Crontab**:
    Edit the crontab for your user (e.g., `pi`):
    ```bash
    crontab -e
    ```
    Add the following line at the end of the file to run the script on reboot:
    ```cron
    @reboot /home/pi/RT_temperature_dashboard/execute.sh
    ```
    *(Important: Adjust the path `/home/pi/RT_temperature_dashboard/execute.sh` if your project is located elsewhere or if you are using a different username.)*

*   **Operation with Crontab**:
    1.  Ensure the Raspberry Pi is powered on and connected to your network.
    2.  The temperature recording (`record_temp.py`) and the Dash web server (`app.py`) will start automatically after the Pi boots up.
    3.  Access the dashboard from another device on the same network by navigating to `http://<RaspberryPi_IP_Address>:8050`.

    Output from these scripts (when run via `execute.sh`) will be logged to files in the `./logs/` directory (`record_temp.log` and `app.log`).

**CAUTION**: The original README mentioned not running a VSCode server on the RPi due to performance issues. This might still be relevant depending on your Raspberry Pi model and workload.

## Troubleshooting

*   **SSH Connection**: Connect to your Raspberry Pi via SSH if you need to manage processes or check logs:
    ```bash
    ssh pi@<RaspberryPi_IP_Address>
    # Default password might be 'raspberry' or as noted in the original README ('0000').
    ```
*   **Check Logs**:
    *   For the data recording script (if run via `execute.sh`): `tail -f ./logs/record_temp.log`
    *   For the Dash application (if run via `execute.sh`): `tail -f ./logs/app.log`
    *   If `nohup` was used directly without redirection: `tail -f nohup.out`.
*   **Process Management**:
    *   To find Process IDs (PIDs): `pgrep -f record_temp.py` or `pgrep -f app.py`.
    *   To stop a process: `kill <PID>`.
*   **I2C Issues**: Ensure sensors are correctly wired and the I2C address in `record_temp.py` (SMOKER_SENSOR_I2C_ADDR, MEAT_SENSOR_I2C_ADDR) matches your hardware. Use `i2cdetect -y 1` (or `i2cdetect -y 0` on older Pis) to scan for connected I2C devices.

## Hardware/Library References
*   [MCP9600 Thermocouple Amplifier Breakout](https://www.pi-shop.ch/thermocouple-amplifier-breakout) (Example product page)
*   [Pimoroni MCP9600 Python Library](https://github.com/pimoroni/mcp9600-python)
*   [Dash Documentation](https://dash.plotly.com/)
*   [Plotly Python Documentation](https://plotly.com/python/)
```
