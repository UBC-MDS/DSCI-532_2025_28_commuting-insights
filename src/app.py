import dash
import dash_bootstrap_components as dbc
import dash_vega_components as dvc
from dash import dcc, html, Input, Output
import altair as alt
import pandas as pd
import geopandas as gpd
import plotly.express as px
import json
import os

### --- LOAD DATA ---

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

# Define the selectable commuting modes (only these will be available)
selectable_modes = [
    "Total - Main mode of commuting",
    "Car, truck or van",
    "Public transit",
    "Walked",
    "Bicycle",
    "Motorcycle, scooter or moped",
    "Other method"
]
available_modes = selectable_modes  # Fixed list
dropdown_options = [{"label": mode, "value": mode} for mode in selectable_modes]

# Extract unique Census Divisions for the new dropdown
available_cdnames = df["GEO"].unique()
dropdown_cd_options = [{"label": cd, "value": cd} for cd in available_cdnames]

# Rename commute time column for easier reference
df = df.rename(
    columns={
        "Commuting duration (7):Average commuting duration (in minutes)[7]": "AverageCommuteTime",
        "Commuting duration (7):Total - Commuting duration[1]": "TotalDuration"
        }
)

# Define the time bins present in the dataset (excluding the "Total - Time arriving at work" summary)
time_bins = [
    "Between 5 a.m. and 5:29 a.m.",
    "Between 5:30 a.m. and 5:59 a.m.",
    "Between 6 a.m. and 6:29 a.m.",
    "Between 6:30 a.m. and 6:59 a.m.",
    "Between 7 a.m. and 7:29 a.m.",
    "Between 7:30 a.m. and 7:59 a.m.",
    "Between 8 a.m. and 8:29 a.m.",
    "Between 8:30 a.m. and 8:59 a.m.",
    "Between 9 a.m. and 9:59 a.m.",
    "Between 10 a.m. and 10:59 a.m.",
    "Between 11 a.m. and 11:59 a.m.",
    "Between 12 p.m. and 3:59 p.m.",
    "Between 4 p.m. and 7:59 p.m.",
    "Between 8 p.m. and 11:59 p.m.",
    "Between 12 a.m. and 4:59 a.m."
]

# Create a mapping from time bin to its order (0-indexed).
time_bin_order = {t: i for i, t in enumerate(time_bins)}

# Create a mapping from time bin to a representative label.
# Note: We update the last bin's label to "5:00am" since its exclusive end is 5:00am.
time_bin_labels = {
    "Between 5 a.m. and 5:29 a.m.": "5:00am",
    "Between 5:30 a.m. and 5:59 a.m.": "5:30am",
    "Between 6 a.m. and 6:29 a.m.": "6:00am",
    "Between 6:30 a.m. and 6:59 a.m.": "6:30am",
    "Between 7 a.m. and 7:29 a.m.": "7:00am",
    "Between 7:30 a.m. and 7:59 a.m.": "7:30am",
    "Between 8 a.m. and 8:29 a.m.": "8:00am",
    "Between 8:30 a.m. and 8:59 a.m.": "8:30am",
    "Between 9 a.m. and 9:59 a.m.": "9:00am",
    "Between 10 a.m. and 10:59 a.m.": "10:00am",
    "Between 11 a.m. and 11:59 a.m.": "11:00am",
    "Between 12 p.m. and 3:59 p.m.": "12:00pm",
    "Between 4 p.m. and 7:59 p.m.": "4:00pm",
    "Between 8 p.m. and 11:59 p.m.": "8:00pm",
    "Between 12 a.m. and 4:59 a.m.": "5:00am"
}

# Create slider marks using the representative labels.
time_marks = {i: time_bin_labels[time_bins[i]] for i in range(len(time_bins))}

### --- INITIALIZATION ---

# Enable VegaFusion to handle large datasets in Altair
alt.data_transformers.enable("vegafusion")

# Create the Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CERULEAN]
)
server = app.server

### --- COMPONENTS ---

title = html.H1("Commuting Insights")
map_title = html.H5("Average Commute Time by Census Division")
violin_title = html.H5("Average Commute Time by Mode")

control_widgets = [
    dbc.Label("Census Division"),
    dcc.Dropdown(
        id="cd-dropdown",
        options=dropdown_cd_options,
        multi=False,
        placeholder="Select a Division...",
        searchable=True
    ),
    html.Br(),
    dbc.Label("Commuting Mode"),
    dcc.Dropdown(
        id="mode-dropdown",
        options=dropdown_options,
        multi=True,
        placeholder="Select one or more modes...",
        searchable=True
    ),
    html.Br(),
    dbc.Label("Time arriving at work"),
    dcc.RangeSlider(
        id="time-slider",
        min=0,
        max=len(time_bins) - 1,
        value=[0, len(time_bins) - 1],
        marks=time_marks,
        step=1
    )
]

choropleth_map = dcc.Graph(id="choropleth-map")
violin_plot = dvc.Vega(id="altair-violin-plot")

### --- LAYOUT ---

app.layout = dbc.Container([
    dbc.Row(dbc.Col(title)),
    dbc.Row([
        dbc.Col(control_widgets, md=2),
        dbc.Col([
            dbc.Row(dbc.Col(map_title)),
            dbc.Row(dbc.Col(choropleth_map)),
            html.Br(),
            html.Br(),
            dbc.Row(dbc.Col(violin_title)),
            dbc.Row(dbc.Col(violin_plot))
        ], md=10),
    ])
], fluid=True)

### --- CALLBACKS ---

@app.callback(
    [Output("choropleth-map", "figure"), Output("altair-violin-plot", "spec")],
    [Input("cd-dropdown", "value"),
     Input("mode-dropdown", "value"),
     Input("time-slider", "value")]
)
def update_charts(selected_cd, selected_modes, time_range):
    # ---- Choropleth Map ----
    filtered_df = df.copy()
    if selected_cd:
        filtered_df = filtered_df[filtered_df["GEO"] == selected_cd]
    if selected_modes and len(selected_modes) > 0:
        filtered_df = filtered_df[filtered_df["Main mode of commuting (21)"].isin(selected_modes)]
    filtered_df = filtered_df[filtered_df["Time arriving at work (16)"].isin(time_bin_order.keys())]
    # Use left-inclusive, right-exclusive filtering.
    filtered_df = filtered_df[
        filtered_df["Time arriving at work (16)"].apply(lambda t: time_bin_order[t]).between(time_range[0], time_range[1], inclusive="left")
    ]
    
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
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 30})
    
    # ---- Altair Violin Plot with Weighted Red Rule ----
    # Filter base data by our defined time bins.
    base_data = df[df["Time arriving at work (16)"].isin(time_bin_order.keys())].copy()
    base_data["time_order"] = base_data["Time arriving at work (16)"].apply(lambda t: time_bin_order[t])
    base_data = base_data[base_data["time_order"].between(time_range[0], time_range[1], inclusive="left")]
    
    if not selected_modes or len(selected_modes) == 0:
        selected_modes = list(available_modes)
    base_data_filtered = base_data[base_data["Main mode of commuting (21)"].isin(selected_modes)]
    
    # If a Census Division is selected, compute weighted averages per mode using pandas.
    if selected_cd:
        # Ensure the weight column is numeric.
        base_data_filtered["TotalDuration"] = pd.to_numeric(base_data_filtered["TotalDuration"], errors="coerce")
        cd_data = base_data_filtered[base_data_filtered["GEO"] == selected_cd].copy()
        # Compute weighted average per mode: sum(AverageCommuteTime * TotalDuration) / sum(TotalDuration)
        agg_df = cd_data.groupby("Main mode of commuting (21)").apply(
            lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
            if g["TotalDuration"].sum() != 0 else None
        ).reset_index(name="meanCommute")
        # Merge the aggregated weighted means back into the filtered data.
        merged_data = pd.merge(base_data_filtered, agg_df, on="Main mode of commuting (21)", how="left")
    else:
        merged_data = base_data_filtered.copy()
    
    # Create a base Altair chart using the merged data.
    base = alt.Chart(merged_data)
    
    # Violin plot: compute density per commuting mode.
    violin = base.transform_density(
        density="AverageCommuteTime",
        groupby=["Main mode of commuting (21)"],
        as_=["AverageCommuteTime", "density"]
    ).mark_area(orient="horizontal").encode(
        y=alt.Y("AverageCommuteTime:Q", title="Average Commute Time (min)"),
        x=alt.X("density:Q", stack="center", title=None, axis=None),
        # color=alt.Color("Main mode of commuting (21):N")
    ).properties(
        width=150,
        height=400
    )
    
    # Red horizontal rule with tooltip: drawn at the weighted mean (if computed).
    rule = base.mark_rule(color="red", strokeWidth=2).encode(
        y=alt.Y("meanCommute:Q"),
        tooltip=alt.Tooltip("meanCommute:Q", format=".1f", title="Weighted Mean Commute Time")
    )
    
    # Layer the violin and red rule; facet by commuting mode.
    final_chart = alt.layer(violin, rule).facet(
        column=alt.Column("Main mode of commuting (21):N", title="Mode of Commute")
    ).resolve_scale(x="independent")
    
    return fig_map, final_chart.to_dict(format="vega")




### --- RUN THE APP ---

if __name__ == "__main__":
    app.server.run(port=8000, host="127.0.0.1", debug=True)
