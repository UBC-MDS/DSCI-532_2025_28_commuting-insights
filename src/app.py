import dash
import dash_bootstrap_components as dbc
import dash_vega_components as dvc
from dash import dcc, html, Input, Output, callback, State
import altair as alt
import os
import sys
import numpy as np
import pandas as pd
from flask_caching import Cache

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from src.data.preprocessing import load, widget_inputs
from src.callbacks.update_mode import update_mode_callback
from src.callbacks.update_cd import update_cd_callback
from src.callbacks.update_charts import update_all_charts
from src.callbacks.update_choropleth import update_choropleth_callback  
from src.callbacks.reset_filters import reset_filters_callback
from src.components.cd_dropdown import create_cd_dropdown
from src.components.mode_dropdown import create_mode_dropdown
from src.components.province_dropdown import create_province_dropdown  
from src.components.time_slider import create_time_slider
from src.components.charts import create_choropleth, create_violin, create_bar, create_line, create_pie
from src.components.title_and_footer import create_title, create_reset_button, create_footer

### --- LOAD AND PREPROCESS DATA ---

geojson_data, df = load(
    "data/processed/binary/data_geojson.parquet", 
    "data/processed/binary/data_csv.parquet"
)

provinces, dropdown_province_options, available_modes, dropdown_options, available_cdnames, dropdown_cd_options, time_bins, time_bin_order, slider_marks = widget_inputs(df)

### --- INITIALIZATION ---

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], title="Commuting Insights Dashboard", assets_folder = "assets")
server = app.server

cache = Cache(
    app.server,
    config={
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300
    }
)

### --- COMPONENTS ---

title = create_title()
reset_button = create_reset_button()
footer = create_footer()

province_dropdown_label, province_dropdown = create_province_dropdown(dropdown_province_options)
cd_dropdown_label, cd_dropdown = create_cd_dropdown(dropdown_cd_options)
mode_dropdown_label, mode_dropdown = create_mode_dropdown(dropdown_options)
time_slider_label, time_slider = create_time_slider(time_bins, slider_marks)

map_title, choropleth_map = create_choropleth()
violin_title, violin_plot = create_violin()
bar_title, bar_chart = create_bar()
line_title, line_chart = create_line()
pie_title, pie_chart = create_pie()

### --- LAYOUT ---


app.layout = dbc.Container([
    # First Row: Controls
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.Container([
                    dbc.Row(dbc.Col(title, width=12)),
                    dbc.Row(dbc.Col(reset_button, width=12), className="mb-1"),
                    dbc.Row([
                        dbc.Col([province_dropdown_label, province_dropdown], xxl=2),  # Responsive
                        dbc.Col([cd_dropdown_label, cd_dropdown], xxl=3),
                        dbc.Col([mode_dropdown_label, mode_dropdown], xxl=2),
                        dbc.Col([time_slider_label, time_slider], xxl=5)
                    ]),
                ], fluid=True),
                style={
                    "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                    "border-radius": "10px",
                    "margin": "10px",
                    "padding": "10px",
                    "backgroundColor": "#f8f9fa"
                }
            ),
            width=12
        ), className="mt-3"
    ),
    dcc.Store(id="preprocessed-data"),
    dcc.Store(id="preprocessed-chart-data"),
    dcc.Store(id="top-3-cds-data"),  
    dcc.Store(id="bot-3-cds-data"),

    # First Chart Row
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(map_title, width=12),
                        dbc.Col([
                            html.Div([
                                dcc.Checklist(
                                    id="zoom-toggle",
                                    options=[{"label": " Zoom into Southern Quebec", "value": "zoom"}],
                                    value=[],
                                    inline=True
                                )
                            ], id="zoom-toggle-container", style={"display": "none"})  # Initially hidden
                        ], width=12)
                    ]),
                    dbc.Row(dbc.Col(choropleth_map, className="h-100"))
                ]
            )], style={
                "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                "border-radius": "10px",
                "margin": "10px",
                "height": "100%"
            })
        , xl=12, xxl=5),  # Responsive

        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(dbc.Col(violin_title, width=12)),
                    dbc.Row(dbc.Col(violin_plot, width="auto", className="d-flex justify-content-center align-items-center h-100"),  # Centered
                    className="d-flex justify-content-center align-items-center h-100")
                ]
            )], style={
                "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                "border-radius": "10px",
                "margin": "10px",
                "height": "100%"
            })
        , xl=12, xxl=7),  # Responsive
        
    ], className="gx-3 gy-3"),  # Adds spacing between rows/columns


    html.Br(),

    # Second Chart Row
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(id="bot-3-cds-content", className="g-2")  
                ])
            ], style={
                "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                "border-radius": "10px",
                "margin": "10px",
                "height": "100%"
            }), lg=6, xl=6, xxl=2),

        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(id="top-3-cds-content", className="g-2")  # Will be updated with the top 3 CDs
                ])
            ], style={
                "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                "border-radius": "10px",
                "margin": "10px",
                "height": "100%"
            }), lg=6, xl=6, xxl=2),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(dbc.Col(line_title, width=12)),
                    dbc.Row(dbc.Col(line_chart, width=12, className="h-100"))
                ]
            )], style={
                "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                "border-radius": "10px",
                "margin": "10px",
                "height": "100%"
            }),
            html.Br()
        ], xl=12, xxl=8),

    ], className="gx-3 gy-3"),  # Adds spacing between rows/columns

    html.Br(),

    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(dbc.Col(bar_title, width=12)),
                    dbc.Row(dbc.Col(bar_chart, width=12, className="h-100"))
                ]
            )], style={
                "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                "border-radius": "10px",
                "margin": "10px",
                "height": "100%"
            })
        , xl=12, xxl=7),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    dbc.Row(dbc.Col(pie_title, width=12)),
                    dbc.Row(dbc.Col(pie_chart, width=12, className="h-100"))
                ]
            )], style={
                "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                "border-radius": "10px",
                "margin": "10px",
                "height": "100%"
            })
        , xl=12, xxl=5),
    ], className="gx-3 gy-3"),

    html.Br(),
    footer
], fluid=True)





### --- CALLBACKS ---

update_mode_callback(df, available_modes, dropdown_options, cache)
update_cd_callback(df, dropdown_cd_options, cache)
update_choropleth_callback(df, time_bin_order, geojson_data, cache)
update_all_charts(df, time_bins, time_bin_order, cache)
reset_filters_callback(time_bins, cache)

### --- RUN THE APP ---

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
