import numpy as np

def exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Simple exponential smoothing with trend - the sweet spot for BBQ forecasting.
    Balances responsiveness with stability.
    """
    if len(temperatures) < 3:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Simple parameters
    alpha = 0.3  # Smoothing factor (0.2-0.4 works well for BBQ)
    
    # Initialize with first temperature
    smoothed = temperatures[0]
    
    # Apply exponential smoothing
    for temp in temperatures[1:]:
        smoothed = alpha * temp + (1 - alpha) * smoothed
    
    # Simple trend from recent data
    recent_window = min(10, len(temperatures))
    recent_temps = temperatures[-recent_window:]
    
    if len(recent_temps) >= 3:
        # Linear trend over recent window
        trend = (recent_temps[-1] - recent_temps[0]) / (len(recent_temps) - 1)
        # Dampen trend if temperature is stable
        if np.std(recent_temps) < 1.0:
            trend *= 0.3
    else:
        trend = 0
    
    # Generate predictions
    predictions = []
    for step in range(1, future_steps + 1):
        pred = smoothed + trend * step
        predictions.append(pred)
    
    predictions = np.array(predictions)
    
    # Simple confidence bounds
    recent_std = np.std(temperatures[-min(15, len(temperatures)):])
    confidence_width = recent_std * (1.0 + 0.1 * np.arange(1, future_steps + 1))
    
    upper_bound = predictions + confidence_width
    lower_bound = predictions - confidence_width
    
    return predictions, upper_bound, lower_bound

def moving_average_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Simple weighted moving average - best for stable temperatures.
    """
    if len(temperatures) < 3:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Use recent data only
    window_size = min(12, len(temperatures))
    recent_temps = temperatures[-window_size:]
    
    # Simple weighted average (more weight to recent values)
    weights = np.arange(1, window_size + 1)  # 1, 2, 3, ..., window_size
    weights = weights / np.sum(weights)
    current_temp = np.sum(recent_temps * weights)
    
    # Simple trend calculation
    if window_size >= 6:
        early_avg = np.mean(recent_temps[:window_size//2])
        late_avg = np.mean(recent_temps[window_size//2:])
        trend = (late_avg - early_avg) / (window_size // 2)
        
        # Dampen trend if stable
        if np.std(recent_temps) < 1.5:
            trend *= 0.2
    else:
        trend = 0
    
    # Generate predictions
    predictions = []
    for step in range(1, future_steps + 1):
        pred = current_temp + trend * step
        predictions.append(pred)
    
    predictions = np.array(predictions)
    
    # Simple confidence bounds
    std_error = np.std(recent_temps)
    confidence_width = std_error * (0.8 + 0.1 * np.arange(1, future_steps + 1))
    
    upper_bound = predictions + confidence_width
    lower_bound = predictions - confidence_width
    
    return predictions, upper_bound, lower_bound

def simple_trend_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Simple linear trend forecast (fallback method).
    """
    if len(temperatures) < 3:
        return np.array([]), np.array([]), np.array([])
    
    recent_points = min(15, len(temperatures))
    recent_temps = temperatures[-recent_points:]
    recent_times = timestamps[-recent_points:]
    
    # Simple linear regression
    time_diff = np.array(recent_times) - recent_times[0]
    if len(time_diff) > 1 and np.std(time_diff) > 0:
        slope, intercept = np.polyfit(time_diff, recent_temps, 1)
    else:
        slope = 0
        intercept = np.mean(recent_temps)
    
    # Dampen trend if stable
    if np.var(recent_temps) < 1.0:
        slope *= 0.2
    
    current_temp = recent_temps[-1]
    future_time_offsets = np.arange(1, future_steps + 1) * future_dt
    predictions = current_temp + slope * future_time_offsets
    
    std_error = np.std(recent_temps) if len(recent_temps) > 1 else 1.0
    confidence_width = std_error * (1.0 + 0.1 * np.sqrt(future_time_offsets / 60.0))
    
    return predictions, predictions + confidence_width, predictions - confidence_width

def adaptive_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Simple adaptive forecasting - chooses between 3 basic methods.
    """
    if len(temperatures) < 5:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Analyze recent temperature behavior
    recent_temps = temperatures[-min(15, len(temperatures)):]
    variance = np.var(recent_temps)
    
    # Simple decision logic
    if variance < 0.8:  # Very stable - use moving average
        return moving_average_forecast(timestamps, temperatures, future_steps, future_dt)
    else:  # Some variation - use exponential smoothing
        return exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt)

# Main forecasting function - automatically selects best method
def forecast_temperature(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Main temperature forecasting function for BBQ monitoring.
    Automatically selects the best forecasting method based on data characteristics.
    
    Args:
        timestamps: array of timestamps (seconds from start)
        temperatures: array of temperature measurements
        future_steps: number of future steps to predict
        future_dt: time step for future predictions (seconds)
    
    Returns:
        predictions, upper_bound, lower_bound
    """
    return adaptive_forecast(timestamps, temperatures, future_steps, future_dt)

# Backward compatibility - keep the old function name
def kalman_forecast_temperature(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Legacy function name for backward compatibility.
    """
    return forecast_temperature(timestamps, temperatures, future_steps, future_dt)

# Alternative forecasting methods you can use directly:
# - exponential_smoothing_forecast() - Balanced approach for most BBQ scenarios
# - moving_average_forecast() - Best for very stable temperatures  
# - simple_trend_forecast() - Basic linear trend (fallback)
#
# Simplified for BBQ: Just 3 methods that work well for <1hr forecasts
