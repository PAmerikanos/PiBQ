import numpy as np
import pandas as pd

def simple_trend_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Simple and robust temperature forecasting for BBQ monitoring.
    Uses linear trend with exponential smoothing for steady-state detection.
    
    Args:
        timestamps: array of timestamps (seconds from start)
        temperatures: array of temperature measurements
        future_steps: number of future steps to predict
        future_dt: time step for future predictions (seconds)
    
    Returns:
        predictions, upper_bound, lower_bound
    """
    
    if len(temperatures) < 3:
        # Not enough data for forecasting
        return np.array([]), np.array([]), np.array([])
    
    # Use recent data for trend analysis (last 30-50 points or all if less)
    recent_points = min(50, len(temperatures))
    recent_temps = temperatures[-recent_points:]
    recent_times = timestamps[-recent_points:]
    
    # Calculate simple linear trend
    time_diff = recent_times - recent_times[0]
    
    # Fit linear regression manually (more stable than polyfit)
    n = len(recent_temps)
    sum_x = np.sum(time_diff)
    sum_y = np.sum(recent_temps)
    sum_xy = np.sum(time_diff * recent_temps)
    sum_x2 = np.sum(time_diff ** 2)
    
    # Calculate slope (trend) and intercept
    if sum_x2 > 0:
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
    else:
        slope = 0.0
        intercept = np.mean(recent_temps)
    
    # Detect if temperature is in steady state
    temp_variance = np.var(recent_temps[-min(20, len(recent_temps)):])
    is_steady_state = temp_variance < 1.0  # Less than 1°C variance
    
    # If steady state, reduce trend influence
    if is_steady_state:
        slope *= 0.1  # Heavily dampen the trend
    
    # Current temperature (smoothed)
    current_temp = np.mean(recent_temps[-3:])  # Average of last 3 readings
    
    # Generate predictions
    future_time_offsets = np.arange(1, future_steps + 1) * future_dt
    predictions = current_temp + slope * future_time_offsets
    
    # Calculate confidence bounds based on recent temperature variability
    if len(recent_temps) > 5:
        recent_std = np.std(recent_temps[-10:])  # Standard deviation of last 10 points
    else:
        recent_std = 0.5
    
    # Confidence bounds grow with time (uncertainty increases)
    time_factor = np.sqrt(future_time_offsets / 60.0)  # Sqrt of minutes
    confidence_width = recent_std * (1.0 + 0.5 * time_factor)
    
    upper_bound = predictions + confidence_width
    lower_bound = predictions - confidence_width
    
    return predictions, upper_bound, lower_bound

# Keep the original function name for compatibility
def kalman_forecast_temperature(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Wrapper function that calls the simple trend forecast
    (renamed from Kalman for compatibility with existing code)
    """
    return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
