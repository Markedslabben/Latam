import geopandas as gpd
import pandas as pd

# Read the shapefile
shapefile_path = r'C:\Users\klaus\klauspython\Latam\Inputdata\GISdata\Turbine layout 14.shp'
gdf = gpd.read_file(shapefile_path)

# Extract coordinates
coords_df = pd.DataFrame({
    'turbine_id': range(1, len(gdf) + 1),
    'x_coord': gdf.geometry.x,
    'y_coord': gdf.geometry.y
})

# Save to CSV
output_csv = 'Inputdata/Turbine Layout 14.csv'
coords_df.to_csv(output_csv, index=False)
print(f"Exported to {output_csv}")
