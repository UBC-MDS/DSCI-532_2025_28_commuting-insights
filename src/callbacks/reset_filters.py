from dash import Input, Output, callback
from dash.exceptions import PreventUpdate

def reset_filters_callback(time_bins, cache):
    @callback(
        Output("province-dropdown", "value"),
        Output("cd-dropdown", "value", allow_duplicate=True),
        Output("mode-dropdown", "value"),
        Output("time-slider", "value"),
        Input("reset-button", "n_clicks"),
        prevent_initial_call=True
    )
    @cache.memoize()
    def reset_filters(n):
        if not n:
            raise PreventUpdate  # Ignore if button not clicked
        return None, None, [], [0, len(time_bins)]