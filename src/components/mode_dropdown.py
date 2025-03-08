import dash_bootstrap_components as dbc
from dash import dcc

def create_mode_dropdown(dropdown_options):
    mode_dropdown_label = dbc.Label("Commuting Mode")
    mode_dropdown = dcc.Dropdown(
        id="mode-dropdown",
        options=dropdown_options,
        multi=True,
        placeholder="Select one or more modes...",
        searchable=True
    )
    return mode_dropdown_label, mode_dropdown