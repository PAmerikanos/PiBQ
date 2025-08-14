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
    future_time_strings = [pd.to_datetime(dt.strftime('%H:%M:%S')[:-3]) for dt in future_datetimes]
    
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
