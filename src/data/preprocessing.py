import pandas as pd
import geopandas as gpd
import json

def load(geo_path, commuting_path):

    gdf = gpd.read_parquet(geo_path)

    # Subset to only the columns we need
    gdf = gdf[["DGUID", "CDNAME", "geometry"]]

    # Fix the projection: EPSG:3347 → EPSG:4326 (lat/lon)
    gdf.crs = "EPSG:3347"
    gdf_latlon = gdf.to_crs(epsg=4326)

    gdf_latlon["geometry"] = gdf_latlon["geometry"].buffer(0)

    # Convert to GeoJSON dictionary
    geojson_data = json.loads(gdf_latlon.to_json())


    # Load and filter the commuting data
    df = pd.read_parquet(commuting_path)
    # Keep only selected columns (including the count columns):
    df = df[[ 
        "GEO", 
        "DGUID", 
        "Time arriving at work (16)", 
        "Main mode of commuting (21)", 
        "Commuting duration (7):Total - Commuting duration[1]",
        "Commuting duration (7):Average commuting duration (in minutes)[7]",
        "Commuting duration (7):Less than 15 minutes[2]",
        "Commuting duration (7):15 to 29 minutes[3]",
        "Commuting duration (7):30 to 44 minutes[4]",
        "Commuting duration (7):45 to 59 minutes[5]",
        "Commuting duration (7):60 minutes and over[6]",
        "Province"
    ]]
    # Rename columns for convenience.
    df = df.rename(
        columns={
            "Commuting duration (7):Average commuting duration (in minutes)[7]": "AverageCommuteTime",
            "Commuting duration (7):Total - Commuting duration[1]": "TotalDuration",
            "Commuting duration (7):Less than 15 minutes[2]": "Less15",
            "Commuting duration (7):15 to 29 minutes[3]": "15to29",
            "Commuting duration (7):30 to 44 minutes[4]": "30to44",
            "Commuting duration (7):45 to 59 minutes[5]": "45to59",
            "Commuting duration (7):60 minutes and over[6]": "60plus"
        }
    )
    # Convert numeric columns.
    df["AverageCommuteTime"] = pd.to_numeric(df["AverageCommuteTime"], errors="coerce")
    df["TotalDuration"] = pd.to_numeric(df["TotalDuration"], errors="coerce")
    df["Less15"] = pd.to_numeric(df["Less15"], errors="coerce")
    df["15to29"] = pd.to_numeric(df["15to29"], errors="coerce")
    df["30to44"] = pd.to_numeric(df["30to44"], errors="coerce")
    df["45to59"] = pd.to_numeric(df["45to59"], errors="coerce")
    df["60plus"] = pd.to_numeric(df["60plus"], errors="coerce")

    return geojson_data, df

def widget_inputs(df):
    # Create dropdown options with province names as labels and DGUID prefixes as values
    provinces = sorted(df["Province"].unique())
    dropdown_province_options = [
        {"label": province, "value": province} for province in provinces
    ]

    # Define the selectable commuting modes
    available_modes = sorted(df["Main mode of commuting (21)"].unique())  # Sort alphabetically
    dropdown_options = [{"label": mode, "value": mode} for mode in available_modes]

    # Extract unique Census Divisions
    available_cdnames = df["GEO"].unique()
    dropdown_cd_options = [{"label": row["GEO"], "value": row["DGUID"]} for _, row in df[["GEO", "DGUID"]].drop_duplicates().iterrows()]

    # Define the time bins present in the dataset
    time_bins = [
        "Between 5 a.m. and 5:29 a.m.", "Between 5:30 a.m. and 5:59 a.m.",
        "Between 6 a.m. and 6:29 a.m.", "Between 6:30 a.m. and 6:59 a.m.",
        "Between 7 a.m. and 7:29 a.m.", "Between 7:30 a.m. and 7:59 a.m.",
        "Between 8 a.m. and 8:29 a.m.", "Between 8:30 a.m. and 8:59 a.m.",
        "Between 9 a.m. and 9:59 a.m.", "Between 10 a.m. and 10:59 a.m.",
        "Between 11 a.m. and 11:59 a.m.", "Between 12 p.m. and 3:59 p.m.",
        "Between 4 p.m. and 7:59 p.m.", "Between 8 p.m. and 11:59 p.m.",
        "Between 12 a.m. and 4:59 a.m."
    ]

    # Create a mapping from time bin to its order (0-indexed)
    time_bin_order = {t: i for i, t in enumerate(time_bins)}

    # Build slider marks
    point_labels = {
        "Between 5 a.m. and 5:29 a.m.": "5am", "Between 5:30 a.m. and 5:59 a.m.": "5:30",
        "Between 6 a.m. and 6:29 a.m.": "6am", "Between 6:30 a.m. and 6:59 a.m.": "6:30",
        "Between 7 a.m. and 7:29 a.m.": "7am", "Between 7:30 a.m. and 7:59 a.m.": "7:30",
        "Between 8 a.m. and 8:29 a.m.": "8am", "Between 8:30 a.m. and 8:59 a.m.": "8:30",
        "Between 9 a.m. and 9:59 a.m.": "9am", "Between 10 a.m. and 10:59 a.m.": "10am",
        "Between 11 a.m. and 11:59 a.m.": "11am", "Between 12 p.m. and 3:59 p.m.": "12pm",
        "Between 4 p.m. and 7:59 p.m.": "4pm", "Between 8 p.m. and 11:59 p.m.": "8pm",
        "Between 12 a.m. and 4:59 a.m.": "12am"
    }
    slider_marks = {i: point_labels[time_bins[i]] for i in range(len(time_bins))}
    slider_marks[len(time_bins)] = "5am"  # Extra mark for the right endpoint

    return provinces, dropdown_province_options, available_modes, dropdown_options, available_cdnames, dropdown_cd_options, time_bins, time_bin_order, slider_marks
