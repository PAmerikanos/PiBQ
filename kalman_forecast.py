import numpy as np
import pandas as pd
from scipy import optimize

def double_exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Double Exponential Smoothing (Holt's method) for BBQ temperature forecasting.
    Handles level and trend only - no seasonality needed for BBQ.
    Best for short-term forecasting with trending data.
    """
    if len(temperatures) < 5:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Parameters for exponential smoothing (optimized for BBQ)
    alpha = 0.4  # Level smoothing - higher for responsiveness
    beta = 0.3   # Trend smoothing - moderate for stability
    
    # Initialize
    level = temperatures[0]
    trend = temperatures[1] - temperatures[0] if len(temperatures) > 1 else 0
    
    # Fit the model
    smoothed = [level]
    for i in range(1, len(temperatures)):
        temp = temperatures[i]
        last_level = level
        level = alpha * temp + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        smoothed.append(level)
    
    # Generate predictions
    predictions = []
    for step in range(1, future_steps + 1):
        pred = level + step * trend
        predictions.append(pred)
    
    predictions = np.array(predictions)
    
    # Calculate confidence bounds based on recent forecast errors
    if len(temperatures) > 3:
        recent_errors = np.array(temperatures[1:]) - np.array(smoothed[1:])
        std_error = np.std(recent_errors[-min(15, len(recent_errors)):])
    else:
        std_error = 1.0
    
    # Conservative confidence bounds for short-term forecasting
    time_factor = np.sqrt(np.arange(1, future_steps + 1) * future_dt / 60.0)
    confidence_width = std_error * (1.0 + 0.2 * time_factor)
    
    upper_bound = predictions + confidence_width
    lower_bound = predictions - confidence_width
    
    return predictions, upper_bound, lower_bound

def exponential_decay_forecast(timestamps, temperatures, future_steps, future_dt=1.0):
    """
    Exponential approach to target temperature - excellent for BBQ heating/cooling curves.
    Models temperature as: T(t) = T_target + (T0 - T_target) * exp(-t/tau)
    Perfect for meat approaching target temperature or grill cooling down.
    """
    if len(temperatures) < 6:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Use recent data (enough for good fit, not too much for responsiveness)
    recent_points = min(25, len(temperatures))
    recent_temps = np.array(temperatures[-recent_points:])
    recent_times = np.array(timestamps[-recent_points:])
    
    # Normalize time to start from 0
    time_normalized = recent_times - recent_times[0]
    
    # Exponential model function
    def exponential_model(t, T_target, T0, tau):
        return T_target + (T0 - T_target) * np.exp(-t / max(tau, 0.1))
    
    try:
        # Better initial guesses for BBQ scenarios
        T0_guess = recent_temps[0]
        
        # Target temp: extrapolate current trend or use recent average
        recent_trend = (recent_temps[-1] - recent_temps[0]) / max(time_normalized[-1], 1.0)
        if abs(recent_trend) > 0.1:  # If there's a trend
            T_target_guess = recent_temps[-1] + recent_trend * 300  # Extrapolate 5 min ahead
        else:  # If stable, assume current is target
            T_target_guess = np.mean(recent_temps[-5:])
        
        # Time constant: estimate from data length
        tau_guess = time_normalized[-1] / 3.0  # About 1/3 of the observation period
        
        # Constrain the fit to reasonable bounds for BBQ
        bounds = (
            [min(recent_temps) - 20, min(recent_temps) - 10, 1.0],    # Lower bounds
            [max(recent_temps) + 50, max(recent_temps) + 10, 3600.0]  # Upper bounds (max 1hr time constant)
        )
        
        # Fit the model with bounds
        popt, pcov = optimize.curve_fit(
            exponential_model, 
            time_normalized, 
            recent_temps,
            p0=[T_target_guess, T0_guess, tau_guess],
            bounds=bounds,
            maxfev=2000
        )
        
        T_target, T0, tau = popt
        
        # Generate predictions
        last_time = time_normalized[-1]
        future_times = last_time + np.arange(1, future_steps + 1) * future_dt
        predictions = exponential_model(future_times, T_target, T0, tau)
        
        # Calculate goodness of fit
        fitted_temps = exponential_model(time_normalized, T_target, T0, tau)
        fit_error = np.std(recent_temps - fitted_temps)
        
        # If fit is poor, fall back to simpler method
        if fit_error > np.std(recent_temps) * 0.8:  # Fit doesn't explain much variance
            return double_exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt)
        
    except:
        # Fallback if fitting fails
        return double_exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Calculate confidence bounds based on fit quality
    time_factor = np.sqrt(np.arange(1, future_steps + 1) * future_dt / 60.0)
    confidence_width = fit_error * (1.0 + 0.3 * time_factor)
    
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
    Adaptive forecasting optimized for BBQ temperature monitoring.
    Chooses the best method based on data characteristics - no seasonality.
    """
    if len(temperatures) < 8:
        return simple_trend_forecast(timestamps, temperatures, future_steps, future_dt)
    
    # Analyze recent temperature characteristics
    recent_temps = np.array(temperatures[-min(25, len(temperatures)):])
    variance = np.var(recent_temps)
    
    # Calculate trend strength over recent data
    if len(recent_temps) > 5:
        early_half = recent_temps[:len(recent_temps)//2]
        late_half = recent_temps[len(recent_temps)//2:]
        trend_strength = abs(np.mean(late_half) - np.mean(early_half))
    else:
        trend_strength = 0
    
    # Choose method based on BBQ-specific characteristics
    if variance < 0.5:  # Very stable temperature - use moving average
        return moving_average_forecast(timestamps, temperatures, future_steps, future_dt)
    elif trend_strength > 2.0 and len(temperatures) > 10:  # Strong trend - use exponential model
        return exponential_decay_forecast(timestamps, temperatures, future_steps, future_dt)
    else:  # Moderate trend/noise - use double exponential smoothing
        return double_exponential_smoothing_forecast(timestamps, temperatures, future_steps, future_dt)

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
# - double_exponential_smoothing_forecast() - Best for trending data with noise
# - exponential_decay_forecast() - Best for heating/cooling curves approaching target
# - moving_average_forecast() - Best for very stable temperatures
# - simple_trend_forecast() - Simple linear trend (fallback method)
#
# For BBQ temperature forecasting (<1hr), recommended priority:
# 1. Double exponential smoothing - handles trend + noise well
# 2. Exponential decay - good for approach-to-target behavior
# 3. Moving average - best for stable cooking temperatures
