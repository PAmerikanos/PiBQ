#!/bin/bash

# Navigate to the project directory
cd /home/pi/PiBQ || exit

# Activate the virtual environment
source /home/pi/PiBQ/rt_plotly/bin/activate

# Start temperature recording
nohup python3 record_temp.py > ./logs/record_temp.log 2>&1 &

# Wait 5 sec
sleep 5

# Run Flask server for Plotly Dash
nohup python3 app.py > ./logs/app.log 2>&1 &
