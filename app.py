from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objs as go
import numpy as np
import pandas as pd
from helpers import convert_to_time, forecast_temperature, enhanced_forecast_temperature, parse_temperature_data


app = Dash(__name__, assets_folder='assets', external_stylesheets=['/assets/styles.css'])
app.title = 'PiBQ - BBQ monitoring dashboard'

# Add custom favicon
app._favicon = 'favicon.png'

app.layout = html.Div([
    # Main container with sidebar layout
    html.Div([
        # Sidebar - will stack vertically on mobile
        html.Div([
            # Header with logo and title
            html.Div([
                html.Img(
                    src='/assets/logo.png',
                    className='logo'
                ),
                html.H1(
                    'PiBQ',
                    className='title'
                ),
                html.P(
                    'BBQ monitoring dashboard',
                    className='subtitle'
                )
            ], className='header'),

            # Current Temperature Display
            html.Div([
                html.H3('Current Temps', className='section-header section-header-small'),
                html.Div([
                    html.Div([
                        html.Span('🔥', className='temp-icon'),
                        html.Span('Smoker:', className='temp-label'),
                        html.Div(id='current-smoker-temp', children='--°C', className='temp-value smoker-temp')
                    ], className='temp-display'),
                    html.Div([
                        html.Span('🥩', className='temp-icon'),
                        html.Span('Meat:', className='temp-label'),
                        html.Div(id='current-meat-temp', children='--°C', className='temp-value meat-temp')
                    ], className='temp-display')
                ])
            ], className='card'),

            # Update Button
            html.Div([
                html.Button('Update Dashboard', id='update-button', className='button')
            ], className='button-container'),

            # Temperature Settings
            html.Div([
                html.H3('Target Temps', className='section-header section-header-small'),
                html.Div([
                    html.Label('Smoker Target (°C)', className='input-label'),
                    html.Div([
                        dcc.Input(id='smoker_target_temp', type='number', min=0, step=1, value=120, className='input-field'),
                        html.Span('ⓘ', 
                                 title="120/74°C for chicken\n130/63°C for spare ribs",
                                 style={'marginLeft': '5px', 'cursor': 'help', 'color': '#666'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ], className='input-group'),
                html.Div([
                    html.Label('Meat Minimum (°C)', className='input-label'),
                    dcc.Input(id='meat_min_temp', type='number', min=0, step=1, value=74, className='input-field')
                ], className='input-group')
            ], className='card'),

            # Analysis Settings
            html.Div([
                html.H3('Forecast Temps', className='section-header section-header-small'),
                html.Div([
                    html.Label('History Window (min)', className='input-label'),
                    dcc.Input(id='past_minutes', type='number', min=0, step=1, value=10, className='input-field')
                ], className='input-group'),
                html.Div([
                    html.Label('Forecast (min)', className='input-label'),
                    dcc.Input(id='forecast_minutes', type='number', min=0, step=1, value=10, className='input-field')
                ], className='input-group'),
                html.Div([
                    html.Label('Smoothing Window (samples)', className='input-label'),
                    dcc.Input(id='rolling_avg_window', type='number', min=1, max=1000, step=1, value=9, className='input-field')
                ], className='input-group')
            ], className='card'),

            # Session Settings
            html.Div([
                html.H3('Session Settings', className='section-header section-header-small'),
                html.Div([
                    html.Label('Previous Days', className='input-label'),
                    html.Div([
                        dcc.Input(id='previous_days', type='number', min=0, step=1, value=0, className='input-field'),
                        html.Span('ⓘ', 
                                 title="0: Latest session\n1: Today's sessions\nX: Sessions from last X days",
                                 style={'marginLeft': '5px', 'cursor': 'help', 'color': '#666'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ], className='input-group'),
                html.Div([
                    html.Label('UTC Offset (hours)', className='input-label'),
                    html.Div([
                        dcc.Input(id='utc_offset', type='number', step=1, value=3, className='input-field'),
                        html.Span('ⓘ', 
                                 title="+3 for EEST\n+2 for EET",
                                 style={'marginLeft': '5px', 'cursor': 'help', 'color': '#666'})
                    ], style={'display': 'flex', 'alignItems': 'center'})
                ], className='input-group')
            ], className='card')

        ], className='sidebar'),

        # Main content area
        html.Div([
            dcc.Graph(id='graph-content', className='graph-container')
        ], className='main-content')

    ], className='main-container'),

    # Hidden timer for auto-refresh every 60 seconds
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # in milliseconds (60 seconds)
        n_intervals=0
    )

])

def create_empty_figure(message="No data available"):
    """Create an empty figure with error message"""
    fig = go.Figure()
    fig.add_annotation(
        x=0.5, y=0.5,
        text=message,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=16, color="red")
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    return fig

@callback(
    [Output('graph-content', 'figure'),
     Output('current-smoker-temp', 'children'),
     Output('current-meat-temp', 'children')],
    [Input('update-button', 'n_clicks'),
     Input('interval-component', 'n_intervals'),
     Input("smoker_target_temp", "value"),
     Input("meat_min_temp", "value"),
     Input("past_minutes", "value"),
     Input("forecast_minutes", "value"),
     Input("rolling_avg_window", "value"),
     Input("previous_days", "value"),
     Input("utc_offset", "value")]
)
def update_graph(n_clicks, n_intervals, smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes, rolling_avg_window, previous_days, utc_offset):
    
    try:
        # Input validation
        if not all(isinstance(x, (int, float)) and x >= 0 for x in [past_minutes, forecast_minutes, rolling_avg_window, previous_days] if x is not None):
            print("Invalid input parameters detected")
            return create_empty_figure("Invalid input parameters"), "--°C", "--°C"
        
        # Ensure minimum values
        rolling_avg_window = max(1, rolling_avg_window or 1)
        past_minutes = max(1, past_minutes or 10)
        forecast_minutes = max(1, forecast_minutes or 10)
        
        # Parse temperature data
        df = parse_temperature_data(previous_days=previous_days)
        if df is None or df.empty:
            print("No temperature data available")
            return create_empty_figure("No temperature data available"), "--°C", "--°C"
        
        # Data cleaning and validation
        df = df.dropna()  # Remove any NaN values
        if df.empty:
            return create_empty_figure("No valid temperature data"), "--°C", "--°C"
        
        # Convert timestamps and handle timezone
        df['datetime'] = pd.to_datetime(df['datetime'], unit='s', utc=True) + pd.Timedelta(hours=utc_offset)
        df = df.drop_duplicates(subset=['datetime'], keep='first')
        df = df.sort_values('datetime')
        
        # Validate temperature ranges (reasonable BBQ temperatures)
        df = df[(df['smoker_temp'] >= -10) & (df['smoker_temp'] <= 500) & 
                (df['meat_temp'] >= -10) & (df['meat_temp'] <= 200)]
        
        if df.empty:
            return create_empty_figure("No valid temperature readings in range"), "--°C", "--°C"
        
        # Apply smoothing with bounds checking
        window_size = min(rolling_avg_window, len(df))
        df['smoker_temp'] = df['smoker_temp'].rolling(window=window_size, min_periods=1).mean()
        df['meat_temp'] = df['meat_temp'].rolling(window=window_size, min_periods=1).mean()
        
    except Exception as e:
        print(f"Error in data processing: {e}")
        return create_empty_figure(f"Data processing error: {str(e)}"), "Error", "Error"

    # Get current temperatures for display
    current_smoker = f"{df['smoker_temp'].iloc[-1]:.1f}°C" if not df.empty else "--°C"
    current_meat = f"{df['meat_temp'].iloc[-1]:.1f}°C" if not df.empty else "--°C"

    # Create a new dataframe containing only the last past_minutes
    if len(df) == 0:
        return create_empty_figure("No data for analysis"), "--°C", "--°C"
    
    time_cutoff = df['datetime'].iloc[-1] - pd.Timedelta(minutes=past_minutes)
    df_window = df[df['datetime'] >= time_cutoff].copy()
    
    # Ensure we have enough data for forecasting
    if len(df_window) < 3:
        # Use more data if window is too small
        df_window = df.tail(max(3, min(len(df), 50))).copy()
    
    # Reshape the data to fit the model
    full_time_min = df_window['datetime'].min()
    X = (df_window['datetime'] - full_time_min).dt.total_seconds().values.reshape(-1, 1)
    
    # Predict for Future Times
    last_value = X[-1] if np.isscalar(X[-1]) else X[-1][0]
    future_times = np.arange(int(last_value) + 1, int(last_value) + forecast_minutes * 60 + 1).reshape(-1, 1)
    future_time_strings = convert_to_time(future_times, full_time_min)

    # Use enhanced forecasting with simple trend analysis
    try:
        smoker_forecast, smoker_upper_bound, smoker_lower_bound = enhanced_forecast_temperature(
            X, df_window['smoker_temp'].values, future_times, method='simple'
        )
        meat_forecast, meat_upper_bound, meat_lower_bound = enhanced_forecast_temperature(
            X, df_window['meat_temp'].values, future_times, method='simple'
        )
    except Exception as e:
        print(f"Enhanced forecasting failed, using basic polynomial: {e}")
        smoker_forecast, smoker_upper_bound, smoker_lower_bound = forecast_temperature(X, df_window['smoker_temp'].values, future_times)
        meat_forecast, meat_upper_bound, meat_lower_bound = forecast_temperature(X, df_window['meat_temp'].values, future_times)

    time_now = df_window['datetime'].iloc[-1]
    time_start_window = df_window['datetime'].iloc[0] # time_now - pd.Timedelta(minutes=past_minutes)

    # BBQ-themed color palette with high contrast
    smoker_full_color = '#228B22'  # Forest Green for smoker full history
    smoker_window_color = '#32CD32'  # Lime Green for smoker analysis window
    smoker_pred_color = '#90EE90'  # Light Green for smoker forecast
    meat_full_color = '#8B0000'  # Dark Red for meat full history
    meat_window_color = '#DC143C'  # Crimson for meat analysis window
    meat_pred_color = '#FF6347'  # Tomato for meat forecast
    vline_color = '#4FB0D6'  # Light Blue for vertical lines

    fig = go.Figure()

    # Past temperature values with BBQ-themed colors
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', 
                   line=dict(color=smoker_full_color, width=3), 
                   name='Full history', legendgroup='smoker', legendgrouptitle_text="🔥 Smoker")
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', 
                   line=dict(color=meat_full_color, width=3), 
                   name='Full history', legendgroup='meat', legendgrouptitle_text="🥩 Meat")

    fig.add_scatter(x=df_window["datetime"], y=df_window["smoker_temp"], mode='lines', 
                   line=dict(color=smoker_window_color, width=3), name='Analysis window', legendgroup='smoker')
    fig.add_scatter(x=df_window["datetime"], y=df_window["meat_temp"], mode='lines', 
                   line=dict(color=meat_window_color, width=3), name='Analysis window', legendgroup='meat')

    # Target temperature values
    fig.add_hline(y=smoker_target_temp, line_width=2, line_color=smoker_full_color, line_dash="dash",
                 annotation_text=f"Target: {smoker_target_temp}°C")
    fig.add_hline(y=meat_min_temp, line_width=2, line_color=meat_full_color, line_dash="dash",
                 annotation_text=f"Min: {meat_min_temp}°C")

    # Predicted temperature values with confidence bands
    fig.add_scatter(x=future_time_strings, y=smoker_forecast, mode='lines', 
                   line=dict(color=smoker_pred_color, width=2, dash='dot'), 
                   name='Forecast', legendgroup='smoker')
    fig.add_scatter(x=future_time_strings, y=meat_forecast, mode='lines', 
                   line=dict(color=meat_pred_color, width=2, dash='dot'), 
                   name='Forecast', legendgroup='meat')
    
    # Add confidence bands for forecasts (if data available)
    if len(smoker_forecast) > 0 and len(smoker_upper_bound) > 0:
        fig.add_scatter(x=future_time_strings, y=smoker_upper_bound, mode='lines',
                       line=dict(width=0), showlegend=False, hoverinfo='skip')
        fig.add_scatter(x=future_time_strings, y=smoker_lower_bound, mode='lines',
                       line=dict(width=0), fillcolor=f'rgba({int(smoker_pred_color[1:3], 16)}, {int(smoker_pred_color[3:5], 16)}, {int(smoker_pred_color[5:7], 16)}, 0.2)',
                       fill='tonexty', showlegend=False, hoverinfo='skip', name='Smoker Confidence')
    
    if len(meat_forecast) > 0 and len(meat_upper_bound) > 0:
        fig.add_scatter(x=future_time_strings, y=meat_upper_bound, mode='lines',
                       line=dict(width=0), showlegend=False, hoverinfo='skip')
        fig.add_scatter(x=future_time_strings, y=meat_lower_bound, mode='lines',
                       line=dict(width=0), fillcolor=f'rgba({int(meat_pred_color[1:3], 16)}, {int(meat_pred_color[3:5], 16)}, {int(meat_pred_color[5:7], 16)}, 0.2)',
                       fill='tonexty', showlegend=False, hoverinfo='skip', name='Meat Confidence')
    
    # Calculate axis limits based on actual temperature data and forecasts (excluding confidence intervals)
    y_min = min(df['smoker_temp'].min(), df['meat_temp'].min()) - 5  # Add 5°C padding
    y_max = max(df['smoker_temp'].max(), df['meat_temp'].max()) + 5  # Add 5°C padding
    
    # Include forecast predictions in axis calculation, but not confidence bands
    if len(smoker_forecast) > 0:
        forecast_min = min(smoker_forecast.min(), meat_forecast.min())
        forecast_max = max(smoker_forecast.max(), meat_forecast.max())
        y_min = min(y_min, forecast_min - 2)  # Less padding for forecasts
        y_max = max(y_max, forecast_max + 2)
    
    # Ensure target temperature lines are always visible
    target_temps = [smoker_target_temp, meat_min_temp]
    if any(target_temps):
        valid_targets = [temp for temp in target_temps if temp is not None]
        if valid_targets:
            target_min = min(valid_targets)
            target_max = max(valid_targets)
            y_min = min(y_min, target_min - 10)  # Extra padding below targets
            y_max = max(y_max, target_max + 10)  # Extra padding above targets
    
    # Add a transparent rectangular box for the analysis window
    fig.add_shape(
        type="rect",
        x0=time_start_window,
        y0=y_min,
        x1=time_now,
        y1=y_max,
        fillcolor="rgba(75, 176, 214, 0.1)",  # More transparent light blue
        line=dict(color="rgba(75, 176, 214, 0.3)", width=1),
        layer="below"
    )
    
    # Add label for the prediction window
    fig.add_annotation(
        x=time_start_window + (time_now - time_start_window) / 2,  # Center of the box
        y=y_max - 2,  # Near the top with small margin
        text="Prediction Window",
        showarrow=False,
        font=dict(size=10, color="rgba(75, 176, 214, 0.8)"),
        bgcolor="rgba(255, 255, 255, 0.7)",
        bordercolor="rgba(75, 176, 214, 0.3)",
        borderwidth=1
    )

    # Update layout with modern styling
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='#fafafa',
        xaxis_title='Time',
        yaxis_title='Temperature (°C)',
        xaxis=dict(
            tickangle=270,
            gridcolor='#e0e0e0',
            gridwidth=1,
            showgrid=True
        ),
        yaxis=dict(
            gridcolor='#e0e0e0',
            gridwidth=1,
            showgrid=True,
            range=[y_min, y_max]  # Set explicit y-axis range to prevent confidence intervals from zooming out
        ),
        legend=dict(
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='rgba(0, 0, 0, 0.1)',
            borderwidth=1,
            orientation='v',
            tracegroupgap=15,
            itemsizing='constant',
            itemwidth=30,
            font=dict(size=11, family='Monaco, "Lucida Console", "Courier New", Courier, monospace')
        ),
        font=dict(
            family='Monaco, "Lucida Console", "Courier New", Courier, monospace',
            size=12,
            color='#4a4a4a'
        ),
        margin=dict(l=60, r=40, t=40, b=60)
    )

    return fig, current_smoker, current_meat


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
