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
csv_path = os.path.abspath(os.path.join(script_dir, "../data/processed/commuting_data/commuting_data_census_divisions_disambiguated.csv"))
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

# Define the selectable commuting modes by looking at unique values in the mode column
available_modes = sorted(df["Main mode of commuting (21)"].unique()) # Sort alphabetically
dropdown_options = [{"label": mode, "value": mode} for mode in available_modes]

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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], title="Commuting Insights Dashboard")
server = app.server

@app.callback(
    Output("mode-dropdown", "options"),
    [Input("cd-dropdown", "value")]
)
def update_mode_options(selected_cd):
    if not selected_cd:
        return dropdown_options
    # Filter for the selected CD and nonzero average commute time
    df_cd = df[(df["GEO"] == selected_cd) & (df["AverageCommuteTime"] > 0)]
    # Get the unique modes that appear in the CD
    modes = df_cd["Main mode of commuting (21)"].unique()
    # Only keep those modes that are in the allowed available_modes list
    valid_modes = [m for m in modes if m in available_modes]
    options = [{"label": m, "value": m} for m in valid_modes]
    return options


### --- COMPONENTS ---

title = html.H1("Commuting Insights Dashboard")
cd_dropdown_label = dbc.Label("Census Division (CD)")
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

@app.callback(
    [
        Output("choropleth-map", "figure"),
        Output("altair-violin-plot", "spec"),
        Output("altair-bar-chart", "spec"),
        Output("altair-line-chart", "spec")
    ],
    [
        Input("cd-dropdown", "value"),
        Input("mode-dropdown", "value"),
        Input("time-slider", "value")
    ]
)

def update_charts(selected_cd, selected_modes, time_range):
    # ---- Choropleth Map ----
    # Start with all data and filter by Census Division and time range.
    map_df = df.copy()

    # Filter by Census Division if selected.
    if selected_cd:
        map_df = map_df[map_df["GEO"] == selected_cd]
    if selected_modes and len(selected_modes) > 0:
        map_df = map_df[map_df["Main mode of commuting (21)"].isin(selected_modes)]

    # Ensure only valid time bins are used and apply the time range filter.
    map_df = map_df[map_df["Time arriving at work (16)"].isin(time_bin_order.keys())]
    map_df = map_df[
        map_df["Time arriving at work (16)"]
        .apply(lambda t: time_bin_order[t])
        .between(time_range[0], time_range[1], inclusive="left")
    ]
    
    # Remove rows with missing numeric values.
    map_df = map_df.dropna(subset=["AverageCommuteTime", "TotalDuration"])

    # Group by division (using both DGUID and GEO) and compute the weighted average.
    agg_df = map_df.groupby(["DGUID", "GEO"]).apply(
        lambda g: np.average(g["AverageCommuteTime"], weights=g["TotalDuration"])
        if g["TotalDuration"].sum() > 0 else np.nan
    ).reset_index(name="WeightedAverageCommute")

    # Create the choropleth map with the aggregated weighted averages.
    fig_map = px.choropleth_map(
        agg_df,
        geojson=geojson_data,
        locations="DGUID",
        featureidkey="properties.DGUID",
        color="WeightedAverageCommute",
        color_continuous_scale="OrRd",
        hover_name="GEO",
        custom_data=["WeightedAverageCommute"],
        map_style="open-street-map",
        center={"lat": 56, "lon": -106},
        zoom=3,
        opacity=0.7,
    )
    fig_map.update_traces(marker_line_width=1.5, marker_line_color="black", showscale=True)
    fig_map.update_traces(
        hovertemplate="<b>%{hovertext}</b><br /><br />Average, currrent filters: %{customdata[0]:.1f} min<extra></extra>"
    )
    fig_map.update_layout(
        coloraxis_colorbar_title="Minutes",
        margin={"r": 0, "t": 0, "l": 0, "b": 70},
        height=488
    )
    
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
    
    weighted_violin = alt.Chart(density_merged).mark_area(orient="horizontal", color="red", opacity=0.25).encode(
        y=alt.Y("AverageCommuteTime:Q", title="Average Commute Time (min)"),
        x=alt.X("density:Q", stack="center", title=None, axis=None)
    ).properties(width=100, height=400)
    
    # National weighted average (Canadian red horizontal rule).
    national_rule = alt.Chart(density_merged).mark_rule(color="#FF3C3C", strokeWidth=5).encode(
        y=alt.Y("nationalMean:Q"),
        tooltip=[alt.Tooltip("nationalMean:Q", format=".1f", title="Average: Canada (min)"),
         alt.Tooltip("", type="nominal", title="")]
    )
    
    # CD weighted average (blue horizontal rule).
    blue_rule = alt.Chart(density_merged).mark_rule(color="blue", strokeWidth=5).encode(
        y=alt.Y("cdMean:Q"),
        tooltip=[alt.Tooltip("cdMean:Q", format=".1f", title="Average: Selected CD (min)"),
         alt.Tooltip("", type="nominal", title="")]
    )
    
    final_violin = alt.layer(weighted_violin, national_rule, blue_rule).facet(
        column=alt.Column("Main mode of commuting (21):N", title="Commuting Mode")
    ).resolve_scale(x="independent") 

    legend_data = pd.DataFrame({
        "Label": ["Average: Canada (min)", "Average: Selected CD (min)"],
        "Color": ["red", "blue"]
    })

    # Circles
    legend_points = (
        alt.Chart(legend_data)
        .mark_circle(size=100)
        .encode(
            # We’ll map each row to a distinct Y-position, effectively stacking them
            y=alt.Y("Label:N", axis=None),
            # Fix the x-position of the circles
            x=alt.value(10),
            color=alt.Color("Color:N", scale=None)  # Use the “Color” column as-is
        )
    )

    # Text
    legend_text = (
        alt.Chart(legend_data)
        .mark_text(align="left", dx=10)  # shift text to the right
        .encode(
            y=alt.Y("Label:N", axis=None),
            x=alt.value(10),  # line up horizontally with circles
            text="Label:N"
        )
    )

    # Combine the points + text into one layer
    custom_legend = (
        alt.layer(legend_points, legend_text)
        .properties(width=120, height=60)
    )

    final_violin_with_legend = (
        alt.HConcatChart(hconcat=[final_violin, custom_legend])
        .configure_view(stroke=None)
        .configure_axis(titleFontSize=14, labelFontSize=12)
        .configure_header(titleFontSize=14, labelFontSize=12)
    )

    # ---- Altair Bar Chart: Stacked Counts for Duration Categories ----
    # Use the same filtered data (base_data) and melt the five duration columns.
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
        "Less15": "< 15 mins",
        "15to29": "15 - 29 mins",
        "30to44": "30 - 44 mins",
        "45to59": "45 - 59 mins",
        "60plus": "> 60 mins"
    }
    bar_data["DurationCategory"] = bar_data["DurationCategory"].map(lambda t: duration_labels.get(t, t))
    
    bar_chart = alt.Chart(bar_data).mark_bar().encode(
        x=alt.X("Count:Q", title="Count of Commute Observations"),
        y=alt.Y("DurationCategory:N",
                title="Commute Duration Category",
                sort=["> 60 mins", "45 - 59 mins", "30 - 44 mins", "15 - 29 mins", "< 15 mins"],
                axis=alt.Axis(labelAlign="left", orient="right")
        ),
        color=alt.Color("Main mode of commuting (21):N", title="Mode"),
        tooltip=[
            alt.Tooltip("Main mode of commuting (21):N", title="Mode"),
            alt.Tooltip("DurationCategory:N", title="Duration Category"),
            alt.Tooltip("Count:Q", format=",.0f")
        ]
    ).properties(
        width="container",
        height=425
    ).configure_axis(
        titleFontSize=14,
        labelFontSize=13
    ).configure_legend(
        titleFontSize=14,
        labelFontSize=13 
    )
    
    # # ---- Altair Line Chart: Weighted Average Commute Time by Time of Day ----
    # # Create a separate dataframe for the line chart that is not filtered by the time slider.
    line_df = df[df["Time arriving at work (16)"].isin(time_bin_order.keys())].copy()
    if selected_cd:
        line_df = line_df[line_df["GEO"] == selected_cd]
    if selected_modes and len(selected_modes) > 0:
        line_df = line_df[line_df["Main mode of commuting (21)"].isin(selected_modes)]
    # Exclude the summary row if present.
    line_df = line_df[line_df["Time arriving at work (16)"] != "Total - Time arriving at work"]
    line_df_agg = line_df.groupby(["Time arriving at work (16)", "Main mode of commuting (21)"]).apply(
        lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
        if g["TotalDuration"].sum() != 0 else None
    ).reset_index(name="weighted_avg")

    line_df_agg = line_df_agg[line_df_agg["weighted_avg"] != 0]
    
    line_chart_spec = alt.Chart(line_df_agg).mark_line(point=True).encode(
        x=alt.X("Time arriving at work (16):N", sort=list(time_bins), title="Time arriving at work"),
        y=alt.Y("weighted_avg:Q", title="Average Commute Time (min)"),
        color=alt.Color("Main mode of commuting (21):N", title="Mode"),
        tooltip=[
            alt.Tooltip("Time arriving at work (16):N", title="Time"),
            alt.Tooltip("weighted_avg:Q", format=".1f", title="Average (mins)")
        ]
    ).properties(
        width="container",
        height=400
    ).configure_axis(
        titleFontSize=14,
        labelFontSize=13
    ).configure_legend(
        titleFontSize=14,
        labelFontSize=13 
    )
    
    return fig_map, final_violin_with_legend.to_dict(format="vega"), bar_chart.to_dict(format="vega"), line_chart_spec.to_dict(format="vega")


### --- RUN THE APP ---

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host="0.0.0.0", port=port, debug=False)
