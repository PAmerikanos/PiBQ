from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def forecast_temperature(temp, fsteps):
    # Fit an ARIMA model and predict the next forecast_steps with confidence intervals
    model = ARIMA(temp, order=(5,1,0))
    model_fit = model.fit()
    forecast_result = model_fit.get_forecast(steps=fsteps)
    forecast = forecast_result.predicted_mean
    confidence_intervals = forecast_result.conf_int()

    return forecast, confidence_intervals


app = Dash()

app.layout = [
    #html.H1(children='Title of Dash App', style={'textAlign':'center'}),

    dcc.Graph(id='graph-content'),

    html.Div(
        [
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
                style={'display': 'flex', 'alignItems': 'center'}
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
                style={'display': 'flex', 'alignItems': 'center'}
            ),
        ],
        style={
            'display': 'flex',
            'flexDirection': 'column',
            'alignItems': 'center',
            'justifyContent': 'center',
        }
    ),

    # Interval component for auto-refreshing every 10 sec (300000 milliseconds)
    dcc.Interval(
        id='interval-component',
        interval=10*1000,  # 300 seconds = 5 minutes
        n_intervals=0  # Number of times the interval has passed
    )
]

@callback(
    Output('graph-content', 'figure'),
    Input('interval-component', 'n_intervals'),
    Input("smoker_target_temp", "value"),
    Input("meat_min_temp", "value"),
    Input("past_minutes", "value"),
    Input("forecast_minutes", "value")
)
def update_graph(n_intervals, smoker_target_temp, meat_min_temp, past_minutes, forecast_minutes):
    # Load the CSV file
    column_names = ['datetime', 'smoker_temp', 'meat_temp']
    df = pd.read_csv('../logs/temperature.log', header=None, names=column_names)
    df['datetime'] = pd.to_datetime(df['datetime'], format='mixed').dt.strftime('%H:%M:%S')

    past_steps = 60 * past_minutes
    forecast_steps = 60 * forecast_minutes

    # Display onle last 10 minutes
    date_time = df['datetime'].tail(past_steps).to_list()
    smoker_temp = df['smoker_temp'].tail(past_steps).to_list()
    meat_temp = df['meat_temp'].tail(past_steps).to_list()

    # Forecast temps
    smoker_forecast, smoker_confidence_intervals = forecast_temperature(smoker_temp, forecast_steps)
    meat_forecast, meat_confidence_intervals = forecast_temperature(meat_temp, forecast_steps)

    # Generate future time indices for the forecast
    future_times = pd.date_range(start=date_time[-1], periods=forecast_steps + 1, freq='s')[1:].time


    fig = go.Figure()

    # Past temperature values
    fig.add_scatter(x=df["datetime"], y=df["smoker_temp"], mode='lines', line=dict(color='blue'), name='Smoker Temperature')
    fig.add_scatter(x=df["datetime"], y=df["meat_temp"], mode='lines', line=dict(color='red'), name='Meat Temperature')

    # Target temperature values
    fig.add_hline(y=smoker_target_temp, line_width=1, line_color="blue")
    fig.add_hline(y=meat_min_temp, line_width=1, line_color="red")

    # Predicted temperature values
    fig.add_scatter(x=future_times, y=smoker_forecast, mode='lines', line=dict(color='cyan'), name='Predicted Smoker Temperature')
    #ax.fill_between(future_times, smoker_confidence_intervals[:, 0], smoker_confidence_intervals[:, 1], color='pink', alpha=0.3)
    
    fig.add_scatter(x=future_times, y=meat_forecast, mode='lines', line=dict(color='pink'), name='Predicted Meat Temperature')
    #ax.fill_between(future_times, meat_confidence_intervals[:, 0], meat_confidence_intervals[:, 1], color='cyan', alpha=0.3)

    # Update layout labels
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Temperature',
        legend_title='Legend'
    )
    return fig


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True, threaded=True)
