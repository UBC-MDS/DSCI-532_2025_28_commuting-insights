import dash
import dash_bootstrap_components as dbc
import dash_vega_components as dvc
from dash import dcc, html, Input, Output
import altair as alt
import os
import sys

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from src.data.preprocessing import load, widget_inputs
from src.callbacks.update_mode import update_mode_callback
from src.callbacks.update_cd import update_cd_callback
from src.callbacks.update_charts import update_all_charts
from src.components.cd_dropdown import create_cd_dropdown

### --- LOAD AND PREPROCESS DATA ---

geojson_data, df = load("data/raw/geojson/lcd_000b21a_e_simplified_0.5percent.geojson", "data/processed/commuting_data/commuting_data_census_divisions_disambiguated.csv")
available_modes, dropdown_options, available_cdnames, dropdown_cd_options, time_bins, time_bin_order, slider_marks = widget_inputs(df)

### --- INITIALIZATION ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], title="Commuting Insights Dashboard")
server = app.server

update_mode_callback(df, available_modes, dropdown_options)
update_cd_callback(df, dropdown_cd_options)

### --- COMPONENTS ---

title = html.H1("Commuting Insights Dashboard")

cd_dropdown_label, cd_dropdown = create_cd_dropdown(dropdown_cd_options)

mode_dropdown_label = dbc.Label("Commuting Mode")
mode_dropdown = dcc.Dropdown(
    id="mode-dropdown",
    options=dropdown_options,
    multi=True,
    placeholder="Select one or more modes...",
    searchable=True
)
time_slider_label = dbc.Label("Arrival Time")
time_slider = dcc.RangeSlider(
    id="time-slider",
    min=0,
    max=len(time_bins),
    value=[0, len(time_bins)],
    marks=slider_marks,
    step=1,
    allowCross=False,
    pushable=1
)

map_title = html.H5("Average Commute Time by Census Division")
choropleth_map = dcc.Graph(id="choropleth-map")

violin_title = html.H5("Commute Times by Mode, Selected Census Division vs. Canada")
violin_plot = dvc.Vega(id="altair-violin-plot")

bar_title = html.H5("Commute Duration Distribution")
bar_chart = dvc.Vega(id="altair-bar-chart")

line_title = html.H5("Average Commute Time by Time of Day")
line_chart = dvc.Vega(id="altair-line-chart")

footer = dbc.Container([
    html.Hr(),
    dbc.Row(dbc.Col(html.P("Commuting Insights is an interactive visualization dashboard for analyzing commuting patterns across Canadian Census Divisions. Users can explore commute times by mode of transport, time of day, and region. Commuting Insights aims to assist the Canadian Federal government in identifying trends for the purpose of informing national transportation funding strategies."), md=6)),
    dbc.Row(dbc.Col(html.P("Created by:"))),
    dbc.Row(dbc.Col(html.Ul([
        html.Li(html.A("Francisco Ramirez", href="https://github.com/fraramfra", target="_blank")),
        html.Li(html.A("Jinxiong (Eugene) You", href="https://github.com/jinxyou", target="_blank")),
        html.Li(html.A("Derek Rodgers", href="https://github.com/derekrodgers", target="_blank")),
        html.Li(html.A("Han Wang", href="https://github.com/hanwang205", target="_blank")),
    ]))),
    dbc.Row(dbc.Col(html.A("View on GitHub", href="https://github.com/UBC-MDS/DSCI-532_2025_28_commuting-insights", target="_blank", style={"font-weight": "bold"}))),
    html.Br(),
    dbc.Row(dbc.Col(html.P("Last updated: Saturday, 29 Feb 2025", style={"font-style": "italic"})))
], fluid=True)

### --- LAYOUT ---

app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.Container([
                    dbc.Row(dbc.Col(title, width=12)),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([cd_dropdown_label, cd_dropdown], md=3),
                        dbc.Col([mode_dropdown_label, mode_dropdown], md=2),
                        dbc.Col([time_slider_label, time_slider], md=7)
                    ]),
                ], fluid=True),
                style={"backgroundColor": "#f8f9fa", "padding": "10px", "borderRadius": "10px"}
            ),
            width=12
        ), className="mt-3"  # Adds top margin above the card
    ),
    html.Br(),
    
    # First Chart Row - With Left & Right Padding
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(map_title)),
            dbc.Row(dbc.Col(choropleth_map))
        ], md=7),
        dbc.Col([
            dbc.Row(dbc.Col(bar_title)),
            dbc.Row(dbc.Col(bar_chart))
        ], md=5)
    ], style={"paddingLeft": "20px", "paddingRight": "20px"}),

    # Second Chart Row - With Left & Right Padding
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(violin_title)),
            dbc.Row(dbc.Col(violin_plot))
        ], md=7),
        dbc.Col([
            dbc.Row(dbc.Col(line_title)),
            dbc.Row(dbc.Col(line_chart))
        ], md=5)
    ], style={"paddingLeft": "20px", "paddingRight": "20px"}),

    footer
], fluid=True)


### --- CALLBACKS ---

update_all_charts(df, time_bins, time_bin_order, geojson_data)

### --- RUN THE APP ---

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
