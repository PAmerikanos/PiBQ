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

def convert_to_time(future_times_seconds_array, min_datetime_reference):
    """Converts an array of future times (in seconds) back to time strings.

    Args:
        future_times_seconds_array: NumPy array of future time offsets in seconds.
        min_datetime_reference: The minimum datetime reference for converting seconds back to datetime objects.

    Returns:
        A list of time strings in HH:MM:SS.f format.
    """
    # Reverse transformation for future_times
    # Convert the future_times back to seconds
    future_times_seconds_flat = future_times_seconds_array.flatten()
    
    # Convert seconds to datetime by adding the minimum datetime
    future_datetimes = [min_datetime_reference + pd.Timedelta(seconds=sec) for sec in future_times_seconds_flat]
    
    # Convert datetime to HH:MM:SS.f format
    future_time_strings = [dt.strftime('%H:%M:%S.%f')[:-3] for dt in future_datetimes]
    
    return future_time_strings

def forecast_temperature(temperature_series, time_steps_seconds_array, past_steps_count, future_times_seconds_array):
    """Forecasts temperature using polynomial regression.

    Args:
        temperature_series: Pandas Series of temperature data.
        time_steps_seconds_array: NumPy array of time steps in seconds for training.
        past_steps_count: Number of past data points to use for training.
        future_times_seconds_array: NumPy array of future time steps in seconds for prediction.

    Returns:
        A tuple containing:
            - future_predictions: NumPy array of predicted temperatures.
            - upper_bound: NumPy array of the upper confidence interval.
            - lower_bound: NumPy array of the lower confidence interval.
    """
    y_train = temperature_series.values[-past_steps_count:]

    # Polynomial Features Transformation (e.g., degree 2 for quadratic regression)
    polynomial_degree = 3
    poly_features = PolynomialFeatures(degree=polynomial_degree)
    time_steps_poly = poly_features.fit_transform(time_steps_seconds_array)

    # Fit the Polynomial Regression Model
    model = LinearRegression()
    model.fit(time_steps_poly, y_train)

    # Predict temperature values on the training set
    y_train_pred = model.predict(time_steps_poly)

    # Calculate the Residual Sum of Squares
    residual_sum_of_squares = np.sum((y_train - y_train_pred) ** 2)
    num_data_points = len(y_train)
    # Mean Squared Error, adjusted for degrees of freedom
    mean_squared_error_val = residual_sum_of_squares / (num_data_points - polynomial_degree - 1)
    root_mean_squared_error = np.sqrt(mean_squared_error_val)            # Root Mean Squared Error

    # Predict for Future Times
    future_times_poly = poly_features.transform(future_times_seconds_array)
    future_predictions = model.predict(future_times_poly)

    # Calculate Confidence Intervals
    # 1.96 corresponds to a 95% confidence interval
    confidence_interval_margin = 1.96 * root_mean_squared_error

    # Upper and lower bounds
    upper_bound = future_predictions + confidence_interval_margin
    lower_bound = future_predictions - confidence_interval_margin

    return future_predictions, upper_bound, lower_bound

def parse_temperature_data():
    """Parses all temperature data from CSV files recorded on the current day.

    The CSV files are expected to be in the './temperature/' directory and named
    with the format YYYYMMDD_*.csv. Each CSV file should have three columns:
    datetime, smoker_temp, meat_temp, without a header row.

    Returns:
        A pandas DataFrame containing the combined temperature data from all
        relevant CSV files.
    """
    # Get today's date in YYYYMMDD format
    today_date_str = datetime.now().strftime('%Y%m%d')

    # Define the path to the folder
    data_folder_path = './temperature/'

    # List all files in the directory
    try:
        all_files = os.listdir(data_folder_path)
    except FileNotFoundError:
        # If the directory doesn't exist, return an empty DataFrame
        return pd.DataFrame(columns=['datetime', 'smoker_temp', 'meat_temp'])


    # Filter files that start with today's date and end with .csv
    csv_files_today = [f for f in all_files if f.startswith(today_date_str) and f.endswith('.csv')]
    csv_files_today.sort()

    # List to hold dataframes
    dataframe_list = []

    # Load each csv file into a dataframe and append to list
    for csv_file_name in csv_files_today:
        file_path = os.path.join(data_folder_path, csv_file_name)
        try:
            df = pd.read_csv(file_path, header=None, names=['datetime', 'smoker_temp', 'meat_temp'])
            dataframe_list.append(df)
        except pd.errors.EmptyDataError:
            # Skip empty CSV files
            print(f"Warning: Skipping empty CSV file: {file_path}")
            continue


    # Concatenate all dataframes into a single dataframe
    if not dataframe_list:
        # Return an empty DataFrame if no valid CSV files were found
        return pd.DataFrame(columns=['datetime', 'smoker_temp', 'meat_temp'])

    combined_data_df = pd.concat(dataframe_list, ignore_index=True)

    # Return the combined dataframe
    return combined_data_df


app = Dash(__name__)

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
    Input("past_minutes", "value"), # Number of past minutes to use for prediction base
    Input("forecast_minutes", "value"), # Number of future minutes to forecast
    Input("rolling_avg_window", "value") # Window size for rolling average
)
def update_graph(n_clicks, smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes, rolling_avg_window):
    """
    Updates the graph with current and forecasted temperature data.

    This function is a Dash callback triggered by user inputs. It handles data parsing,
    preprocessing, forecasting, and plotting.
    """
    # Pass input values directly to the helper function
    processed_data = _prepare_temperature_data(
        rolling_avg_window,
        past_minutes,
        forecast_minutes
    )
    if isinstance(processed_data, go.Figure):  # Error case, return figure directly
        return processed_data

    temperature_df, num_past_steps, num_forecast_steps = processed_data

    # Ensure there's enough data for the 'past_steps'
    if len(temperature_df) < num_past_steps:
        return go.Figure(layout=dict(title=f"Not enough data for {past_minutes} minutes of history. Need {num_past_steps} data points, have {len(temperature_df)}."))

    training_time_in_seconds, future_times_reshaped, future_time_strings = _prepare_time_series_for_forecast(
        temperature_df, num_past_steps, num_forecast_steps
    )

    # Forecast temperatures
    smoker_forecast, smoker_upper_bound, smoker_lower_bound = forecast_temperature(
        temperature_df['smoker_temp'], training_time_in_seconds, num_past_steps, future_times_reshaped
    )
    meat_forecast, meat_upper_bound, meat_lower_bound = forecast_temperature(
        temperature_df['meat_temp'], training_time_in_seconds, num_past_steps, future_times_reshaped
    )

    # Create the plot
    fig = _create_temperature_plot(
        temperature_df, num_past_steps, future_time_strings,
        smoker_forecast, smoker_upper_bound, smoker_lower_bound,
        meat_forecast, meat_upper_bound, meat_lower_bound,
        smoker_target_temp, meat_min_temp
    )

    return fig


def _prepare_temperature_data(rolling_avg_window, past_minutes_input, forecast_minutes_input):
    """
    Loads, parses, and preprocesses temperature data.

    Args:
        rolling_avg_window: Window size for calculating the rolling average.
        past_minutes_input: Number of past minutes of data to use.
        forecast_minutes_input: Number of minutes into the future to forecast.

    Returns:
        A tuple (temperature_df, num_past_steps, num_forecast_steps) or a go.Figure on error.
    """
    temperature_df = parse_temperature_data()
    if temperature_df.empty:
        return go.Figure(layout=dict(title="No temperature data available for today."))

    temperature_df['datetime'] = pd.to_datetime(temperature_df['datetime'], format='mixed').dt.strftime('%H:%M:%S')
    # Apply rolling average
    temperature_df['smoker_temp'] = temperature_df['smoker_temp'].rolling(window=rolling_avg_window).mean()
    temperature_df['meat_temp'] = temperature_df['meat_temp'].rolling(window=rolling_avg_window).mean()
    # Drop rows with NA values that were created by the rolling mean, especially at the beginning
    temperature_df.dropna(subset=['smoker_temp', 'meat_temp'], inplace=True)

    if temperature_df.empty:
        return go.Figure(layout=dict(title="Not enough data points after applying rolling average."))

    # Convert minutes to number of data points (assuming 1 data point per second)
    num_past_steps = past_minutes_input * 60
    num_forecast_steps = forecast_minutes_input * 60

    return temperature_df, num_past_steps, num_forecast_steps


def _prepare_time_series_for_forecast(df, num_past_steps, num_forecast_steps):
    """
    Prepares time series data for the forecasting model.

    Args:
        df: Pandas DataFrame with temperature data, including a 'datetime' column.
        num_past_steps: Number of past data points to use for training.
        num_forecast_steps: Number of future data points to predict.

    Returns:
        A tuple containing:
            - training_time_in_seconds: NumPy array of time steps for training.
            - future_times_reshaped: NumPy array of future time steps for prediction.
            - future_time_strings: List of future time strings for plotting.
    """
    # Convert datetime strings to datetime objects
    datetime_objects = pd.to_datetime(df['datetime'], format='%H:%M:%S.%f')
    # Convert datetimes to seconds since the first record for numerical modeling
    time_in_seconds = (datetime_objects - datetime_objects.min()).dt.total_seconds().values.reshape(-1, 1)

    # Select the most recent 'num_past_steps' for training data
    training_time_in_seconds = time_in_seconds[-num_past_steps:]

    # Generate future time steps for prediction
    # Start from the second after the last recorded time
    last_recorded_time_seconds = training_time_in_seconds[-1][0]
    future_time_offsets_seconds = np.arange(1, num_forecast_steps + 1) # e.g., 1s, 2s, ... up to num_forecast_steps
    future_times_absolute_seconds = last_recorded_time_seconds + future_time_offsets_seconds
    future_times_reshaped = future_times_absolute_seconds.reshape(-1, 1) # Reshape for model input

    # Convert future time seconds back to HH:MM:SS.f strings for plotting
    min_datetime_reference = datetime_objects.min() # Use the first datetime as a reference point
    future_time_strings = convert_to_time(future_times_reshaped, min_datetime_reference)

    return training_time_in_seconds, future_times_reshaped, future_time_strings


def _create_temperature_plot(df, num_past_steps, future_time_strings,
                             smoker_forecast, smoker_upper_bound, smoker_lower_bound,
                             meat_forecast, meat_upper_bound, meat_lower_bound,
                             smoker_target_temp, meat_min_temp):
    """
    Creates the Plotly figure for displaying temperature data and forecasts.

    Args:
        df: DataFrame containing historical temperature data.
        num_past_steps: Number of past data points used for prediction base.
        future_time_strings: List of time strings for the x-axis of forecast data.
        smoker_forecast: Array of forecasted smoker temperatures.
        smoker_upper_bound: Array for smoker forecast upper confidence bound.
        smoker_lower_bound: Array for smoker forecast lower confidence bound.
        meat_forecast: Array of forecasted meat temperatures.
        meat_upper_bound: Array for meat forecast upper confidence bound.
        meat_lower_bound: Array for meat forecast lower confidence bound.
        smoker_target_temp: Target temperature for the smoker.
        meat_min_temp: Minimum target temperature for the meat.

    Returns:
        A Plotly Figure object.
    """
    fig = go.Figure()

    # Plotting historical temperature data
    # Full history
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', line=dict(color='blue'), name='Smoker Temp (All)')
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', line=dict(color='red'), name='Meat Temp (All)')
    # Highlighted portion used for prediction
    fig.add_scatter(x=df["datetime"].tail(num_past_steps), y=df["smoker_temp"].tail(num_past_steps), mode='lines', line=dict(color='magenta', width=2), name='Smoker Temp (for Prediction)')
    fig.add_scatter(x=df["datetime"].tail(num_past_steps), y=df["meat_temp"].tail(num_past_steps), mode='lines', line=dict(color='purple', width=2), name='Meat Temp (for Prediction)')

    # Add target temperature lines
    if smoker_target_temp is not None:
        fig.add_hline(y=smoker_target_temp, line_width=1, line_color="blue", line_dash="dash", name="Smoker Target Temp")
    if meat_min_temp is not None:
        fig.add_hline(y=meat_min_temp, line_width=1, line_color="red", line_dash="dash", name="Meat Min Temp")

    # Plotting predicted temperature values with confidence intervals
    # Smoker Temperature Forecast
    fig.add_scatter(x=future_time_strings, y=smoker_forecast, mode='lines', line=dict(color='cyan'), name='Predicted Smoker Temp')
    fig.add_scatter(x=future_time_strings, y=smoker_lower_bound, mode='lines', line=dict(width=0), showlegend=False)
    fig.add_scatter(x=future_time_strings, y=smoker_upper_bound, mode='lines', fill='tonexty', fillcolor='rgba(0, 255, 255, 0.2)', line=dict(width=0), name='Smoker Confidence Interval')

    # Meat Temperature Forecast
    fig.add_scatter(x=future_time_strings, y=meat_forecast, mode='lines', line=dict(color='pink'), name='Predicted Meat Temp')
    fig.add_scatter(x=future_time_strings, y=meat_lower_bound, mode='lines', line=dict(width=0), showlegend=False)
    fig.add_scatter(x=future_time_strings, y=meat_upper_bound, mode='lines', fill='tonexty', fillcolor='rgba(255, 105, 180, 0.2)', line=dict(width=0), name='Meat Confidence Interval')

    # Update layout labels and overall appearance
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Temperature (C)',
        xaxis=dict(tickangle=270), # Rotate x-axis labels for better readability
        legend=dict(
            x=0.01, y=0.01, # Position legend at bottom-left
            xanchor='left', yanchor='bottom',
            bgcolor='rgba(255, 255, 255, 0.6)' # Semi-transparent background
        ),
        margin=dict(l=40, r=40, t=40, b=40) # Adjust margins for a tighter layout
    )
    return fig


if __name__ == '__main__':
    # Ensure the temperature data directory exists before starting the app
    temperature_data_dir = './temperature/'
    if not os.path.exists(temperature_data_dir):
        os.makedirs(temperature_data_dir)
        print(f"Created directory: {temperature_data_dir}")
    app.run(host='0.0.0.0', port=8050, debug=True, threaded=True)
