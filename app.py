from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objs as go
from statsmodels.tsa.arima.model import ARIMA
import pandas as pd
import os
from datetime import datetime


def forecast_temperature(temp, fsteps):
    # Fit an ARIMA model and predict the next forecast_steps with confidence intervals
    model = ARIMA(temp, order=(5,1,0))
    model_fit = model.fit()
    forecast_result = model_fit.get_forecast(steps=fsteps)
    forecast = forecast_result.predicted_mean
    confidence_intervals = forecast_result.conf_int()

    return forecast, confidence_intervals

def parse_temperature_data():
    # Parse all temperature data from today's sessions

    # Get today's date in YYYYMMDD format
    today_date = datetime.now().strftime('%Y%m%d')

    # Define the path to the folder
    folder_path = './temperature/'

    # List all files in the directory
    all_files = os.listdir(folder_path)

    # Filter files that start with today's date and end with .csv
    csv_files = [f for f in all_files if f.startswith(today_date) and f.endswith('.csv')]

    # List to hold dataframes
    df_list = []

    # Load each csv file into a dataframe and append to list
    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path, header=None, names=['datetime', 'smoker_temp', 'meat_temp'])
        df_list.append(df)

    # Concatenate all dataframes into a single dataframe
    combined_df = pd.concat(df_list, ignore_index=True)

    # Return the combined dataframe
    return combined_df


app = Dash()

app.layout = [
    #html.H1(children='Title of Dash App', style={'textAlign':'center'}),

    dcc.Graph(id='graph-content'),

    html.Div(
        [
            html.Div(
                [
                    #html.Label('Update graph', style={'width': '250px', 'textAlign': 'right', 'marginRight': '10px'}),
                    html.Button('Update graph', id='update-button')
                ],
                style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}
            ),
            html.Div(
                [
                    html.Label('Smoker target temperature (C)', style={'width': '250px', 'textAlign': 'right', 'marginRight': '10px'}),
                    dcc.Input(id='smoker_target_temp', type='number', min=0, max=200, step=1, value=1),
                ],
                style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}
            ),
            html.Div(
                [
                    html.Label('Meat minimum temperature (C)', style={'width': '250px', 'textAlign': 'right', 'marginRight': '10px'}),
                    dcc.Input(id='meat_min_temp', type='number', min=0, max=200, step=1, value=0),
                ],
                style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}
            ),
            html.Div(
                [
                    html.Label('Based on last minutes', style={'width': '250px', 'textAlign': 'right', 'marginRight': '10px'}),
                    dcc.Input(id='past_minutes', type='number', min=0, max=120, step=10, value=10),
                ],
                style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}
            ),
            html.Div(
                [
                    html.Label('Forecast next minutes', style={'width': '250px', 'textAlign': 'right', 'marginRight': '10px'}),
                    dcc.Input(id='forecast_minutes', type='number', min=0, max=120, step=10, value=10),
                ],
                style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}
            ),
            html.Div(
                [
                    html.Label('Rolling average window', style={'width': '250px', 'textAlign': 'right', 'marginRight': '10px'}),
                    dcc.Input(id='rolling_avg_window', type='number', min=1, max=1000, step=1, value=9),
                ],
                style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}
            ),
        ],
        style={
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'justifyContent': 'center',
        }
    )

    # # Interval component for auto-refreshing every 10 sec (300000 milliseconds)
    # dcc.Interval(
    #     id='interval-component',
    #     interval=300*1000,  # 300 seconds = 5 minutes
    #     n_intervals=0  # Number of times the interval has passed
    # )
]

@callback(
    Output('graph-content', 'figure'),
    #Input('interval-component', 'n_intervals'),
    Input('update-button', 'n_clicks'),
    Input("smoker_target_temp", "value"),
    Input("meat_min_temp", "value"),
    Input("past_minutes", "value"),
    Input("forecast_minutes", "value"),
    Input("rolling_avg_window", "value")
)
def update_graph(n_intervals, smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes, rolling_avg_window):
    # Parse temperature data
    df = parse_temperature_data()
    df['datetime'] = pd.to_datetime(df['datetime'], format='mixed').dt.strftime('%H:%M:%S')
    df['smoker_temp'] = df['smoker_temp'].rolling(window=rolling_avg_window).mean()
    df['meat_temp'] = df['meat_temp'].rolling(window=rolling_avg_window).mean()


    past_steps = past_minutes * 60
    forecast_steps = forecast_minutes * 60

    # Display onle last 10 minutes
    date_time = df['datetime'].tail(past_steps).to_list()
    smoker_temp = df['smoker_temp'].tail(past_steps).to_list()
    meat_temp = df['meat_temp'].tail(past_steps).to_list()

    # Forecast temps
    smoker_forecast, smoker_confidence_intervals = forecast_temperature(smoker_temp, forecast_steps)
    meat_forecast, meat_confidence_intervals = forecast_temperature(meat_temp, forecast_steps)

    # Generate future time indices for the forecast
    future_times = pd.date_range(start=date_time[-1], periods=forecast_steps + 1, freq='s')[1:].time


    fig = go.Figure()

    # Past temperature values
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', line=dict(color='blue'), name='Smoker Temperature')
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', line=dict(color='red'), name='Meat Temperature')

    # Target temperature values
    fig.add_hline(y=smoker_target_temp, line_width=1, line_color="blue", line_dash="dash")
    fig.add_hline(y=meat_min_temp, line_width=1, line_color="red", line_dash="dash")

    # Predicted temperature values with confidence intervals
    # Smoker Temperature
    fig.add_scatter(x=future_times, y=smoker_forecast, mode='lines', line=dict(color='cyan'), name='Predicted Smoker Temperature')
    fig.add_scatter(x=future_times, y=smoker_confidence_intervals[:, 0], mode='lines', line=dict(width=0), showlegend=False)
    fig.add_scatter(x=future_times, y=smoker_confidence_intervals[:, 1], mode='lines', fill='tonexty', fillcolor='rgba(0, 255, 255, 0.3)', line=dict(width=0), showlegend=False)

    # Meat Temperature
    fig.add_scatter(x=future_times, y=meat_forecast, mode='lines', line=dict(color='pink'), name='Predicted Meat Temperature')
    fig.add_scatter(x=future_times, y=meat_confidence_intervals[:, 0], mode='lines', line=dict(width=0), showlegend=False)
    fig.add_scatter(x=future_times, y=meat_confidence_intervals[:, 1], mode='lines', fill='tonexty', fillcolor='rgba(255, 105, 180, 0.3)', line=dict(width=0), showlegend=False)


    # Update layout labels
    fig.update_layout(
        width=1280,  # Set the width of the figure
        height=720,  # Set the height of the figure
        xaxis_title='Time',
        yaxis_title='Temperature',
        xaxis=dict(
            tickangle=180  # Rotate x-axis labels by 180 degrees
        ),
        yaxis=dict(
            tickmode='linear',  # Set tick mode to linear
            tick0=0,            # Starting tick (0 for integers starting from 0)
            dtick=1,            # Interval of 1 for every integer
            nticks=20           # Increase the number of gridlines on the y-axis
        ),
        legend=dict(
            x=0,  # x-coordinate of the legend (0 is far left)
            y=0,  # y-coordinate of the legend (0 is bottom)
            xanchor='left',  # anchor legend to the left
            yanchor='bottom',  # anchor legend to the bottom
            bgcolor='rgba(255, 255, 255, 0.5)'  # Optional: semi-transparent background
        )
    )

    return fig


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True, threaded=True)
