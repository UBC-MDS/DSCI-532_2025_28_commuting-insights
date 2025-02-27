import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import geopandas as gpd
import pandas as pd
import plotly.express as px
import json
import os

###
### --- LOAD DATA ---
###

# Load the GeoJSON data
script_dir = os.path.dirname(os.path.abspath(__file__))
geojson_path = os.path.abspath(os.path.join(script_dir, "../data/raw/geojson/lcd_000b21a_e_simplified_0.5percent.geojson"))
gdf = gpd.read_file(geojson_path)

# Subset to only the columns we need
gdf = gdf[["DGUID", "CDUID", "CDNAME", "geometry"]]

# Fix the projection: EPSG:3347 → EPSG:4326 (lat/lon)
gdf.crs = "EPSG:3347"
gdf_latlon = gdf.to_crs(epsg=4326)

# Convert to GeoJSON dictionary
geojson_data = json.loads(gdf_latlon.to_json())

# Assign "id" to each feature based on CDUID
for feature in geojson_data["features"]:
    feature["id"] = feature["properties"]["CDUID"]

# Load and filter the commuting data
csv_path = os.path.abspath(os.path.join(script_dir, "../data/raw/commuting_data/commuting_data_census_divisions.csv"))
df = pd.read_csv(csv_path)

# Extract unique commuting modes for dropdown options
available_modes = df["Main mode of commuting (21)"].unique()
dropdown_options = [{"label": mode, "value": mode} for mode in available_modes]

# Initialize the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CERULEAN]
)
server = app.server

###
### --- COMPONENTS ---
###
title = html.H1("Commuting Insights")

map_title = html.H3("Average Commute Time by Census Division")

control_widgets = [
    html.Label("Select commuting modes:"),
    dcc.Dropdown(
        id="mode-dropdown",
        options=dropdown_options,
        multi=True,
        placeholder="Select commuting modes...",
        searchable=True
    )
]

choropleth_map = dcc.Graph(id="choropleth-map")
violin_plot = dcc.Graph(id="violin-plot")
second_visualization = dcc.Graph(id="second-visualization")

###
### --- LAYOUT ---
###
app.layout = dbc.Container([
    dbc.Row(dbc.Col(title)),
    
    dbc.Row([
        # Control Widgets Column
        dbc.Col(dbc.Row(control_widgets), md=2),

        # First Visualization Column (Choropleth + Violin)
        dbc.Col([
            dbc.Row(dbc.Col(map_title)),
            dbc.Row(dbc.Col(choropleth_map)),
            dbc.Row(dbc.Col(violin_plot))
        ], md=7),

        # Second Visualization Column
        dbc.Col(second_visualization, md=3)
    ])
], fluid=True)

###
### --- CALLBACK ---
###
@app.callback(
    Output("choropleth-map", "figure"),
    Input("mode-dropdown", "value")
)
def update_map(selected_modes):
    # If no mode is selected, show all modes
    if not selected_modes or len(selected_modes) == 0:
        filtered_df = df
    else:
        filtered_df = df[df["Main mode of commuting (21)"].isin(selected_modes)]

    # Ensure only relevant data is shown
    filtered_df = filtered_df[
        (filtered_df["Time arriving at work (16)"] == "Total - Time arriving at work")
    ]

    # Rename column for easier use
    filtered_df = filtered_df.rename(
        columns={"Commuting duration (7):Average commuting duration (in minutes)[7]": "AverageCommuteTime"}
    )

    # Create updated choropleth map
    fig = px.choropleth_map(
        filtered_df,
        geojson=geojson_data,
        locations="DGUID",
        featureidkey="properties.DGUID",
        color="AverageCommuteTime",
        color_continuous_scale="OrRd",
        hover_name="GEO",
        hover_data={"DGUID": False, "AverageCommuteTime": True},
        map_style="open-street-map",
        center={"lat": 56, "lon": -106},
        zoom=3,
        opacity=0.7,
    )

    # Adjust map appearance
    fig.update_traces(marker_line_width=1.5, marker_line_color="black", showscale=True)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig

###
### --- RUN THE APP ---
###
if __name__ == "__main__":
    app.run(debug=True)