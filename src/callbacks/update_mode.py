from dash import Input, Output, callback

def update_mode_callback(df, available_modes, dropdown_options):
    @callback(
        Output("mode-dropdown", "options"),
        [Input("cd-dropdown", "value")]
    )
    def update_mode_options(selected_cd):
        if not selected_cd:
            return dropdown_options
        # Filter for the selected CD and nonzero average commute time
        df_cd = df[(df["DGUID"] == selected_cd) & (df["AverageCommuteTime"] > 0)]
        # Get the unique modes that appear in the CD
        modes = df_cd["Main mode of commuting (21)"].unique()
        # Only keep those modes that are in the allowed available_modes list
        valid_modes = [m for m in modes if m in available_modes]
        options = [{"label": m, "value": m} for m in valid_modes]
        return options