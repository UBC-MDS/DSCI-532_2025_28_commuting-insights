from dash import Input, Output, callback
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import gaussian_kde
alt.data_transformers.enable("vegafusion")

def update_all_charts(df, time_bins, time_bin_order, geojson_data, cache):
    @callback(
        [ 
            Output("altair-violin-plot", "spec"),
            Output("altair-bar-chart", "spec"),
            Output("altair-line-chart", "spec")
        ],
        [
            Input("province-dropdown", "value"),
            Input("cd-dropdown", "value"),
            Input("choropleth-map", "signalData"),
            Input("mode-dropdown", "value"),
            Input("time-slider", "value")
        ]
    )
    @cache.memoize()
    def update_charts(selected_province, selected_cd, signalData, selected_modes, time_range):
        # ---- Choropleth Map Data Processing ----
        if signalData and 'select_region' in signalData and 'properties\\.DGUID' in signalData['select_region']:
            selected_cd = signalData['select_region']['properties\\.DGUID'][0]
        
        # ---- Altair Violin Plot with Weighted Horizontal Rules ----
        base_data = df[df["Time arriving at work (16)"].isin(time_bin_order.keys())].copy()
        base_data["time_order"] = base_data["Time arriving at work (16)"].apply(lambda t: time_bin_order[t])
        base_data = base_data[base_data["time_order"].between(time_range[0], time_range[1], inclusive="left")]

        if selected_cd:
            base_data["is_subset"] = base_data["DGUID"] == selected_cd
        else:
            base_data["is_subset"] = False
        
        # Right after you finish filtering base_data by time range, etc.:

        if not selected_modes or len(selected_modes) == 0:
            if selected_cd:
                # Highlight only modes that have nonzero AverageCommuteTime in the chosen CD
                modes_in_cd = base_data[
                    (base_data["DGUID"] == selected_cd) & (base_data["AverageCommuteTime"] > 0)
                ]["Main mode of commuting (21)"].unique()
                selected_modes = list(modes_in_cd)
            else:
                # No CD chosen, highlight all modes with nonzero AverageCommuteTime
                modes_nonzero = base_data[base_data["AverageCommuteTime"] > 0]["Main mode of commuting (21)"].unique()
                selected_modes = list(modes_nonzero)

        # Then set the "selected" flag:
        base_data["selected"] = base_data["Main mode of commuting (21)"].isin(selected_modes)

        # Compute national weighted averages per mode.
        agg_national = (
            base_data.groupby("Main mode of commuting (21)")
            .apply(lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
                if g["TotalDuration"].sum() != 0 else None)
            .reset_index(name="nationalMean")
        )

        # Compute CD weighted averages if a Census Division is selected.
        if selected_cd:
            cd_data = base_data[base_data["DGUID"] == selected_cd].copy()
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
            # Add selected flag to density_df
            density_df["selected"] = density_df["Main mode of commuting (21)"].isin(selected_modes)
        else:
            density_df = pd.DataFrame(columns=["Main mode of commuting (21)", "AverageCommuteTime", "density", "selected"])

        density_merged = pd.merge(density_df, agg_national, on="Main mode of commuting (21)", how="left")
        density_merged = pd.merge(density_merged, agg_cd, on="Main mode of commuting (21)", how="left")
        # Ensure the 'selected' column is present
        density_merged["selected"] = density_merged["Main mode of commuting (21)"].isin(selected_modes)

        # Create the weighted density area with conditional color encoding.
        weighted_violin = alt.Chart(density_merged).mark_area(orient="horizontal", opacity=0.25).encode(
            y=alt.Y("AverageCommuteTime:Q", title="Average Commute Time (min)"),
            x=alt.X("density:Q", stack="center", title=None, axis=None),
            color=alt.condition(
                alt.datum.selected,
                alt.value("red"),   # normal color for selected modes
                alt.value("grey")   # grey for unselected modes
            )
        ).properties(width=80, height=400)

        # National weighted average (horizontal rule) with conditional color.
        national_rule = alt.Chart(density_merged).mark_rule(strokeWidth=5).encode(
            y=alt.Y("nationalMean:Q"),
            color=alt.condition(
                alt.datum.selected,
                alt.value("#FF3C3C"),
                alt.value("grey")
            ),
            tooltip=[alt.Tooltip("nationalMean:Q", format=".1f", title="Average: Canada (min)"),
                    alt.Tooltip("", type="nominal", title="")]
        )

        # CD weighted average (horizontal rule) with conditional color.
        blue_rule = alt.Chart(density_merged).mark_rule(strokeWidth=5).encode(
            y=alt.Y("cdMean:Q"),
            color=alt.condition(
                alt.datum.selected,
                alt.value("blue"),
                alt.value("grey")
            ),
            tooltip=[alt.Tooltip("cdMean:Q", format=".1f", title="Average: Selected CD (min)"),
                    alt.Tooltip("", type="nominal", title="")]
        )

        # Combine the density area and the horizontal rules, faceted by mode.
        final_violin = alt.layer(weighted_violin, national_rule, blue_rule).facet(
            column=alt.Column("Main mode of commuting (21):N", title="Commuting Mode")
        ).resolve_scale(x="independent")

        # (The legend and subsequent chart configurations remain unchanged.)


        legend_data = pd.DataFrame({
            "Label": ["Average: Canada (min)", "Average: Selected CD (min)", "Unavailable"],
            "Color": ["red", "blue", "grey"]
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
            bar_data = bar_data[bar_data["DGUID"] == selected_cd]
        if selected_modes and len(selected_modes) > 0:
            bar_data = bar_data[bar_data["Main mode of commuting (21)"].isin(selected_modes)]
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
        ).add_selection(
            alt.selection_interval(bind='scales')
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
            # ---- Altair Line Chart: Weighted Average Commute Time by Time of Day ----
        line_df = df[df["Time arriving at work (16)"].isin(time_bin_order.keys())].copy()
        if selected_cd:
            line_df = line_df[line_df["DGUID"] == selected_cd]
        if selected_modes and len(selected_modes) > 0:
            line_df = line_df[line_df["Main mode of commuting (21)"].isin(selected_modes)]
        # Filter based on the time slider range:
        line_df = line_df[line_df["Time arriving at work (16)"].apply(lambda t: time_bin_order[t]).between(time_range[0], time_range[1], inclusive="left")]
        line_df_agg = line_df.groupby(["Time arriving at work (16)", "Main mode of commuting (21)"]).apply(
            lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
            if g["TotalDuration"].sum() != 0 else None
        ).reset_index(name="weighted_avg")

        line_df_agg = line_df_agg[line_df_agg["weighted_avg"] != 0]
        
        # Create a dictionary to map full labels to simplified labels.
        simplified_labels = {
            "Between 5 a.m. and 5:29 a.m.": "5am - 5:29am",
            "Between 5:30 a.m. and 5:59 a.m.": "5:30am - 5:59am",
            "Between 6 a.m. and 6:29 a.m.": "6am - 6:29am",
            "Between 6:30 a.m. and 6:59 a.m.": "6:30am - 6:59am",
            "Between 7 a.m. and 7:29 a.m.": "7am - 7:29am",
            "Between 7:30 a.m. and 7:59 a.m.": "7:30am - 7:59am",
            "Between 8 a.m. and 8:29 a.m.": "8am - 8:29am",
            "Between 8:30 a.m. and 8:59 a.m.": "8:30am - 8:59am",
            "Between 9 a.m. and 9:59 a.m.": "9am - 9:59am",
            "Between 10 a.m. and 10:59 a.m.": "10am - 10:59am",
            "Between 11 a.m. and 11:59 a.m.": "11am - 11:59am",
            "Between 12 p.m. and 3:59 p.m.": "12pm - 3:59pm",
            "Between 4 p.m. and 7:59 p.m.": "4pm - 7:59pm",
            "Between 8 p.m. and 11:59 p.m.": "8pm - 11:59pm",
            "Between 12 a.m. and 4:59 a.m.": "12am - 4:59am"
        }

        # Create a simplified order list that matches the original time_bins order.
        simplified_time_bins = [simplified_labels[t] for t in time_bins]

        # In your line chart data (line_df_agg), create a new column "TimeSimplified":
        line_df_agg["TimeSimplified"] = line_df_agg["Time arriving at work (16)"].map(simplified_labels)

        
        line_chart_spec = alt.Chart(line_df_agg).mark_line(point=True).encode(
            x=alt.X("TimeSimplified:N", sort=simplified_time_bins, title="Time arriving at work"),
            y=alt.Y("weighted_avg:Q", title="Average Commute Time (min)"),
            color=alt.Color("Main mode of commuting (21):N", title="Mode"),
            tooltip=[
                alt.Tooltip("TimeSimplified:N", title="Time"),
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
        
        return final_violin_with_legend.to_dict(format="vega"), bar_chart.to_dict(format="vega"), line_chart_spec.to_dict(format="vega")