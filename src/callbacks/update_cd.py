from dash import Input, Output, callback

def update_cd_callback(df, dropdown_cd_options):

    @callback(
        Output("cd-dropdown", "options"),
        [Input("mode-dropdown", "value")]
    )
    def update_cd_options(selected_modes):
        # If no mode is selected, return all CD options.
        if not selected_modes or len(selected_modes) == 0:
            return dropdown_cd_options
        # Filter the dataframe for selected modes with nonzero AverageCommuteTime.
        df_modes = df[(df["Main mode of commuting (21)"].isin(selected_modes)) &
                    (df["AverageCommuteTime"] > 0)]
        unique_cds = df_modes["GEO"].unique()
        # Sort the CDs for consistency
        options = [{"label": cd, "value": cd} for cd in sorted(unique_cds)]
        return options