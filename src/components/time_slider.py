import dash_bootstrap_components as dbc
from dash import dcc

def create_time_slider(time_bins, slider_marks):
    time_slider_label = dbc.Label("Arrival Time")
    time_slider = dcc.RangeSlider(
        id="time-slider",
        min=0,
        max=len(time_bins),
        value=[0, len(time_bins)],
        marks=slider_marks,
        step=1,
        allowCross=False,
        pushable=1
    )
    return time_slider_label, time_slider