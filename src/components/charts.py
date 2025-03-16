from dash import dcc, html
import dash_vega_components as dvc

def create_choropleth():
    map_title = html.H5("Average Commute Time by Census Division")
    choropleth_map = dvc.Vega(id="choropleth-map", spec={}, signalsToObserve=['select_region'])
    return map_title, choropleth_map

def create_violin():
    violin_title = html.H5("Commute Times by Mode, Selected Census Division vs. Canada")
    violin_plot = dvc.Vega(id="altair-violin-plot")
    return violin_title, violin_plot

def create_bar():
    bar_title = html.H5("Commute Duration Distribution")
    bar_chart = dvc.Vega(id="altair-bar-chart")
    return bar_title, bar_chart

def create_line():
    line_title = html.H5("Average Commute Time by Time of Day")
    line_chart = dvc.Vega(id="altair-line-chart")
    return line_title, line_chart

def create_pie():
    pie_title = html.H5("Commute mode Distribution")
    pie_chart = dvc.Vega(id="altair-pie-chart")
    return pie_title, pie_chart