import dash_bootstrap_components as dbc
from dash import dcc

def create_cd_dropdown(dropdown_cd_options):
    cd_dropdown_label = dbc.Label("Census Division (CD)")
    cd_dropdown = dcc.Dropdown(
        id="cd-dropdown",
        options=dropdown_cd_options,
        multi=False,
        placeholder="Select a Division...",
        searchable=True
    )
    return cd_dropdown_label, cd_dropdown