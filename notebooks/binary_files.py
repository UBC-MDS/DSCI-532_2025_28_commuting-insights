import geopandas as gpd
import pandas as pd

#GeoJSON to GeoPandas
gdf = gpd.read_file("../data/raw/geojson/lcd_000b21a_e_simplified_0.25percent.geojson")
#GeoPandas to Parquet file
gdf.to_parquet("../data/processed//binary/data_geojson.parquet", engine='pyarrow')

print("GeoJSON has been converted to Parquet.")

#CSV to Pandas
df = pd.read_csv("../data/processed/commuting_data/commuting_data_with_province.csv")
#Pandas to Parquet
df.to_parquet("../data/processed//binary/data_csv.parquet", engine='pyarrow')

print("CSV has been converted to Parquet.")