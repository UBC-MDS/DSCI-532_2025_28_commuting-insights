from dash import Input, Output, callback
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import gaussian_kde
alt.data_transformers.enable("vegafusion")

def update_choropleth_callback(df, time_bin_order, geojson_data):
    @callback(
        [
            Output("choropleth-map", "spec")
        ],
        [
            Input("province-dropdown", "value"),
            # Input("cd-dropdown", "value"),
            Input("mode-dropdown", "value"),
            Input("time-slider", "value")
        ]
    )
    def update_choropleth(selected_province, selected_modes, time_range):
        # Start with all data and filter by Census Division and time range.
        map_df = df.copy()
        if selected_province:
            map_df = map_df[map_df["DGUID"].astype(str).str.startswith(selected_province)]

        # if selected_cd:
        #     map_df = map_df[map_df["DGUID"] == selected_cd]
        if selected_modes and len(selected_modes) > 0:
            map_df = map_df[map_df["Main mode of commuting (21)"].isin(selected_modes)]
        map_df = map_df[map_df["Time arriving at work (16)"].isin(time_bin_order.keys())]
        map_df = map_df[
            map_df["Time arriving at work (16)"]
            .apply(lambda t: time_bin_order[t])
            .between(time_range[0], time_range[1], inclusive="left")
        ]
        map_df = map_df.dropna(subset=["AverageCommuteTime", "TotalDuration"])
        # Group by division (using both DGUID and GEO) and compute the weighted average.
        agg_df = map_df.groupby(["DGUID", "GEO"]).apply(
            lambda g: np.average(g["AverageCommuteTime"], weights=g["TotalDuration"])
            if g["TotalDuration"].sum() > 0 else np.nan
        ).reset_index(name="WeightedAverageCommute")
        
        
        
        # --- Merge aggregated data into the GeoJSON ---
        # Create a dict: key = DGUID, value = WeightedAverageCommute
        agg_dict = agg_df.set_index("DGUID")[["GEO", "WeightedAverageCommute"]].to_dict(orient="index")
        # For each feature, update properties with the aggregated value (if available)
        for feature in geojson_data["features"]:
            dguid = feature["properties"].get("DGUID")

            if dguid in agg_dict:
                feature["properties"]["WeightedAverageCommute"] = agg_dict[dguid]["WeightedAverageCommute"]
                feature["properties"]["GEO"] = agg_dict[dguid]["GEO"]  # Add GEO name
            else:
                feature["properties"]["WeightedAverageCommute"] = None
                feature["properties"]["GEO"] = None  # Default to None if not found
        
        # --- Build Altair Geoshape Chart for the Map ---
        select_region = alt.selection_point(fields=['properties.DGUID'], name='select_region')
        map_chart = alt.Chart(alt.Data(values=geojson_data["features"])).mark_geoshape(
            stroke="black"
        ).encode(
            color=alt.Color("properties.WeightedAverageCommute:Q",
                            scale=alt.Scale(scheme="orangered"),
                            title="Avg Commute (min)"),
            tooltip=[
                alt.Tooltip("properties.GEO:N", title="Division"),
                alt.Tooltip("properties.WeightedAverageCommute:Q", format=".1f", title="Avg Commute (min)"),
            ],
            opacity=alt.condition(select_region, alt.value(0.9), alt.value(0.3))
        ).add_params(
            select_region
    )   .project(
            type="transverseMercator",
            rotate=[90, 0, 0]
        ).properties(width="container", height=600)

        print(select_region)
        return [map_chart.to_dict(format="vega")]  # Return must be a tuple or list