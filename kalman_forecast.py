import numpy as np
import pandas as pd
from scipy import optimize

def exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Triple Exponential Smoothing (Holt-Winters) for BBQ temperature forecasting.
    Handles level, trend, and seasonality patterns common in cooking.
    """
    if len(temperatures) < 10:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Parameters for exponential smoothing
    alpha = 0.3  # Level smoothing
    beta = 0.2   # Trend smoothing
    gamma = 0.1  # Seasonal smoothing
    
    # Initialize
    level = temperatures[0]
    trend = (temperatures[1] - temperatures[0])
    seasonals = np.zeros(12)  # 12-point seasonal cycle (e.g., 12 minutes)
    
    # Fit the model
    smoothed = []
    for i, temp in enumerate(temperatures):
        if i == 0:
            smoothed.append(level)
            continue
            
        last_level, level = level, alpha * temp + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        
        # Update seasonal component
        season_idx = i % len(seasonals)
        seasonals[season_idx] = gamma * (temp - level) + (1 - gamma) * seasonals[season_idx]
        
        smoothed.append(level + trend + seasonals[season_idx])
    
    # Forecast
    predictions = []
    for step in range(1, future_steps + 1):
        season_idx = (len(temperatures) + step - 1) % len(seasonals)
        pred = level + step * trend + seasonals[season_idx]
        predictions.append(pred)
    
    predictions = np.array(predictions)
    
    # Calculate confidence bounds
    residuals = np.array(temperatures) - np.array(smoothed)
    std_error = np.std(residuals)
    
    time_factor = np.sqrt(np.arange(1, future_steps + 1))
    confidence_width = std_error * (1.0 + 0.3 * time_factor)
    
    upper_bound = predictions + confidence_width
    lower_bound = predictions - confidence_width
    
    return predictions, upper_bound, lower_bound

def exponential_decay_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Exponential approach to target temperature - good for BBQ heating/cooling curves.
    Models temperature as approaching an asymptotic target.
    """
    if len(temperatures) < 5:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Use recent data
    recent_points = min(30, len(temperatures))
    recent_temps = np.array(temperatures[-recent_points:])
    recent_times = np.array(timestamps[-recent_points:]) - timestamps[-recent_points]
    
    # Fit exponential model: T(t) = T_target + (T0 - T_target) * exp(-t/tau)
    def exponential_model(t, T_target, T0, tau):
        return T_target + (T0 - T_target) * np.exp(-t / max(tau, 1.0))
    
    try:
        # Initial guesses
        T0_guess = recent_temps[0]
        T_target_guess = recent_temps[-1] + (recent_temps[-1] - recent_temps[0]) * 2
        tau_guess = (recent_times[-1] - recent_times[0]) / 2
        
        # Fit the model
        popt, _ = optimize.curve_fit(
            exponential_model, 
            recent_times, 
            recent_temps,
            p0=[T_target_guess, T0_guess, tau_guess],
            maxfev=1000
        )
        
        T_target, T0, tau = popt
        
        # Generate predictions
        last_time = recent_times[-1]
        future_times = last_time + np.arange(1, future_steps + 1) * future_dt
        predictions = exponential_model(future_times, T_target, T0, tau)
        
    except:
        # Fallback to simple trend if fitting fails
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Calculate confidence bounds
    residuals = recent_temps - exponential_model(recent_times, T_target, T0, tau)
    std_error = np.std(residuals)
    
    time_factor = np.sqrt(np.arange(1, future_steps + 1) * future_dt / 60.0)
    confidence_width = std_error * (1.0 + 0.4 * time_factor)
    
    upper_bound = predictions + confidence_width
    lower_bound = predictions - confidence_width
    
    return predictions, upper_bound, lower_bound

def moving_average_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Weighted moving average with trend detection for stable short-term forecasting.
    """
    if len(temperatures) < 5:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Use recent data
    window_size = min(20, len(temperatures))
    recent_temps = np.array(temperatures[-window_size:])
    
    # Create weights that emphasize recent data
    weights = np.exp(np.linspace(-2, 0, window_size))
    weights = weights / np.sum(weights)
    
    # Weighted average
    current_temp = np.sum(recent_temps * weights)
    
    # Calculate weighted trend
    if window_size >= 10:
        mid_point = window_size // 2
        early_avg = np.mean(recent_temps[:mid_point])
        late_avg = np.mean(recent_temps[mid_point:])
        time_span = (window_size // 2) * (timestamps[-1] - timestamps[-window_size]) / (window_size - 1)
        trend = (late_avg - early_avg) / max(time_span, 1.0) if time_span > 0 else 0
    else:
        trend = 0
    
    # Dampen trend if temperature is stabilizing
    recent_variance = np.var(recent_temps[-min(10, len(recent_temps)):])
    if recent_variance < 2.0:
        trend *= 0.3
    
    # Generate predictions
    future_time_offsets = np.arange(1, future_steps + 1) * future_dt
    predictions = current_temp + trend * future_time_offsets
    
    # Calculate confidence bounds
    std_error = np.std(recent_temps)
    time_factor = np.sqrt(future_time_offsets / 60.0)
    confidence_width = std_error * (0.8 + 0.4 * time_factor)
    
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
    Adaptive forecasting that chooses the best method based on data characteristics.
    """
    if len(temperatures) < 10:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Analyze temperature characteristics
    recent_temps = np.array(temperatures[-20:])
    variance = np.var(recent_temps)
    trend_strength = abs(recent_temps[-1] - recent_temps[0]) / len(recent_temps)
    
    # Choose method based on characteristics
    if variance < 1.0:  # Very stable - use moving average
        return moving_average_forecast(timestamps, temperatures, future_steps, future_dt)
    elif trend_strength > 0.5:  # Strong trend - use exponential model
        return exponential_decay_forecast(timestamps, temperatures, future_steps, future_dt)
    else:  # Mixed behavior - use exponential smoothing
        return exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt)

# Main forecasting function - automatically selects best method
def kalman_forecast_temperature(timestamps, temperatures, future_steps, future_dt=1.0):
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

# Alternative forecasting methods you can use directly:
# - exponential_smoothing_forecast() - Best for data with patterns/seasonality
# - exponential_decay_forecast() - Best for heating/cooling curves
# - moving_average_forecast() - Best for stable temperatures
# - simple_trend_forecast() - Fallback method
