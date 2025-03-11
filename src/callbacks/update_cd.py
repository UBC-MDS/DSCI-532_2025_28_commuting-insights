from dash import Input, Output, callback

def update_cd_callback(df, dropdown_cd_options):

    @callback(
        Output("cd-dropdown", "options"),
        [Input("mode-dropdown", "value"), Input("province-dropdown", "value")]  # Added province input
    )
    def update_cd_options(selected_modes, selected_province):
        # Start with the full dataframe
        filtered_df = df.copy()

        # Filter by province if selected
        if selected_province:
            filtered_df = filtered_df[filtered_df["DGUID"].astype(str).str.startswith(selected_province)]

        # Filter by selected modes if any
        if selected_modes and len(selected_modes) > 0:
            filtered_df = filtered_df[(filtered_df["Main mode of commuting (21)"].isin(selected_modes)) & 
                                      (filtered_df["AverageCommuteTime"] > 0)]

        # Get unique Census Divisions (GEO) after filtering
        # unique_cds = filtered_df["GEO"].unique()
        
        # Sort for consistency
        options = [{"label": row["GEO"], "value": row["DGUID"]} for _, row in filtered_df[["GEO", "DGUID"]].drop_duplicates().iterrows()]
        
        return options
