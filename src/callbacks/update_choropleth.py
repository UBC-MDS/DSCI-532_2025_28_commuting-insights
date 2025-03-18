from dash import Input, Output, callback, State, no_update, html
import dash_bootstrap_components as dbc
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import gaussian_kde
alt.data_transformers.enable("vegafusion")

def update_choropleth_callback(df, time_bin_order, geojson_data, cache):
    
    @callback(
        Output("preprocessed-data", "data"),  # Store precomputed values
        Output("top-3-cds-data", "data"),  # Store top 3 CDs
        Output("bot-3-cds-data", "data"),
        Input("province-dropdown", "value"),
        Input("mode-dropdown", "value"),
        Input("time-slider", "value"),
    )
    @cache.memoize()
    def preprocess_data(selected_province, selected_modes, time_range):
        """Preprocess data and find top 3 Census Divisions with highest commute time."""
        map_df = df[["GEO", "DGUID", "Time arriving at work (16)", "Main mode of commuting (21)", "AverageCommuteTime", "TotalDuration", "Province"]].copy()

        # Apply filters efficiently
        if selected_province:
            map_df = map_df[map_df["Province"] == selected_province]
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

        # Get the top 3 CDs
        top_3_cds = agg_df.nlargest(3, "WeightedAverageCommute")[["GEO", "WeightedAverageCommute"]]
        top_3_cds_json = top_3_cds.to_json(date_format="iso", orient="split")

        bot_3_cds = agg_df.nsmallest(3, "WeightedAverageCommute")[["GEO", "WeightedAverageCommute"]]
        bot_3_cds_json = bot_3_cds.to_json(date_format="iso", orient="split")

        # Store as JSON for fast retrieval
        return agg_df.to_json(date_format="iso", orient="split"), top_3_cds_json, bot_3_cds_json

    
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
        State("province-dropdown", "value")
    )
    def update_choropleth(preprocessed_json, selected_cd, zoom_enabled, selected_province):
        """Update choropleth visualization efficiently using precomputed data."""
        if preprocessed_json is None:
            return no_update  # Prevent updates if no data

        # Convert JSON back to DataFrame
        agg_df = pd.read_json(preprocessed_json, orient="split")

        # Merge with GeoJSON features
        agg_dict = agg_df.set_index("DGUID")[["GEO", "WeightedAverageCommute"]].to_dict(orient="index")
        for feature in geojson_data["features"]:
            dguid = feature["properties"].get("DGUID")
            feature["properties"]["WeightedAverageCommute"] = agg_dict.get(dguid, {}).get("WeightedAverageCommute", None)
            # feature["properties"]["GEO"] = agg_dict.get(dguid, {}).get("GEO", None)

        # --- Build Altair Geoshape Chart ---
        select_region = alt.selection_point(fields=['properties.DGUID'], name='select_region')

        highlight_condition = alt.condition(
            alt.datum["properties.DGUID"] == selected_cd,  # If selected
            alt.value(1),  # Full opacity
            alt.value(1) if selected_cd is None else alt.value(0.5)  # Otherwise, default to 1 or 0.5
        )

        projection_params = {"type": "transverseMercator", "rotate": [90, 0, 0]}

        
        if selected_province:
            projection_params = {
                "type": "mercator",
            }

        if zoom_enabled and selected_province == "Quebec":
            projection_params = {
                "type": "mercator",
                "scale": 5000,  # Higher scale for zoom
                "center": [-71.2082, 46.8033],  # Approximate center of Southern Quebec
            }

        map_chart = alt.Chart(alt.Data(values=geojson_data["features"])).mark_geoshape(
            stroke="black"
        ).encode(
            color=alt.Color("properties.WeightedAverageCommute:Q",
                            scale=alt.Scale(domain=[0, 60], scheme="orangered"),
                            title="Avg Commute (mins)"),
            tooltip=[
                alt.Tooltip("properties.CDNAME:N", title="Census Division"),
                alt.Tooltip("properties.WeightedAverageCommute:Q", format=".1f", title="Avg Commute (mins)"),
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
        return no_update


    @callback(
        Output("top-3-cds-content", "children"),
        Output("bot-3-cds-content", "children"),
        Input("top-3-cds-data", "data"),
        Input("bot-3-cds-data", "data"),
    )
    def update_top_3_cds_card(top_3_json, bot_3_json):
        """Update the card with top 3 highest and lowest commute times."""
        if top_3_json is None:
            return "No data available."

        top_3_df = pd.read_json(top_3_json, orient="split")

        if top_3_df.empty:
            return "No data available."
        
        if bot_3_json is None:
            return "No data available."

        bot_3_df = pd.read_json(bot_3_json, orient="split")

        if bot_3_df.empty:
            return "No data available."

        # Reset index for proper ranking
        top_3_df = top_3_df.reset_index(drop=True)
        bot_3_df = bot_3_df.reset_index(drop=True)

        # Fixed colors: Red for highest, Green for lowest
        high_color = "#D9534F"  # Bootstrap "danger" red
        low_color = "#5CB85C"   # Bootstrap "success" green


        # Generate cards for highest commute times (red)
        top_3_high_cards = [
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"#{i+1}: {row['GEO']}", className="card-title", style={"color": "white"}),
                        html.P(f"{row['WeightedAverageCommute']:.1f} min", className="card-text", style={"color": "white"})
                    ], style={"textAlign": "center"})
                ], style={
                    "backgroundColor": high_color,
                    "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                    "border-radius": "10px",
                    "margin": "5px",
                    "padding": "10px",
                    "height": "100%"
                }),
                width=12
            ) for i, row in top_3_df.iterrows()
        ]

        # Generate cards for lowest commute times (green)
        top_3_low_cards = [
            dbc.Col(
                dbc.Card([
                    dbc.CardBody([
                        html.H6(f"#{i+1}: {row['GEO']}", className="card-title", style={"color": "white"}),
                        html.P(f"{row['WeightedAverageCommute']:.1f} min", className="card-text", style={"color": "white"})
                    ], style={"textAlign": "center"})
                ], style={
                    "backgroundColor": low_color,
                    "box-shadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
                    "border-radius": "10px",
                    "margin": "5px",
                    "padding": "10px",
                    "height": "100%"
                }),
                width=12
            ) for i, row in bot_3_df.iterrows()
        ]

        return dbc.Container([dbc.Row(html.H5("CDs with Highest Commute Time")), dbc.Row(top_3_high_cards, className="g-2")]), dbc.Container([dbc.Row(html.H5("CDs with Lowest Commute Time")), dbc.Row(top_3_low_cards, className="g-2")])

