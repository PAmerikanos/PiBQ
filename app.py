from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objs as go
import numpy as np
import pandas as pd
from helpers import convert_to_time, forecast_temperature, parse_temperature_data


app = Dash(assets_folder='assets')
app.title = 'PiBQ - Meat Monitoring'

app.layout = [
    # Header with logo and title
    html.Div([
        html.Img(
            src='/assets/logo.png',
            style={
                'height': '30px',
                'marginRight': '15px',
                'verticalAlign': 'middle'
            }
        ),
        html.H1(
            'PiBQ',
            style={
                'display': 'inline-block',
                'verticalAlign': 'middle',
                'margin': '0',
                'color': '#666666',
                'fontFamily': 'Monaco, "Lucida Console", "Courier New", Courier, monospace',
                'fontSize': '30px',
                'fontWeight': 'bold',
                'textShadow': '1px 1px 2px #cccccc'
            }
        )
    ], style={
        'textAlign': 'center',
        'padding': '20px',
        'backgroundColor': '#f8f9fa',
        'borderBottom': '2px solid #dddddd',
        'marginBottom': '20px'
    }),

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
]

@callback(
    Output('graph-content', 'figure'),
    Input('update-button', 'n_clicks'),
    Input("smoker_target_temp", "value"),
    Input("meat_min_temp", "value"),
    Input("past_minutes", "value"),
    Input("forecast_minutes", "value"),
    Input("rolling_avg_window", "value")
)
def update_graph(n_clicks, smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes, rolling_avg_window):
    # Parse temperature data
    df = parse_temperature_data()
    df['datetime'] = pd.to_datetime(df['datetime'], format='mixed').dt.strftime('%H:%M:%S.%f')
    df['smoker_temp'] = df['smoker_temp'].rolling(window=rolling_avg_window).mean()
    df['meat_temp'] = df['meat_temp'].rolling(window=rolling_avg_window).mean()
    df.dropna(how='any', inplace=True)


    past_steps = past_minutes * 60
    forecast_steps = forecast_minutes * 60

    # # Display only last 10 minutes
    # date_time = df['datetime'].tail(past_steps).to_list()
    # smoker_temp = df['smoker_temp'].tail(past_steps).to_list()
    # meat_temp = df['meat_temp'].tail(past_steps).to_list()

    # # Forecast temps
    # smoker_forecast, smoker_confidence_intervals = forecast_temperature(smoker_temp, forecast_steps)
    # meat_forecast, meat_confidence_intervals = forecast_temperature(meat_temp, forecast_steps)

    # # Generate future time indices for the forecast
    # future_times = pd.date_range(start=date_time[-1], periods=forecast_steps + 1, freq='s')[1:].time


    # Reshape the data to fit the model
    full_time = pd.to_datetime(df['datetime'], format='%H:%M:%S.%f')
    full_time = (full_time - full_time.min()).dt.total_seconds().values.reshape(-1, 1)
    X = full_time[-past_steps:]

    # Predict for Future Times
    last_value = X[-1] if np.isscalar(X[-1]) else X[-1][0]
    int_list = range(int(last_value) + 1, int(last_value) + forecast_steps)
    future_times = np.array([float(i) for i in int_list]).reshape(-1, 1)

    full_time_min = pd.to_datetime(df['datetime'], format='%H:%M:%S.%f').min()  # define this based on your data
    future_time_strings = convert_to_time(future_times, full_time_min)

    smoker_forecast, smoker_upper_bound, smoker_lower_bound = forecast_temperature(df['smoker_temp'], X, past_steps, future_times)
    meat_forecast, meat_upper_bound, meat_lower_bound = forecast_temperature(df['meat_temp'], X, past_steps, future_times)

    fig = go.Figure()

    # Past temperature values
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', line=dict(color='blue'), 
                   name='Full history', legendgroup='smoker', legendgrouptitle_text="Smoker")
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', line=dict(color='red'), 
                   name='Full history', legendgroup='meat', legendgrouptitle_text="Meat")

    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["smoker_temp"].tail(past_steps), mode='lines', 
                   line=dict(color='magenta'), name='Rolling window', legendgroup='smoker')
    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["meat_temp"].tail(past_steps), mode='lines', 
                   line=dict(color='purple'), name='Rolling window', legendgroup='meat')

    # Target temperature values
    fig.add_hline(y=smoker_target_temp, line_width=1, line_color="blue", line_dash="dash")
    fig.add_hline(y=meat_min_temp, line_width=1, line_color="red", line_dash="dash")

    # Predicted temperature values with confidence intervals
    # Smoker Temperature
    fig.add_scatter(x=future_time_strings, y=smoker_forecast, mode='lines', line=dict(color='cyan'), 
                   name='Prediction values', legendgroup='smoker')

    # Meat Temperature
    fig.add_scatter(x=future_time_strings, y=meat_forecast, mode='lines', line=dict(color='pink'), 
                   name='Prediction values', legendgroup='meat')
    #fig.add_scatter(x=future_time_strings, y=meat_confidence_intervals[:, 0], mode='lines', line=dict(width=0), showlegend=False)
    #fig.add_scatter(x=future_time_strings, y=meat_confidence_intervals[:, 1], mode='lines', fill='tonexty', fillcolor='rgba(255, 105, 180, 0.3)', line=dict(width=0), showlegend=False)


#    # plt.scatter(full_time, df['smoker_temp'], color='yellow', label='All recorded temperatures')
#    # plt.scatter(X, y, color='blue', label='Observed data')
#    # plt.plot(X, y_pred, color='green', label='Polynomial fit')
#    # plt.scatter(future_times, future_predictions, color='red', label='Predicted future values')
    # plt.fill_between(future_times.flatten(), lower_bound, upper_bound, color='gray', alpha=0.5, label='Confidence Interval')


    # Update layout labels
    fig.update_layout(
#        width=1280,  # Set the width of the figure
#        height=720,  # Set the height of the figure
        xaxis_title='Time',
        yaxis_title='Temperature',
        xaxis=dict(
            tickangle=270  # Rotate x-axis labels by 180 degrees
        ),
#        yaxis=dict(
#            tickmode='linear',  # Set tick mode to linear
#            tick0=0,            # Starting tick (0 for integers starting from 0)
#            dtick=1,            # Interval of 1 for every integer
#            nticks=20           # Increase the number of gridlines on the y-axis
#        ),
        legend=dict(
            x=0.02,  # x-coordinate of the legend (0.02 is slightly from left edge)
            y=0.02,  # y-coordinate of the legend (0.02 is slightly from bottom)
            xanchor='left',  # anchor legend to the left
            yanchor='bottom',  # anchor legend to the bottom
            bgcolor='rgba(255, 255, 255, 0.8)',  # Semi-transparent background
            bordercolor='rgba(0, 0, 0, 0.2)',  # Light border
            borderwidth=1,
            orientation='v',  # vertical orientation for better column control
            tracegroupgap=10,  # gap between trace groups
            itemsizing='constant',  # consistent item sizing
            itemwidth=30,  # width of legend items
            font=dict(size=10)  # font size for legend text
        )
    )

    return fig


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
