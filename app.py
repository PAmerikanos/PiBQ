from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objs as go
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import numpy as np
import pandas as pd
import os
from datetime import datetime


# def forecast_temperature(temp, fsteps):
#     # Fit an ARIMA model and predict the next forecast_steps with confidence intervals
#     model = ARIMA(temp, order=(5,1,0))
#     model_fit = model.fit()
#     forecast_result = model_fit.get_forecast(steps=fsteps)
#     forecast = forecast_result.predicted_mean
#     confidence_intervals = forecast_result.conf_int()

#     return forecast, confidence_intervals

def convert_to_time(future_times, full_time_min):
    # Reverse transformation for future_times
    # Convert the future_times back to seconds
    future_times_seconds = future_times.flatten()
    
    # Convert seconds to datetime by adding the minimum datetime
    future_datetimes = [full_time_min + pd.Timedelta(seconds=sec) for sec in future_times_seconds]
    
    # Convert datetime to HH:MM:SS.f format
    future_time_strings = [dt.strftime('%H:%M:%S.%f')[:-3] for dt in future_datetimes]
    
    return future_time_strings

def forecast_temperature(temp_data, X, past_steps, future_times):
    y = temp_data.values[-past_steps:]

    # Polynomial Features Transformation (e.g., degree 2 for quadratic regression)
    degree = 3
    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X)

    # Fit the Polynomial Regression Model
    model = LinearRegression()
    model.fit(X_poly, y)

    # Predict temperature values on the training set
    y_pred = model.predict(X_poly)

    # Calculate the Residual Sum of Squares
    rss = np.sum((y - y_pred) ** 2)
    n = len(y)
    mse = rss / (n - degree - 1)  # Mean Squared Error
    rmse = np.sqrt(mse)            # Root Mean Squared Error

    # Predict for Future Times
    future_times_poly = poly.transform(future_times)
    future_predictions = model.predict(future_times_poly)

    # Calculate Confidence Intervals
    confidence_interval = 1.96 * rmse  # 95% confidence interval

    # Upper and lower bounds
    upper_bound = future_predictions + confidence_interval
    lower_bound = future_predictions - confidence_interval

    return future_predictions, upper_bound, lower_bound

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
    csv_files.sort()

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
def update_graph(smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes, rolling_avg_window):
    # Parse temperature data
    df = parse_temperature_data()
    df['datetime'] = pd.to_datetime(df['datetime'], format='mixed').dt.strftime('%H:%M:%S')
    df['smoker_temp'] = df['smoker_temp'].rolling(window=rolling_avg_window).mean()
    df['meat_temp'] = df['meat_temp'].rolling(window=rolling_avg_window).mean()


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
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', line=dict(color='blue'), name='Smoker Temperature - ALL')
    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["smoker_temp"].tail(past_steps), mode='lines', line=dict(color='magenta'), name='Smoker Temperature - For prediction')
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', line=dict(color='red'), name='Meat Temperature - ALL')
    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["meat_temp"].tail(past_steps), mode='lines', line=dict(color='purple'), name='Meat Temperature- For prediction')

    # Target temperature values
    fig.add_hline(y=smoker_target_temp, line_width=1, line_color="blue", line_dash="dash")
    fig.add_hline(y=meat_min_temp, line_width=1, line_color="red", line_dash="dash")

    # Predicted temperature values with confidence intervals
    # Smoker Temperature
    fig.add_scatter(x=future_time_strings, y=smoker_forecast, mode='lines', line=dict(color='cyan'), name='Predicted Smoker Temperature')
    #fig.add_scatter(x=future_time_strings, y=smoker_confidence_intervals[:, 0], mode='lines', line=dict(width=0), showlegend=False)
    #fig.add_scatter(x=future_time_strings, y=smoker_confidence_intervals[:, 1], mode='lines', fill='tonexty', fillcolor='rgba(0, 255, 255, 0.3)', line=dict(width=0), showlegend=False)

    # Meat Temperature
    fig.add_scatter(x=future_time_strings, y=meat_forecast, mode='lines', line=dict(color='pink'), name='Predicted Meat Temperature')
    #fig.add_scatter(x=future_time_strings, y=meat_confidence_intervals[:, 0], mode='lines', line=dict(width=0), showlegend=False)
    #fig.add_scatter(x=future_time_strings, y=meat_confidence_intervals[:, 1], mode='lines', fill='tonexty', fillcolor='rgba(255, 105, 180, 0.3)', line=dict(width=0), showlegend=False)


#    # plt.scatter(full_time, df['smoker_temp'], color='yellow', label='All recorded temperatures')
#    # plt.scatter(X, y, color='blue', label='Observed data')
#-    # plt.plot(X, y_pred, color='green', label='Polynomial fit')
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
