import geopandas as gpd
import fiona
import pandas as pd

gpkg_path = 'Dominikanske republikk.gpkg'

# List all layers in the GeoPackage
layers = fiona.listlayers(gpkg_path)
print("\nLayers in the GeoPackage:")
print("------------------------")
for i, layer_name in enumerate(layers, 1):
    try:
        # Try to read as geodataframe first
        gdf = gpd.read_file(gpkg_path, layer=layer_name)
        print(f"{i}. Layer: {layer_name}")
        print(f"   - Number of features: {len(gdf)}")
        if isinstance(gdf, gpd.GeoDataFrame):
            print(f"   - Geometry types: {list(gdf.geometry.type.unique())}")
            print(f"   - CRS: {gdf.crs}")
        print("   - Columns:", list(gdf.columns))
    except Exception as e:
        print(f"{i}. Layer: {layer_name} (Non-geometric or empty layer)")
    print("------------------------") 