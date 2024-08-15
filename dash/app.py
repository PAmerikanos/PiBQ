from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd


app = Dash()

app.layout = [
    html.H1(children='Title of Dash App', style={'textAlign':'center'}),
    #dcc.Dropdown(df.country.unique(), 'Canada', id='dropdown-selection'),
    dcc.Graph(id='graph-content'),

    # Interval component for auto-refreshing every 5 minutes (300000 milliseconds)
    dcc.Interval(
        id='interval-component',
        interval=300*1000,  # 300 seconds = 5 minutes
        n_intervals=0  # Number of times the interval has passed
    )
]

@callback(
    Output('graph-content', 'figure'),
#    Input('dropdown-selection', 'value')
    Input('interval-component', 'n_intervals')
)
def update_graph(value):
    # Define the column names
    column_names = ['datetime', 'smoker_temp', 'meat_temp']

    # Load the CSV file without a header
    df = pd.read_csv('/home/pi/RT_temperature_dashboard/logs/temperature.log', header=None, names=column_names)

    # Parse the datetime column
    df['datetime'] = pd.to_datetime(df['datetime'], format='%H:%M:%S.%f').dt.time

    return px.line(df, x='datetime', y='meat_temp')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True, threaded=True)
