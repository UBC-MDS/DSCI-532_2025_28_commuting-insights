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
import numpy as np
from scipy.stats import gaussian_kde

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
# Keep only selected columns (including the count columns):
df = df[[ 
    "GEO", 
    "DGUID", 
    "Time arriving at work (16)", 
    "Main mode of commuting (21)", 
    "Commuting duration (7):Total - Commuting duration[1]",
    "Commuting duration (7):Average commuting duration (in minutes)[7]",
    "Commuting duration (7):Less than 15 minutes[2]",
    "Commuting duration (7):15 to 29 minutes[3]",
    "Commuting duration (7):30 to 44 minutes[4]",
    "Commuting duration (7):45 to 59 minutes[5]",
    "Commuting duration (7):60 minutes and over[6]"
]]
# Rename columns for convenience.
df = df.rename(
    columns={
        "Commuting duration (7):Average commuting duration (in minutes)[7]": "AverageCommuteTime",
        "Commuting duration (7):Total - Commuting duration[1]": "TotalDuration",
        "Commuting duration (7):Less than 15 minutes[2]": "Less15",
        "Commuting duration (7):15 to 29 minutes[3]": "15to29",
        "Commuting duration (7):30 to 44 minutes[4]": "30to44",
        "Commuting duration (7):45 to 59 minutes[5]": "45to59",
        "Commuting duration (7):60 minutes and over[6]": "60plus"
    }
)
# Convert numeric columns.
df["AverageCommuteTime"] = pd.to_numeric(df["AverageCommuteTime"], errors="coerce")
df["TotalDuration"] = pd.to_numeric(df["TotalDuration"], errors="coerce")
df["Less15"] = pd.to_numeric(df["Less15"], errors="coerce")
df["15to29"] = pd.to_numeric(df["15to29"], errors="coerce")
df["30to44"] = pd.to_numeric(df["30to44"], errors="coerce")
df["45to59"] = pd.to_numeric(df["45to59"], errors="coerce")
df["60plus"] = pd.to_numeric(df["60plus"], errors="coerce")

# Define the selectable commuting modes.
selectable_modes = [
    "Total - Main mode of commuting",
    "Car, truck or van",
    "Public transit",
    "Walked",
    "Bicycle",
    "Motorcycle, scooter or moped",
    "Other method"
]
available_modes = selectable_modes
dropdown_options = [{"label": mode, "value": mode} for mode in selectable_modes]

# Extract unique Census Divisions.
available_cdnames = df["GEO"].unique()
dropdown_cd_options = [{"label": cd, "value": cd} for cd in available_cdnames]

# Define the time bins present in the dataset.
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

# Build slider marks.
# The slider will display point labels (timestamps) for each interval's start,
# plus one extra mark for the right endpoint.
point_labels = {
    "Between 5 a.m. and 5:29 a.m.": "5am",
    "Between 5:30 a.m. and 5:59 a.m.": "5:30am",
    "Between 6 a.m. and 6:29 a.m.": "6am",
    "Between 6:30 a.m. and 6:59 a.m.": "6:30am",
    "Between 7 a.m. and 7:29 a.m.": "7am",
    "Between 7:30 a.m. and 7:59 a.m.": "7:30am",
    "Between 8 a.m. and 8:29 a.m.": "8am",
    "Between 8:30 a.m. and 8:59 a.m.": "8:30am",
    "Between 9 a.m. and 9:59 a.m.": "9am",
    "Between 10 a.m. and 10:59 a.m.": "10am",
    "Between 11 a.m. and 11:59 a.m.": "11am",
    "Between 12 p.m. and 3:59 p.m.": "12pm",
    "Between 4 p.m. and 7:59 p.m.": "4pm",
    "Between 8 p.m. and 11:59 p.m.": "8pm",
    "Between 12 a.m. and 4:59 a.m.": "12am"
}
slider_marks = {i: point_labels[time_bins[i]] for i in range(len(time_bins))}
slider_marks[len(time_bins)] = "5am"  # Extra mark for the right endpoint

### --- INITIALIZATION ---
alt.data_transformers.enable("vegafusion")
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])
server = app.server

### --- COMPONENTS ---
title = html.H1("Commuting Insights")
cd_dropdown_label = dbc.Label("Census Division")
cd_dropdown = dcc.Dropdown(
    id="cd-dropdown",
    options=dropdown_cd_options,
    multi=False,
    placeholder="Select a Division...",
    searchable=True
)
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
scatter_title = html.H5("Average Commute Time by Number of Observations")
scatter_label = dbc.Label("Each point is a unique combination of Census Division and Mode.")
scatter_plot = dvc.Vega(id="altair-scatter-plot")
violin_title = html.H5("Commute Times by Mode")
violin_label_shape = dbc.Label("• Light gray violins show the national (all-Canada) trend for the selected time range.")
violin_label_line = dbc.Label("• Canadian red horizontal lines show the national weighted average; blue horizontal lines show the weighted average for the selected Census Division.")
violin_plot = dvc.Vega(id="altair-violin-plot")
bar_title = html.H5("Commute Duration Distribution")
bar_chart = dvc.Vega(id="altair-bar-chart")

### --- LAYOUT ---
app.layout = dbc.Container([
    dbc.Row(dbc.Col(title, width=12)),
    html.Br(),
    dbc.Row([
        dbc.Col([cd_dropdown_label, cd_dropdown], md=4),
        dbc.Col([mode_dropdown_label, mode_dropdown], md=4),
        dbc.Col([time_slider_label, time_slider], md=4)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(map_title)),
            dbc.Row(dbc.Col(choropleth_map))
        ], md=8),
        dbc.Col([
            dbc.Row(dbc.Col(scatter_title)),
            dbc.Row(dbc.Col(scatter_label)),
            dbc.Row(dbc.Col(scatter_plot))
        ], md=4)
    ]),
    html.Br(),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(violin_title)),
            dbc.Row(dbc.Col(violin_label_shape)),
            dbc.Row(dbc.Col(violin_label_line)),
            dbc.Row(dbc.Col(violin_plot))
        ], width=12)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Row(dbc.Col(bar_title)),
            dbc.Row(dbc.Col(bar_chart))
        ], width=12)
    ])
], fluid=True)

### --- CALLBACKS ---
@app.callback(
    [
        Output("choropleth-map", "figure"),
        Output("altair-violin-plot", "spec"),
        Output("altair-scatter-plot", "spec"),
        Output("altair-bar-chart", "spec")
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
    filtered_df = filtered_df[
        filtered_df["Time arriving at work (16)"].apply(lambda t: time_bin_order[t])
                 .between(time_range[0], time_range[1], inclusive="left")
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
    fig_map.update_layout(coloraxis_colorbar_title="Minutes", margin={"r":0,"t":0,"l":0,"b":30})
    
    # ---- Altair Violin Plot with Weighted Horizontal Rules ----
    base_data = df[df["Time arriving at work (16)"].isin(time_bin_order.keys())].copy()
    base_data["time_order"] = base_data["Time arriving at work (16)"].apply(lambda t: time_bin_order[t])
    base_data = base_data[base_data["time_order"].between(time_range[0], time_range[1], inclusive="left")]
    if not selected_modes or len(selected_modes) == 0:
        selected_modes = list(available_modes)
    base_data = base_data[base_data["Main mode of commuting (21)"].isin(selected_modes)]
    
    if selected_cd:
        base_data["is_subset"] = base_data["GEO"] == selected_cd
    else:
        base_data["is_subset"] = False
    
    # Compute national weighted averages per mode.
    agg_national = (
        base_data.groupby("Main mode of commuting (21)")
        .apply(lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
               if g["TotalDuration"].sum() != 0 else None)
        .reset_index(name="nationalMean")
    )
    
    # Compute CD weighted averages if selected.
    if selected_cd:
        cd_data = base_data[base_data["GEO"] == selected_cd].copy()
        agg_cd = (
            cd_data.groupby("Main mode of commuting (21)")
            .apply(lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
                   if g["TotalDuration"].sum() != 0 else None)
            .reset_index(name="cdMean")
        )
    else:
        agg_cd = pd.DataFrame(columns=["Main mode of commuting (21)", "cdMean"])
    
    merged_data = pd.merge(base_data, agg_national, on="Main mode of commuting (21)", how="left")
    merged_data = pd.merge(merged_data, agg_cd, on="Main mode of commuting (21)", how="left")
    
    base_chart = alt.Chart(merged_data)
    
    # Compute weighted density for the violin plot using gaussian_kde.
    density_list = []
    x_grid = np.linspace(0, 60, 200)
    for mode, group in base_data.groupby("Main mode of commuting (21)"):
        group = group.dropna(subset=["AverageCommuteTime", "TotalDuration"])
        if len(group) == 0 or group["TotalDuration"].sum() == 0:
            continue
        x_vals = group["AverageCommuteTime"].values
        weights = group["TotalDuration"].values
        kde = gaussian_kde(x_vals, weights=weights)
        density = kde(x_grid)
        temp_df = pd.DataFrame({
            "Main mode of commuting (21)": mode,
            "AverageCommuteTime": x_grid,
            "density": density
        })
        density_list.append(temp_df)
    if density_list:
        density_df = pd.concat(density_list, ignore_index=True)
    else:
        density_df = pd.DataFrame(columns=["Main mode of commuting (21)", "AverageCommuteTime", "density"])
    
    # Merge density_df with aggregated weighted averages.
    density_merged = pd.merge(density_df, agg_national, on="Main mode of commuting (21)", how="left")
    density_merged = pd.merge(density_merged, agg_cd, on="Main mode of commuting (21)", how="left")
    
    weighted_violin = alt.Chart(density_merged).mark_area(orient="horizontal", color="lightgray", opacity=0.3).encode(
        y=alt.Y("AverageCommuteTime:Q", title="Average Commute Time (min)"),
        x=alt.X("density:Q", stack="center", title=None, axis=None)
    ).properties(width=100, height=400)
    
    # National weighted average (Canadian red horizontal rule).
    national_rule = alt.Chart(density_merged).mark_rule(color="#FF3C3C", strokeWidth=5).encode(
        y=alt.Y("nationalMean:Q"),
        tooltip=alt.Tooltip("nationalMean:Q", format=".1f", title="National Weighted Average")
    )
    
    # CD weighted average (blue horizontal rule).
    blue_rule = alt.Chart(density_merged).mark_rule(color="blue", strokeWidth=5).encode(
        y=alt.Y("cdMean:Q"),
        tooltip=alt.Tooltip("cdMean:Q", format=".1f", title="CD Weighted Average")
    )
    
    final_violin = alt.layer(weighted_violin, national_rule, blue_rule).facet(
        column=alt.Column("Main mode of commuting (21):N", title="Commuting Mode")
    ).resolve_scale(x="independent").configure_view(clip=True)
    
    # ---- Altair Scatter Plot (unchanged) ----
    scatter_data = base_data.copy()
    if selected_cd:
        scatter_data = scatter_data[scatter_data["GEO"] == selected_cd]
    
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
    
    scatter = (
        alt.Chart(scatter_agg)
        .mark_point()
        .encode(
            x=alt.X("TotalDuration:Q", title="Total Observations"),
            y=alt.Y("WeightedAvgCommute:Q", title="Weighted Average Commute (min)"),
            color=alt.Color("Main mode of commuting (21):N", title="Mode"),
            tooltip=[
                alt.Tooltip("GEO:N", title="Census Division"),
                alt.Tooltip("Main mode of commuting (21):N", title="Mode"),
                alt.Tooltip("TotalDuration:Q", format=",.0f", title="Observations"),
                alt.Tooltip("WeightedAvgCommute:Q", format=",.1f", title="Weighted Avg Commute")
            ]
        )
        .properties(width=370, height=370)
        .interactive()
    )
    
    # ---- Altair Bar Chart: Stacked Counts for Duration Categories ----
    # Here, we want the bar chart to reflect the counts in the filter scenario.
    # We use the same filtered data (base_data) and melt the five duration columns.
    bar_data = base_data.copy()
    if selected_cd:
        bar_data = bar_data[bar_data["GEO"] == selected_cd]
    bar_data = bar_data[["Main mode of commuting (21)", "Less15", "15to29", "30to44", "45to59", "60plus"]].copy()
    bar_data = bar_data.melt(id_vars=["Main mode of commuting (21)"],
                             value_vars=["Less15", "15to29", "30to44", "45to59", "60plus"],
                             var_name="DurationCategory", value_name="Count")
    # Group by DurationCategory and Mode, summing counts.
    bar_data = bar_data.groupby(["DurationCategory", "Main mode of commuting (21)"], as_index=False)["Count"].sum()
    
    # Map raw duration column names to descriptive labels.
    duration_labels = {
        "Less15": "Less than 15 minutes",
        "15to29": "15 to 29 minutes",
        "30to44": "30 to 44 minutes",
        "45to59": "45 to 59 minutes",
        "60plus": "60 minutes and over"
    }
    bar_data["DurationCategory"] = bar_data["DurationCategory"].map(lambda t: duration_labels.get(t, t))
    
    bar_chart = alt.Chart(bar_data).mark_bar().encode(
        x=alt.X("DurationCategory:N", title="Commute Duration Category"),
        y=alt.Y("Count:Q", title="Total Count"),
        color=alt.Color("Main mode of commuting (21):N", title="Mode"),
        tooltip=[alt.Tooltip("DurationCategory:N"), alt.Tooltip("Count:Q", format=",.0f")]
    ).properties(
        width=400,
        height=300,
        title="Commute Duration Distribution"
    )
    
    return fig_map, final_violin.to_dict(format="vega"), scatter.to_dict(format="vega"), bar_chart.to_dict(format="vega")
    
### --- RUN THE APP ---
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
