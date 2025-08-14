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
        # Sidebar for desktop
        html.Div([
            # Header with logo and title (moved to sidebar)
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
                    dcc.Input(id='smoker_target_temp', type='number', min=0, max=200, step=1, value=107, className='input-field')
                ], className='input-group'),
                html.Div([
                    html.Label('Meat Minimum (°C)', className='input-label'),
                    dcc.Input(id='meat_min_temp', type='number', min=0, max=200, step=1, value=74, className='input-field')
                ], className='input-group')
            ], className='card'),

            # Analysis Settings
            html.Div([
                html.H3('Forecast Temps', className='section-header section-header-small'),
                html.Div([
                    html.Label('History Window (min)', className='input-label'),
                    dcc.Input(id='past_minutes', type='number', min=0, max=120, step=10, value=30, className='input-field')
                ], className='input-group'),
                html.Div([
                    html.Label('Forecast (min)', className='input-label'),
                    dcc.Input(id='forecast_minutes', type='number', min=0, max=120, step=10, value=30, className='input-field')
                ], className='input-group'),
                html.Div([
                    html.Label('Smoothing Window (samples)', className='input-label'),
                    dcc.Input(id='rolling_avg_window', type='number', min=1, max=1000, step=1, value=9, className='input-field')
                ], className='input-group')
            ], className='card')

        ], className='sidebar'),

        # Main content area
        html.Div([
            # Mobile header (only visible on mobile)
            html.Div([
                html.Img(
                    src='/assets/logo.png',
                    className='logo'
                ),
                html.H1(
                    'PiBQ',
                    className='title mobile-title'
                ),
                html.P(
                    'BBQ monitoring dashboard',
                    className='subtitle mobile-subtitle'
                )
            ], className='mobile-header'),
            
            dcc.Graph(id='graph-content', className='graph-container')
        ], className='main-content')

    ], className='main-container'),

    # Mobile controls (hidden on desktop)
    html.Div([
        # Current Temperature Display for Mobile
        html.Div([
            html.H3('Current Temperatures', className='section-header mobile-section-header'),
            html.Div([
                html.Div([
                    html.Span('🔥 Smoker: ', className='temp-label-mobile'),
                    html.Span(id='current-smoker-temp-mobile', children='--°C', className='temp-value-mobile smoker-temp')
                ], className='temp-display-mobile'),
                html.Div([
                    html.Span('🥩 Meat: ', className='temp-label-mobile'),
                    html.Span(id='current-meat-temp-mobile', children='--°C', className='temp-value-mobile meat-temp')
                ], className='temp-display-mobile')
            ])
        ], className='card mobile-card'),

        html.Div([
            html.Button('Update Dashboard', id='update-button-mobile', className='button button-mobile')
        ]),

        # Mobile Temperature Settings
        html.Div([
            html.H4('Temperature Settings', className='section-header mobile-section-header'),
            html.Div([
                html.Div([
                    html.Label('Smoker Target (°C)', className='input-label'),
                    dcc.Input(id='smoker_target_temp_mobile', type='number', min=0, max=200, step=1, value=107, className='input-field input-field-mobile')
                ], className='input-group-mobile'),
                html.Div([
                    html.Label('Meat Minimum (°C)', className='input-label'),
                    dcc.Input(id='meat_min_temp_mobile', type='number', min=0, max=200, step=1, value=74, className='input-field input-field-mobile')
                ])
            ])
        ], className='card mobile-card'),

        # Mobile Analysis Settings
        html.Div([
            html.H4('Analysis Settings', className='section-header mobile-section-header'),
            html.Div([
                html.Div([
                    html.Label('History Window (min)', className='input-label'),
                    dcc.Input(id='past_minutes_mobile', type='number', min=0, max=120, step=10, value=30, className='input-field input-field-mobile')
                ], className='input-group-mobile'),
                html.Div([
                    html.Label('Forecast (min)', className='input-label'),
                    dcc.Input(id='forecast_minutes_mobile', type='number', min=0, max=120, step=10, value=30, className='input-field input-field-mobile')
                ], className='input-group-mobile'),
                html.Div([
                    html.Label('Smoothing Window', className='input-label'),
                    dcc.Input(id='rolling_avg_window_mobile', type='number', min=1, max=1000, step=1, value=9, className='input-field input-field-mobile')
                ])
            ])
        ], className='card mobile-card')

    ], className='mobile-controls')

])

@callback(
    [Output('graph-content', 'figure'),
     Output('current-smoker-temp', 'children'),
     Output('current-meat-temp', 'children'),
     Output('current-smoker-temp-mobile', 'children'),
     Output('current-meat-temp-mobile', 'children')],
    [Input('update-button', 'n_clicks'),
     Input('update-button-mobile', 'n_clicks'),
     Input("smoker_target_temp", "value"),
     Input("meat_min_temp", "value"),
     Input("past_minutes", "value"),
     Input("forecast_minutes", "value"),
     Input("rolling_avg_window", "value"),
     Input("smoker_target_temp_mobile", "value"),
     Input("meat_min_temp_mobile", "value"),
     Input("past_minutes_mobile", "value"),
     Input("forecast_minutes_mobile", "value"),
     Input("rolling_avg_window_mobile", "value")]
)
def update_graph(n_clicks_desktop, n_clicks_mobile, smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes, rolling_avg_window,
                smoker_target_temp_mobile, meat_min_temp_mobile, past_minutes_mobile, forecast_minutes_mobile, rolling_avg_window_mobile):
    
    # Use mobile values as fallback, desktop as primary
    smoker_target = smoker_target_temp if smoker_target_temp is not None else smoker_target_temp_mobile
    meat_min = meat_min_temp if meat_min_temp is not None else meat_min_temp_mobile
    past_min = past_minutes if past_minutes is not None else past_minutes_mobile
    forecast_min = forecast_minutes if forecast_minutes is not None else forecast_minutes_mobile
    rolling_window = rolling_avg_window if rolling_avg_window is not None else rolling_avg_window_mobile
    # Parse temperature data
    df = parse_temperature_data()
    df['datetime'] = pd.to_datetime(pd.to_datetime(df['datetime'], format='mixed').dt.strftime('%H:%M:%S'), format='%H:%M:%S')

    df = df.drop_duplicates(subset=['datetime'], keep='first') # Remove duplicate rows based on similar datetime, keeping first occurrence
    df['smoker_temp'] = df['smoker_temp'].rolling(window=rolling_window).mean()
    df['meat_temp'] = df['meat_temp'].rolling(window=rolling_window).mean()
    df.dropna(how='any', inplace=True)

    # Get current temperatures for display
    current_smoker = f"{df['smoker_temp'].iloc[-1]:.1f}°C" if not df.empty else "--°C"
    current_meat = f"{df['meat_temp'].iloc[-1]:.1f}°C" if not df.empty else "--°C"

    past_steps = past_min * 60
    forecast_steps = forecast_min * 60

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
    full_time_min = df['datetime'].min()  # define this based on your data
    full_time = (df['datetime'] - full_time_min).dt.total_seconds().values.reshape(-1, 1)
    X = full_time[-past_steps:]

    # Predict for Future Times
    last_value = X[-1] if np.isscalar(X[-1]) else X[-1][0]
    int_list = range(int(last_value) + 1, int(last_value) + forecast_steps)
    future_times = np.array([float(i) for i in int_list]).reshape(-1, 1)
    future_time_strings = convert_to_time(future_times, full_time_min)

    smoker_forecast, smoker_upper_bound, smoker_lower_bound = forecast_temperature(df['smoker_temp'], X, past_steps, future_times)
    meat_forecast, meat_upper_bound, meat_lower_bound = forecast_temperature(df['meat_temp'], X, past_steps, future_times)

    # BBQ-themed color palette
    smoker_color = '#d2691e'  # Chocolate/orange for smoker
    smoker_light = '#daa520'  # Goldenrod for smoker highlights
    smoker_forecast_color = '#ff8c00'  # Dark orange for smoker forecast
    
    meat_color = '#8b4513'  # Saddle brown for meat
    meat_light = '#a0522d'  # Sienna for meat highlights  
    meat_forecast_color = '#cd853f'  # Peru for meat forecast

    fig = go.Figure()

    # Past temperature values with BBQ-themed colors
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', 
                   line=dict(color=smoker_color, width=2), 
                   name='Full history', legendgroup='smoker', legendgrouptitle_text="🔥 Smoker")
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', 
                   line=dict(color=meat_color, width=2), 
                   name='Full history', legendgroup='meat', legendgrouptitle_text="🥩 Meat")

    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["smoker_temp"].tail(past_steps), mode='lines', 
                   line=dict(color=smoker_light, width=3), name='Analysis window', legendgroup='smoker')
    fig.add_scatter(x=df["datetime"].tail(past_steps), y=df["meat_temp"].tail(past_steps), mode='lines', 
                   line=dict(color=meat_light, width=3), name='Analysis window', legendgroup='meat')

    # Target temperature values
    fig.add_hline(y=smoker_target, line_width=2, line_color=smoker_color, line_dash="dash",
                 annotation_text=f"Target: {smoker_target}°C")
    fig.add_hline(y=meat_min, line_width=2, line_color=meat_color, line_dash="dash",
                 annotation_text=f"Min: {meat_min}°C")

    # Predicted temperature values
    fig.add_scatter(x=future_time_strings, y=smoker_forecast, mode='lines', 
                   line=dict(color=smoker_forecast_color, width=2, dash='dot'), 
                   name='Forecast', legendgroup='smoker')
    fig.add_scatter(x=future_time_strings, y=meat_forecast, mode='lines', 
                   line=dict(color=meat_forecast_color, width=2, dash='dot'), 
                   name='Forecast', legendgroup='meat')
    #fig.add_scatter(x=future_time_strings, y=meat_confidence_intervals[:, 0], mode='lines', line=dict(width=0), showlegend=False)
    #fig.add_scatter(x=future_time_strings, y=meat_confidence_intervals[:, 1], mode='lines', fill='tonexty', fillcolor='rgba(255, 105, 180, 0.3)', line=dict(width=0), showlegend=False)


#    # plt.scatter(full_time, df['smoker_temp'], color='yellow', label='All recorded temperatures')
#    # plt.scatter(X, y, color='blue', label='Observed data')
#    # plt.plot(X, y_pred, color='green', label='Polynomial fit')
#    # plt.scatter(future_times, future_predictions, color='red', label='Predicted future values')
    # plt.fill_between(future_times.flatten(), lower_bound, upper_bound, color='gray', alpha=0.5, label='Confidence Interval')


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

    return fig, current_smoker, current_meat, current_smoker, current_meat


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
