import dash_bootstrap_components as dbc
from dash import html

def create_title():
    title = html.H1("Commuting Insights Dashboard")
    return title

def create_footer():
    footer = dbc.Container([
        html.Hr(),
        dbc.Row(dbc.Col(html.P("Commuting Insights is an interactive visualization dashboard for analyzing commuting patterns across Canadian Census Divisions. Users can explore commute times by mode of transport, time of day, and region. Commuting Insights aims to assist the Canadian Federal government in identifying trends for the purpose of informing national transportation funding strategies."), md=6)),
        dbc.Row(dbc.Col(html.P("Created by:"))),
        dbc.Row(dbc.Col(html.Ul([
            html.Li(html.A("Francisco Ramirez", href="https://github.com/fraramfra", target="_blank")),
            html.Li(html.A("Jinxiong (Eugene) You", href="https://github.com/jinxyou", target="_blank")),
            html.Li(html.A("Derek Rodgers", href="https://github.com/derekrodgers", target="_blank")),
            html.Li(html.A("Han Wang", href="https://github.com/hanwang205", target="_blank")),
        ]))),
        dbc.Row(dbc.Col(html.A("View on GitHub", href="https://github.com/UBC-MDS/DSCI-532_2025_28_commuting-insights", target="_blank", style={"font-weight": "bold"}))),
        html.Br(),
        dbc.Row(dbc.Col(html.P("Last updated: Saturday, March 8th 2025", style={"font-style": "italic"})))
    ], fluid=True)
    return footer