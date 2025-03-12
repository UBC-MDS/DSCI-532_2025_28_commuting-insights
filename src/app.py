import dash
import dash_bootstrap_components as dbc
import dash_vega_components as dvc
from dash import dcc, html, Input, Output, callback, State
import altair as alt
import os
import sys
import numpy as np
import pandas as pd

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from src.data.preprocessing import load, widget_inputs
from src.callbacks.update_mode import update_mode_callback
from src.callbacks.update_cd import update_cd_callback
from src.callbacks.update_charts import update_all_charts
from src.callbacks.update_choropleth import update_choropleth_callback  
from src.components.cd_dropdown import create_cd_dropdown
from src.components.mode_dropdown import create_mode_dropdown
from src.components.province_dropdown import create_province_dropdown  
from src.components.time_slider import create_time_slider
from src.components.charts import create_choropleth, create_violin, create_bar, create_line
from src.components.title_and_footer import create_title, create_footer

### --- LOAD AND PREPROCESS DATA ---

geojson_data, df = load(
    "data/raw/geojson/lcd_000b21a_e_simplified_0.25percent.geojson", 
    "data/processed/commuting_data/commuting_data_with_province.csv"
)
provinces, dropdown_province_options, available_modes, dropdown_options, available_cdnames, dropdown_cd_options, time_bins, time_bin_order, slider_marks = widget_inputs(df)

### --- INITIALIZATION ---

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], title="Commuting Insights Dashboard")
server = app.server

### --- COMPONENTS ---

title = create_title()
footer = create_footer()

province_dropdown_label, province_dropdown = create_province_dropdown(dropdown_province_options)  # NEW
cd_dropdown_label, cd_dropdown = create_cd_dropdown(dropdown_cd_options)
mode_dropdown_label, mode_dropdown = create_mode_dropdown(dropdown_options)
time_slider_label, time_slider = create_time_slider(time_bins, slider_marks)

map_title, choropleth_map = create_choropleth()
violin_title, violin_plot = create_violin()
bar_title, bar_chart = create_bar()
line_title, line_chart = create_line()

### --- LAYOUT ---

app.layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.Container([
                    dbc.Row(dbc.Col(title, width=12)),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([province_dropdown_label, province_dropdown], md=3),  # NEW: Province Dropdown
                        
                        dbc.Col([cd_dropdown_label, cd_dropdown], md=3),
                        dbc.Col([mode_dropdown_label, mode_dropdown], md=2),
                        dbc.Col([time_slider_label, time_slider], md=4)
                    ]),
                ], fluid=True),
                style={"backgroundColor": "#f8f9fa", "padding": "10px", "borderRadius": "10px"}
            ),
            width=12
        ), className="mt-3"
    ),
    html.Br(),
    dcc.Store(id="preprocessed-data"),
    # First Chart Row - With Left & Right Padding
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(map_title),
                dbc.Col([
                            html.Div([
                                dcc.Checklist(
                                    id="zoom-toggle",
                                    options=[{"label": "Zoom into Southern Quebec", "value": "zoom"}],
                                    value=[],
                                    inline=True
                                )
                            ], id="zoom-toggle-container", style={"display": "none"})  # Initially hidden
                        ])
                ]),
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

update_mode_callback(df, available_modes, dropdown_options)
update_cd_callback(df, dropdown_cd_options)
update_choropleth_callback(df, time_bin_order, geojson_data)
update_all_charts(df, time_bins, time_bin_order, geojson_data)



### --- RUN THE APP ---

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=True)
