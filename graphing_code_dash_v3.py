import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import scipy.stats as stats
from statsmodels.stats.anova import AnovaRM

# Load the data
file_path = 'F:/beng/K/KSU/KSU_TAPS/Sensor/DataLogger_code/CR_1000/analog_IRT/comparison_data_analog_sensors.xlsx'  # Replace with your actual file path
df = pd.read_excel(file_path)

# Convert TIMESTAMP to datetime format
df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], format='%m/%d/%Y %H:%M')

# Set TIMESTAMP as the index
df.set_index('TIMESTAMP', inplace=True)

# Replace any NaN or invalid temperature values (-9999)
df.replace(-9999, pd.NA, inplace=True)

# Resample the data every 5 minutes, taking the mean of temperature columns
df_resampled = df[['TempC_target_1331', 'TempC_target_1370', 'TempC_target_1376']].resample('5T').mean()

# Initialize the dashboard app
app = Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("IRT Temperature Dashboard", style={'font-family': 'Open Sans'}),
    
    # Dropdown for selecting which IRTs to plot
    dcc.Tabs([
        dcc.Tab(label="IRT Temperature Plot", children=[
            html.Label("Select IRTs to plot:", style={'font-family': 'Open Sans'}),
            dcc.Dropdown(
                id='sensor-dropdown',
                options=[
                    {'label': 'IRT 1331', 'value': 'TempC_target_1331'},
                    {'label': 'IRT 1370', 'value': 'TempC_target_1370'},
                    {'label': 'IRT 1376', 'value': 'TempC_target_1376'}
                ],
                value=['TempC_target_1331', 'TempC_target_1370', 'TempC_target_1376'],  # Default selection
                multi=True,
                style={'font-family': 'Open Sans'}
            ),
            dcc.Graph(id='temp-plot')
        ]),

        dcc.Tab(label="IRT Temperature with Error Bars", children=[
            html.Label("Select IRTs for error bars plot:", style={'font-family': 'Open Sans'}),
            dcc.Dropdown(
                id='errorbars-dropdown',
                options=[
                    {'label': 'IRT 1331', 'value': 'TempC_target_1331'},
                    {'label': 'IRT 1370', 'value': 'TempC_target_1370'},
                    {'label': 'IRT 1376', 'value': 'TempC_target_1376'}
                ],
                value=['TempC_target_1331', 'TempC_target_1370'],  # Default selection
                multi=True,
                style={'font-family': 'Open Sans'}
            ),
            dcc.Graph(id='errorbars-plot'),
            html.Div(id='anova-results', style={'whiteSpace': 'pre-line', 'font-family': 'Open Sans'})
        ])
    ])
])

# Callback for the temperature plot (first tab)
@app.callback(
    Output('temp-plot', 'figure'),
    [Input('sensor-dropdown', 'value')]
)
def update_temp_plot(selected_sensors):
    fig = go.Figure()
    
    # Plot the selected sensors
    for sensor in selected_sensors:
        fig.add_trace(go.Scatter(
            x=df_resampled.index,
            y=df_resampled[sensor],
            mode='lines+markers',
            name=sensor
        ))

    # Update layout
    fig.update_layout(
        title="IRT Temperatures (Every 5 Minutes)",
        xaxis_title="Timestamp",
        yaxis_title="Temperature (°C)",
        template="plotly_dark",
        hovermode="x",
        font=dict(family="Open Sans", size=14)
    )
    return fig

# Callback for the error bars plot and statistical analysis (second tab)
@app.callback(
    [Output('errorbars-plot', 'figure'),
     Output('anova-results', 'children')],
    [Input('errorbars-dropdown', 'value')]
)
def update_errorbars_plot(selected_sensors):
    fig = go.Figure()

    # Plot the selected sensors with error bars
    for sensor in selected_sensors:
        # Calculate mean and standard deviation for error bars
        df_std = df_resampled[sensor].std()

        # Ensure the error bars are an array of values, not a single scalar
        error_bars = df_resampled[sensor].rolling(window=5).std()  # Rolling std for error bars

        fig.add_trace(go.Scatter(
            x=df_resampled.index,
            y=df_resampled[sensor],
            mode='lines+markers',
            name=sensor,
            error_y=dict(
                type='data',
                array=error_bars,  # Use rolling std as the error bars
                visible=True,
                color='gray',
                thickness=1.5,
                width=3
            )
        ))

    # Perform statistical tests only if two or more sensors are selected
    anova_results_text = ""
    if len(selected_sensors) == 2:
        t_stat, p_value = stats.ttest_rel(df_resampled[selected_sensors[0]], df_resampled[selected_sensors[1]])
        anova_results_text = f"Paired t-test between {selected_sensors[0]} and {selected_sensors[1]}:\n" \
                             f"t-stat = {t_stat:.4f}, p-value = {p_value:.4f}"

    elif len(selected_sensors) > 2:
        df_melted = df_resampled[selected_sensors].reset_index().melt(id_vars=['TIMESTAMP'], 
                                                                      var_name='Sensor', 
                                                                      value_name='Temperature')
        anova_model = AnovaRM(df_melted, 'Temperature', 'TIMESTAMP', within=['Sensor'])
        anova_results = anova_model.fit()
        anova_results_text = str(anova_results)

    # Update layout
    fig.update_layout(
        title="IRT Temperatures with Error Bars (Every 5 Minutes)",
        xaxis_title="Timestamp",
        yaxis_title="Temperature (°C)",
        template="plotly_dark",
        hovermode="x",
        font=dict(family="Open Sans", size=14)
    )

    return fig, anova_results_text

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
