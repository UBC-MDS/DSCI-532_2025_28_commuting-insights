from dash import Input, Output, callback, State
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import gaussian_kde
import dash
alt.data_transformers.enable("vegafusion")

def update_choropleth_callback(df, time_bin_order, geojson_data):
    
    @callback(
        Output("preprocessed-data", "data"),  # Store precomputed values
        Input("province-dropdown", "value"),
        Input("mode-dropdown", "value"),
        Input("time-slider", "value"),
    )
    def preprocess_data(selected_province, selected_modes, time_range):
        """Preprocess data once and store in a Dash Store component."""
        map_df = df.copy()

        # Apply filters efficiently
        if selected_province:
            map_df = map_df[map_df["Province"]==selected_province]
        if selected_modes:
            map_df = map_df[map_df["Main mode of commuting (21)"].isin(selected_modes)]
        
        # Convert time ranges to numerical format
        map_df = map_df[
            map_df["Time arriving at work (16)"].apply(lambda t: time_bin_order[t])
            .between(time_range[0], time_range[1], inclusive="left")
        ]

        # Drop NaNs to avoid errors
        map_df = map_df.dropna(subset=["AverageCommuteTime", "TotalDuration"])

        # Compute weighted average commute time
        agg_df = map_df.groupby(["DGUID", "GEO", "Province"]).apply(
            lambda g: np.average(g["AverageCommuteTime"], weights=g["TotalDuration"])
            if g["TotalDuration"].sum() > 0 else np.nan
        ).reset_index(name="WeightedAverageCommute")

        # Store as JSON for fast retrieval
        return agg_df.to_json(date_format="iso", orient="split")
    
    @callback(
        Output("zoom-toggle-container", "style"),
        Input("province-dropdown", "value"),
    )
    def toggle_zoom_visibility(selected_province):
        """Show zoom toggle only if Quebec (DGUID 24) is selected."""
        if selected_province == "Quebec":
            return {"display": "block"}
        return {"display": "none"}

    @callback(
        Output("choropleth-map", "spec"),
        Input("preprocessed-data", "data"),
        Input("cd-dropdown", "value"),
        Input("zoom-toggle", "value"),
        State("choropleth-map", "spec"),
    )
    def update_choropleth(preprocessed_json, selected_cd, zoom_enabled, current_map):
        """Update choropleth visualization efficiently using precomputed data."""
        if preprocessed_json is None:
            return dash.no_update  # Prevent updates if no data

        # Convert JSON back to DataFrame
        agg_df = pd.read_json(preprocessed_json, orient="split")

        # Merge with GeoJSON features
        agg_dict = agg_df.set_index("DGUID")[["GEO", "WeightedAverageCommute"]].to_dict(orient="index")
        for feature in geojson_data["features"]:
            dguid = feature["properties"].get("DGUID")
            feature["properties"]["WeightedAverageCommute"] = agg_dict.get(dguid, {}).get("WeightedAverageCommute", None)
            feature["properties"]["GEO"] = agg_dict.get(dguid, {}).get("GEO", None)

        # --- Build Altair Geoshape Chart ---
        select_region = alt.selection_point(fields=['properties.DGUID'], name='select_region')

        highlight_condition = alt.condition(
            alt.datum["properties.DGUID"] == selected_cd,  # If selected
            alt.value(1),  # Full opacity
            alt.value(1) if selected_cd is None else alt.value(0.5)  # Otherwise, default to 1 or 0.5
        )

        projection_params = {"type": "transverseMercator", "rotate": [90, 0, 0]}
        print(agg_df.columns)
        unique_provinces = agg_df["Province"].unique()
        # If there's only one unique province, always use Mercator projection
        if len(unique_provinces) == 1:
            projection_params = {
                "type": "mercator",
            }

        if zoom_enabled and (agg_df["Province"] == "Quebec").all():
            projection_params = {
                "type": "mercator",
                "scale": 5000,  # Higher scale for zoom
                "center": [-71.2082, 46.8033],  # Approximate center of Southern Quebec
            }

        map_chart = alt.Chart(alt.Data(values=geojson_data["features"])).mark_geoshape(
            stroke="black"
        ).encode(
            color=alt.Color("properties.WeightedAverageCommute:Q",
                            scale=alt.Scale(scheme="orangered"),
                            title="Avg Commute (min)"),
            tooltip=[
                alt.Tooltip("properties.GEO:N", title="Census Division"),
                alt.Tooltip("properties.WeightedAverageCommute:Q", format=".1f", title="Avg Commute (min)"),
            ],
            opacity=highlight_condition
        ).add_params(
            select_region
        ).project(
            **projection_params
        ).properties(width="container", height=600)

        # Turn off the “...” menu
        map_chart_dict = map_chart.to_dict(format="vega")
        map_chart_dict["usermeta"] = {
            "embedOptions": {
                "actions": False
            }
        }

        return map_chart_dict

    @callback(
        Output("cd-dropdown", "value"),
        Input("choropleth-map", "signalData"),
        State("cd-dropdown", "value"),
    )
    def update_dropdown_from_map(signalData, current_dropdown):
        """Update dropdown when user selects a region on the map."""
        if signalData and 'select_region' in signalData and 'properties\\.DGUID' in signalData['select_region']:
            selected_cd = signalData['select_region']['properties\\.DGUID'][0]
            if selected_cd != current_dropdown:  # Avoid unnecessary updates
                return selected_cd
        return dash.no_update  # No change needed