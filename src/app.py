import dash
import dash_bootstrap_components as dbc
import dash_vega_components as dvc
import altair as alt
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json
from dash import dcc, html, Input, Output
import os

# Enable VegaFusion to handle large datasets in Altair
alt.data_transformers.enable("vegafusion")

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

# Extract unique Census Divisions for the new dropdown
available_cdnames = df["GEO"].unique()
dropdown_cd_options = [{"label": cd, "value": cd} for cd in available_cdnames]

# Rename commute time column for easier reference
df = df.rename(
    columns={"Commuting duration (7):Average commuting duration (in minutes)[7]": "AverageCommuteTime"}
)

# Create the Dash app
app = dash.Dash(__name__)

server = app.server

app.layout = dbc.Container([
    html.H3("Average Commute Time by Census Division"),

    # Dropdown for selecting Census Division
    dcc.Dropdown(
        id="cd-dropdown",
        options=dropdown_cd_options,
        multi=False,  # Single selection
        placeholder="Select a Census Division...",
        searchable=True
    ),

    # Dropdown for selecting commute modes
    dcc.Dropdown(
        id="mode-dropdown",
        options=dropdown_options,
        multi=True,
        placeholder="Select commuting modes...",
        searchable=True
    ),

    # Choropleth Map
    dcc.Graph(id="choropleth-map"),

    # Altair Vega Chart
    dvc.Vega(id="altair-violin-plot")
])

@app.callback(
    [Output("choropleth-map", "figure"), Output("altair-violin-plot", "spec")],
    [Input("cd-dropdown", "value"), Input("mode-dropdown", "value")]
)
def update_charts(selected_cd, selected_modes):
    # ---- Choropleth Map (unchanged) ----
    filtered_df = df.copy()
    if selected_cd:
        filtered_df = filtered_df[filtered_df["GEO"] == selected_cd]
    if selected_modes and len(selected_modes) > 0:
        filtered_df = filtered_df[filtered_df["Main mode of commuting (21)"].isin(selected_modes)]
    filtered_df = filtered_df[filtered_df["Time arriving at work (16)"] == "Total - Time arriving at work"]

    fig_map = px.choropleth_map(
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
    fig_map.update_traces(marker_line_width=1.5, marker_line_color="black", showscale=True)
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # ---- Altair Violin Plot with Dot per Mode ----
    # Base data: always use all rows where Time arriving at work is "Total - Time arriving at work"
    base_data = df[df["Time arriving at work (16)"] == "Total - Time arriving at work"]

    # If no commuting mode is selected, default to all available modes.
    if not selected_modes or len(selected_modes) == 0:
        selected_modes = list(available_modes)
    base_data_filtered = base_data[base_data["Main mode of commuting (21)"].isin(selected_modes)]

    # Create a base chart with the filtered data.
    base = alt.Chart(base_data_filtered)

    # Violin plot: compute density per travel mode.
    violin = base.transform_density(
        density="AverageCommuteTime",
        groupby=["Main mode of commuting (21)"],
        as_=["AverageCommuteTime", "density"]
    ).mark_area(orient="horizontal").encode(
        y=alt.Y("AverageCommuteTime:Q", title="Average Commute Time (min)"),
        x=alt.X("density:Q", stack="center", title=None, axis=None),
    ).properties(
        width=150,
        height=400
    )

    # Dot layer: if a Census Division is selected, filter for it.
    if selected_cd:
        dot = base.transform_filter(alt.datum.GEO == selected_cd).mark_point(
            filled=True, size=100, color="red"
        ).encode(
            y=alt.Y("AverageCommuteTime:Q"),
            x=alt.value(75)  # Position at the center of the density (x=0)
        )
    else:
        dot = alt.Chart(base_data_filtered).mark_point().encode()  # empty chart

    # Layer the violin and dot
    layered = alt.layer(violin, dot)

    # Facet the layered chart by commuting mode.
    final_chart = layered.facet(
        column=alt.Column("Main mode of commuting (21):N", title="Mode of Commute")
    ).resolve_scale(x="independent")

    return fig_map, final_chart.to_dict(format="vega")


# Run the app
if __name__ == "__main__":
    app.run(debug=True)
