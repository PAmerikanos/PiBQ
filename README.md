# RT_temperature_dashboard
Dashboard to monitor temperature readings from IoT sensor in real time.

Connect to headless RPi:
`ssh pi@smokerpi.local`
`pass: 0000`

To run:
1. On SmokerPi initialize Bokeh server: `bokeh serve test.py --allow-websocket-origin localhost:5006 --allow-websocket-origin 192.168.1.7:5006 --allow-websocket-origin 192.168.1.2:5006 --show`
2. On client device open browser at `http://localhost:5006/test` or `192.168.1.XXX:5006`
