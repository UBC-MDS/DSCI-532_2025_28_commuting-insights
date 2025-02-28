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
# Keep only selected columns:
df = df[[
    "GEO", 
    "DGUID", 
    "Time arriving at work (16)", 
    "Main mode of commuting (21)", 
    "Commuting duration (7):Total - Commuting duration[1]", 
    "Commuting duration (7):Average commuting duration (in minutes)[7]"
]]
# Rename columns for convenience.
df = df.rename(
    columns={
        "Commuting duration (7):Average commuting duration (in minutes)[7]": "AverageCommuteTime",
        "Commuting duration (7):Total - Commuting duration[1]": "TotalDuration"
    }
)

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
# For the last bin, we set its representative label as "5am" because its exclusive end is 5:00am.
time_bin_labels = {
    "Between 5 a.m. and 5:29 a.m.": "5",
    "Between 5:30 a.m. and 5:59 a.m.": "5:30",
    "Between 6 a.m. and 6:29 a.m.": "6",
    "Between 6:30 a.m. and 6:59 a.m.": "6:30",
    "Between 7 a.m. and 7:29 a.m.": "7",
    "Between 7:30 a.m. and 7:59 a.m.": "7:30",
    "Between 8 a.m. and 8:29 a.m.": "8",
    "Between 8:30 a.m. and 8:59 a.m.": "8:30",
    "Between 9 a.m. and 9:59 a.m.": "9",
    "Between 10 a.m. and 10:59 a.m.": "10",
    "Between 11 a.m. and 11:59 a.m.": "11",
    "Between 12 p.m. and 3:59 p.m.": "12pm",
    "Between 4 p.m. and 7:59 p.m.": "4",
    "Between 8 p.m. and 11:59 p.m.": "8",
    "Between 12 a.m. and 4:59 a.m.": "5am"
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

violin_title = html.H5("Commute Time by Mode")
violin_label_shape = dbc.Label("• For each mode, blue violin shapes show commute time distributions for all of Canada, all times of day.")
violin_label_line = dbc.Label("• Horizontal red lines show the mode's average commute time for the currently selected Census Division and Arrival Time.")


scatter_title = html.H5("Average Commute Time by Number of Observations")
scatter_label = dbc.Label("Each point is a unique combination of Census Division and Mode.")

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
    dbc.Label("Arrival Time"),
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
scatter_plot = dvc.Vega(id="altair-scatter-plot")

### --- LAYOUT ---

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(title)),
            html.Br()
        ]),
    ]),
    dbc.Row([
        dbc.Col(control_widgets, md=2),
        dbc.Col([
            dbc.Row(dbc.Col(map_title)),
            dbc.Row(dbc.Col(choropleth_map)),
            html.Br(),
            html.Br(),
            dbc.Row(dbc.Col(violin_title)),
            dbc.Row(dbc.Col(violin_label_shape)),
            dbc.Row(dbc.Col(violin_label_line)),
            dbc.Row(dbc.Col(violin_plot))
        ], md=6),
        dbc.Col([
            dbc.Row(dbc.Col(scatter_title)),
            dbc.Row(dbc.Col(scatter_label)),
            dbc.Row(dbc.Col(scatter_plot)),
        ], md=4),
    ])
], fluid=True)

### --- CALLBACKS ---

@app.callback(
    [
        Output("choropleth-map", "figure"),
        Output("altair-violin-plot", "spec"),
        Output("altair-scatter-plot", "spec")
    ],
    [
        Input("cd-dropdown", "value"),
        Input("mode-dropdown", "value"),
        Input("time-slider", "value")
    ]
)

def update_charts(selected_cd, selected_modes, time_range):
    # ---- Choropleth Map ----
    filtered_df = df.copy()
    if selected_cd:
        filtered_df = filtered_df[filtered_df["GEO"] == selected_cd]
    if selected_modes and len(selected_modes) > 0:
        filtered_df = filtered_df[filtered_df["Main mode of commuting (21)"].isin(selected_modes)]
    filtered_df = filtered_df[filtered_df["Time arriving at work (16)"].isin(time_bin_order.keys())]
    # Left-inclusive, right-exclusive filtering.
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
        hover_data={"DGUID": False, "AverageCommuteTime": ":.0f"},
        custom_data=["AverageCommuteTime"],
        map_style="open-street-map",
        center={"lat": 56, "lon": -106},
        zoom=3,
        opacity=0.7,
    )
    fig_map.update_traces(marker_line_width=1.5, marker_line_color="black", showscale=True)
    fig_map.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>Average Commute: %{customdata[0]} min<extra></extra>"
    )
    fig_map.update_layout(coloraxis_colorbar_title="Minutes")
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 30})

    # ---- Altair Violin Plot with Weighted Red Rule ----
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
        # Compute weighted average per mode.
        agg_df = cd_data.groupby("Main mode of commuting (21)").apply(
            lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
            if g["TotalDuration"].sum() != 0 else None
        ).reset_index(name="meanCommute")
        # Merge the aggregated values back into the filtered data.
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
        #color=alt.Color(shorthand="Main mode of commuting (21):N")
    ).properties(
        width=150,
        height=400
    )
    
    # Red horizontal rule with tooltip: drawn at the weighted mean (if computed).
    rule = base.mark_rule(color="red", strokeWidth=2).encode(
        y=alt.Y("meanCommute:Q"),
        tooltip=alt.Tooltip("meanCommute:Q", format=".1f", title="Weighted Mean Commute Time")
    )
    
    final_chart = alt.layer(violin, rule).facet(
        column=alt.Column("Main mode of commuting (21):N", title="Mode of Commute")
    ).resolve_scale(x="independent")

    # ---- Scatter Plot: one point per (Census Division × Major Mode) ----

    # 1) Start with the same base_data_filtered used for the violin
    scatter_data = base_data_filtered.copy()

    # 2) If a census division is selected, filter for just that one
    if selected_cd:
        scatter_data = scatter_data[scatter_data["GEO"] == selected_cd]

    # 3) Group by (GEO, Main mode) and compute:
    #    - total number of records (sum of TotalDuration)
    #    - weighted average of AverageCommuteTime
    scatter_agg = (
        scatter_data.groupby(["GEO", "Main mode of commuting (21)"], as_index=False)
        .apply(lambda g: pd.Series({
            "TotalDuration": g["TotalDuration"].sum(),
            "WeightedAvgCommute": (
                (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
                if g["TotalDuration"].sum() != 0 else None
            )
        }))
    )

    # 4) Build the Altair chart with color and tooltips
    scatter = (
        alt.Chart(scatter_agg)
        .mark_point()
        .encode(
            x=alt.X("TotalDuration:Q", title="Total Commute Observations"),
            y=alt.Y("WeightedAvgCommute:Q", title="Average Commute Time (min)"),
            color=alt.Color("Main mode of commuting (21):N", title="Commuting Mode"),
            tooltip=[
                alt.Tooltip("GEO:N", title="Census Division"),
                alt.Tooltip("Main mode of commuting (21):N", title="Commuting Mode"),
                alt.Tooltip("TotalDuration:Q", format=",.0f", title="Total Commute Observations"),
                alt.Tooltip("WeightedAvgCommute:Q", format=",.1f", title="Average Commute Time (min)"),
            ]
        )
        .properties(width=370, height=370)
    )
    
    return fig_map, final_chart.to_dict(format="vega"), scatter.to_dict(format="vega")

### --- RUN THE APP ---

if __name__ == "__main__":
    #app.server.run(port=8000, host="127.0.0.1", debug=False)
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
