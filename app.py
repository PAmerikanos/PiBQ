from dash import Dash, html, dcc, callback, Output, Input
import plotly.graph_objs as go
import numpy as np
import pandas as pd
from helpers import convert_to_time, forecast_temperature, parse_temperature_data


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
                    dcc.Input(id='smoker_target_temp', type='number', min=0, step=1, value=120, className='input-field')
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
     Input("rolling_avg_window", "value")]
)
def update_graph(n_clicks, n_intervals, smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes, rolling_avg_window):
    
    # Use the input values directly
    smoker_target = smoker_target_temp
    meat_min = meat_min_temp
    past_min = past_minutes
    forecast_min = forecast_minutes
    rolling_window = rolling_avg_window
    # Parse temperature data
    df = parse_temperature_data()
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s', utc=True).dt.tz_convert('Europe/Athens')

    df = df.drop_duplicates(subset=['datetime'], keep='first') # Remove duplicate rows based on similar datetime, keeping first occurrence
    df['smoker_temp'] = df['smoker_temp'].rolling(window=rolling_window).mean()
    df['meat_temp'] = df['meat_temp'].rolling(window=rolling_window).mean()
    df.dropna(how='any', inplace=True)

    # Get current temperatures for display
    current_smoker = f"{df['smoker_temp'].iloc[-1]:.1f}°C" if not df.empty else "--°C"
    current_meat = f"{df['meat_temp'].iloc[-1]:.1f}°C" if not df.empty else "--°C"

    past_steps = past_min * 60
    forecast_steps = forecast_min * 60


    # Reshape the data to fit the model
    full_time_min = df['datetime'].min()
    full_time = (df['datetime'] - full_time_min).dt.total_seconds().values.reshape(-1, 1)
    X = full_time[-past_steps:]

    # Predict for Future Times
    last_value = X[-1] if np.isscalar(X[-1]) else X[-1][0]
    int_list = range(int(last_value) + 1, int(last_value) + forecast_steps)
    future_times = np.array([float(i) for i in int_list]).reshape(-1, 1)
    future_time_strings = convert_to_time(future_times, full_time_min)

    smoker_forecast, smoker_upper_bound, smoker_lower_bound = forecast_temperature(df['smoker_temp'], X, past_steps, future_times)
    meat_forecast, meat_upper_bound, meat_lower_bound = forecast_temperature(df['meat_temp'], X, past_steps, future_times)

    time_now = df['datetime'].max()
    time_start_window = time_now - pd.Timedelta(minutes=past_min)
    print(time_now)
    print(time_start_window)

    # BBQ-themed color palette with high contrast
    smoker_full_color = '#228B22'  # Forest Green for smoker full history
    smoker_window_color = '#32CD32'  # Lime Green for smoker analysis window
    smoker_pred_color = '#90EE90'  # Light Green for smoker forecast
    
    meat_full_color = '#8B0000'  # Dark Red for meat full history
    meat_window_color = '#DC143C'  # Crimson for meat analysis window
    meat_pred_color = '#FF6347'  # Tomato for meat forecast

    fig = go.Figure()

    # Past temperature values with BBQ-themed colors
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', 
                   line=dict(color=smoker_full_color, width=3), 
                   name='Full history', legendgroup='smoker', legendgrouptitle_text="🔥 Smoker")
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', 
                   line=dict(color=meat_full_color, width=3), 
                   name='Full history', legendgroup='meat', legendgrouptitle_text="🥩 Meat")

    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["smoker_temp"].tail(past_steps), mode='lines', 
                   line=dict(color=smoker_window_color, width=3), name='Analysis window', legendgroup='smoker')
    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["meat_temp"].tail(past_steps), mode='lines', 
                   line=dict(color=meat_window_color, width=3), name='Analysis window', legendgroup='meat')

    # Target temperature values
    fig.add_hline(y=smoker_target, line_width=2, line_color=smoker_full_color, line_dash="dash",
                 annotation_text=f"Target: {smoker_target}°C")
    fig.add_hline(y=meat_min, line_width=2, line_color=meat_full_color, line_dash="dash",
                 annotation_text=f"Min: {meat_min}°C")

    # Predicted temperature values
    fig.add_scatter(x=future_time_strings, y=smoker_forecast, mode='lines', 
                   line=dict(color=smoker_pred_color, width=2, dash='dot'), 
                   name='Forecast', legendgroup='smoker')
    fig.add_scatter(x=future_time_strings, y=meat_forecast, mode='lines', 
                   line=dict(color=meat_pred_color, width=2, dash='dot'), 
                   name='Forecast', legendgroup='meat')
    
    # Add vertical lines for time markers using add_vline with converted timestamps
    fig.add_vline(x=time_now.timestamp() * 1000, line_width=2, line_color="#4FB0D6", line_dash="solid",
                 annotation_text="Now", annotation_position="top")
    fig.add_vline(x=time_start_window.timestamp() * 1000, line_width=2, line_color="#4FB0D6", line_dash="dash",
                 annotation_text="Window", annotation_position="top")

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
            showgrid=True
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
