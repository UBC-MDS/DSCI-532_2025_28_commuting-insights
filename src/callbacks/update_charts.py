from dash import Input, Output, callback, State, no_update
import altair as alt
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.stats import gaussian_kde
alt.data_transformers.enable("vegafusion")

def update_all_charts(df, time_bins, time_bin_order, cache):
    @callback(
        Output("preprocessed-chart-data", "data"),
        Input("time-slider", "value")
    )
    def preprocessing_charts(time_range):
        base_data = df[df["Time arriving at work (16)"].isin(time_bin_order.keys())].copy()
        base_data["time_order"] = base_data["Time arriving at work (16)"].apply(lambda t: time_bin_order[t])
        base_data = base_data[base_data["time_order"].between(time_range[0], time_range[1], inclusive="left")]
        return base_data.to_json(date_format="iso", orient="split")
    
    @callback(
        Output("altair-violin-plot", "spec"),
        Input("preprocessed-chart-data", "data"),
        Input("cd-dropdown", "value")
    )
    @cache.memoize()
    def update_violin(base_data_json, selected_cd):
        if base_data_json is None:
            return no_update  # Prevent updates if no data
        
        base_data = pd.read_json(base_data_json, orient="split")

        # ---- Altair Violin Plot with Weighted Horizontal Rules ----
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
        else:
            density_df = pd.DataFrame(columns=["Main mode of commuting (21)", "AverageCommuteTime", "density"])

        density_merged = pd.merge(density_df, agg_national, on="Main mode of commuting (21)", how="left")
        density_merged = pd.merge(density_merged, agg_cd, on="Main mode of commuting (21)", how="left")

        # Create the weighted density area with conditional color encoding.
        weighted_violin = alt.Chart(density_merged).mark_area(orient="horizontal", opacity=0.25).encode(
            y=alt.Y("AverageCommuteTime:Q", title="Commute Time (mins)"),
            x=alt.X("density:Q", stack="center", title=None, axis=None),
            color=alt.value("red")  # Always red, no more graying out!
        ).properties(width=78, height=400)

        # National weighted average (horizontal rule) with conditional color.
        national_rule = alt.Chart(density_merged).mark_rule(strokeWidth=5).encode(
            y=alt.Y("nationalMean:Q"),
            color=alt.value("#FF3C3C"),  # Always red, no conditions
            tooltip=[alt.Tooltip("nationalMean:Q", format=".1f", title="Average: Canada (mins)")]
        )

        # CD weighted average (horizontal rule) with conditional color.
        blue_rule = (
            alt.Chart(density_merged)
            .transform_filter("datum.cdMean != 0 && datum.cdMean != null")  # Hides if 0 or missing
            .mark_rule(strokeWidth=5)
            .encode(
                y=alt.Y("cdMean:Q"),
                color=alt.value("blue"),
                tooltip=[alt.Tooltip("cdMean:Q", format=".1f", title="Average: Selected CD (mins)")]
            )
        )

        # Combine the density area and the horizontal rules, faceted by mode.
        final_violin = alt.layer(weighted_violin, national_rule, blue_rule).facet(
            column=alt.Column("Main mode of commuting (21):N",
                              title="Commuting Mode",
                              header=alt.Header(labelFontSize=13, labelLimit=100))
        ).resolve_scale(x="independent")

        legend_data = pd.DataFrame({
            "Label": ["Average: Canada (mins)", "Average: Selected CD (mins)"],
            "Color": ["#FF3C3C", "blue"]
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
            .properties(width=120, height=40)
        )

        final_violin_with_legend = (
            alt.HConcatChart(hconcat=[final_violin, custom_legend])
            .configure_view(stroke=None)
            .configure_axis(titleFontSize=14, labelFontSize=12)
            .configure_header(titleFontSize=14, labelFontSize=12)
        )

        final_violin_dict = final_violin_with_legend.to_dict(format="vega")
        final_violin_dict["usermeta"] = {
            "embedOptions": {
                "actions": False
            }
        }

        return final_violin_dict


    @callback(
        [ 
            Output("altair-bar-chart", "spec"),
            Output("altair-line-chart", "spec")
        ],
        [
            Input("preprocessed-chart-data", "data"),
            Input("cd-dropdown", "value"),
            Input("mode-dropdown", "value"),
            State("mode-dropdown", "options"),
            Input("time-slider", "value")
        ]
    )
    @cache.memoize()
    def update_charts(base_data_json, selected_cd, selected_modes, mode_options, time_range):
        if base_data_json is None:
            return no_update  # Prevent updates if no data
        
        base_data = pd.read_json(base_data_json, orient="split")
        if not selected_modes:
            selected_modes = [mode["label"] for mode in mode_options]

        # ---- Altair Bar Chart: Stacked Counts for Duration Categories ----
        # Use the same filtered data (base_data) and melt the five duration columns.
        bar_data = base_data.copy()
        if selected_cd:
            bar_data = bar_data[bar_data["DGUID"] == selected_cd]
        if selected_modes:
            bar_data = bar_data[bar_data["Main mode of commuting (21)"].isin(selected_modes)]
        bar_data = bar_data[["Main mode of commuting (21)", "Less15", "15to29", "30to44", "45to59", "60plus"]].copy()
        bar_data = bar_data.melt(id_vars=["Main mode of commuting (21)"],
                                value_vars=["Less15", "15to29", "30to44", "45to59", "60plus"],
                                var_name="DurationCategory", value_name="Count")
        # Group by DurationCategory and Mode, summing counts.
        bar_data = bar_data.groupby(["DurationCategory", "Main mode of commuting (21)"], as_index=False)["Count"].sum()

        # Color code tied to commute mode
        mode_colors = {
            'Bicycle': '#377eb8',  # Blue
            'Car, truck or van': '#ff7f00',  # Orange
            'Motorcycle, scooter or moped': '#e41a1c',  # Red
            'Other method': '#8cbed6',   # Dark Blue Sky
            'Public transit': '#4daf4a', # Green
            'Walked': '#ffdb58'  # Mustard
        }

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
                    title=None,
                    sort=["> 60 mins", "45 - 59 mins", "30 - 44 mins", "15 - 29 mins", "< 15 mins"],
                    axis=alt.Axis(labelAlign="left", orient="right")
            ),
            color=alt.Color("Main mode of commuting (21):N", 
                            title="Mode", 
                            scale=alt.Scale(domain = list(mode_colors.keys()), range = list(mode_colors.values()))),
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
        line_df = base_data.copy()
        if selected_cd:
            line_df = line_df[line_df["DGUID"] == selected_cd]
        if selected_modes:
            line_df = line_df[line_df["Main mode of commuting (21)"].isin(selected_modes)]
        # Filter based on the time slider range:
        line_df = line_df[line_df["Time arriving at work (16)"].apply(lambda t: time_bin_order[t]).between(time_range[0], time_range[1], inclusive="left")]
        line_df_agg = line_df.groupby(["Time arriving at work (16)", "Main mode of commuting (21)"]).apply(
            lambda g: (g["AverageCommuteTime"] * g["TotalDuration"]).sum() / g["TotalDuration"].sum()
            if g["TotalDuration"].sum() != 0 else None
        ).reset_index(name="weighted_avg")

        line_df_agg = line_df_agg[line_df_agg["weighted_avg"] != 0]
        
        # 1️⃣ Define Midpoints for Data Placement
        time_midpoints = {
            "Between 5 a.m. and 5:29 a.m.": 1.25,   # Between 5am and 5:30
            "Between 5:30 a.m. and 5:59 a.m.": 1.75,  # Between 5:30 and 6am
            "Between 6 a.m. and 6:29 a.m.": 2.25,
            "Between 6:30 a.m. and 6:59 a.m.": 2.75,
            "Between 7 a.m. and 7:29 a.m.": 3.25,
            "Between 7:30 a.m. and 7:59 a.m.": 3.75,
            "Between 8 a.m. and 8:29 a.m.": 4.25,
            "Between 8:30 a.m. and 8:59 a.m.": 4.75,
            "Between 9 a.m. and 9:59 a.m.": 5.5,   # Full hour bin sits at 5.5
            "Between 10 a.m. and 10:59 a.m.": 6.5,
            "Between 11 a.m. and 11:59 a.m.": 7.5,
            "Between 12 p.m. and 3:59 p.m.": 10,  # Midpoint of 12pm-4pm
            "Between 4 p.m. and 7:59 p.m.": 14,
            "Between 8 p.m. and 11:59 p.m.": 18,
            "Between 12 a.m. and 4:59 a.m.": 22.5
        }

        # Apply midpoints to DataFrame
        line_df_agg["TimeMidpoint"] = line_df_agg["Time arriving at work (16)"].map(time_midpoints)

        # 2️⃣ Define Tick Positions for Labels
        tick_positions = {
            1: "5am",
            1.5: "5:30",
            2: "6am",
            2.5: "6:30",
            3: "7am",
            3.5: "7:30",
            4: "8am",
            4.5: "8:30",
            5: "9am",
            5.5: "9:30",
            6: "10am",
            6.5: "10:30",
            7: "11am",
            7.5: "11:30",
            8: "12pm",
            10: "2pm",
            12: "4pm",
            14: "6pm",
            16: "8pm",
            18: "10pm",
            20: "12am",
            22.5: "2:30",
            25: "5am"
        }

        # 3️⃣ Generate Altair Label Expression Automatically
        values_list = sorted(tick_positions.keys())  # Sorted list of numeric tick positions
        label_expr = " ".join([f"datum.value == {val} ? '{label}' :" for val, label in tick_positions.items()]) + " ''"


        # 5️⃣ Create Altair Line Chart
        line_chart_spec = alt.Chart(line_df_agg).mark_line(point=False).encode(
            x=alt.X(
                "TimeMidpoint:Q",
                scale=alt.Scale(domain=[min(values_list), max(values_list)]),  # Ensure proper axis limits
                title="Time arriving at work",
                axis=alt.Axis(
                    # tickCount=20,
                    values=values_list,  # Ensure proper tick placement
                    labelExpr=label_expr  # Ensure readable labels
                )
            ),
            y=alt.Y("weighted_avg:Q", title="Average Commute Time (mins)"),
            color=alt.Color(
                "Main mode of commuting (21):N",
                title="Mode",
                scale=alt.Scale(domain=list(mode_colors.keys()), range=list(mode_colors.values()))
            ),
            tooltip=[
                alt.Tooltip("Time arriving at work (16):N", title="Time Bin"),
                alt.Tooltip("weighted_avg:Q", format=".1f", title="Avg Commute (mins)")
            ]
        ).add_selection(
            alt.selection_interval(bind='scales')
        ).properties(
            width="container",
            height=400
        ).configure_axis(
            titleFontSize=14,
            labelFontSize=13,
            labelAngle=0
        ).configure_legend(
            titleFontSize=14,
            labelFontSize=13
        )





        
        ## ---- Remove "..." dropdown from all the charts ---- 
    

        bar_chart_dict = bar_chart.to_dict(format="vega")
        bar_chart_dict["usermeta"] = {
            "embedOptions": {
                "actions": False
            }
        }

        line_chart_spec_dict = line_chart_spec.to_dict(format="vega")
        line_chart_spec_dict["usermeta"] = {
            "embedOptions": {
                "actions": False
            }
        }

        return bar_chart_dict, line_chart_spec_dict
