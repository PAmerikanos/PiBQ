#!/bin/bash

# Navigate to the project directory
cd ~/RT_temperature_dashboard || exit

# Activate the virtual environment
source ~/venv/rt_plotly/bin/activate

# Start temperature recording
nohup python3 record_temp.py > ./logs/record_temp.log 2>&1 &

# Wait 5 sec
sleep 5

# Run Flask server for Plotly Dash
nohup python3 app.py > ./logs/app.log 2>&1 &