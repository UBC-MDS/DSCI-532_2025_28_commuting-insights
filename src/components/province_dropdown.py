import dash_bootstrap_components as dbc
from dash import dcc

def create_province_dropdown(dropdown_options):
    province_dropdown_label = dbc.Label("Province / Territory")
    province_dropdown = dcc.Dropdown(
        id="province-dropdown",
        options=dropdown_options,
        multi=False,
        placeholder="Select one province/territory...",
        searchable=True
    )
    return province_dropdown_label, province_dropdown