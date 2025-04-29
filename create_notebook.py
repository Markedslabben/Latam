import nbformat as nbf

# Create a new notebook
nb = nbf.v4.new_notebook()

# Add a markdown cell with title and description
markdown_cell = nbf.v4.new_markdown_cell('''# Wind Farm Layout Analysis

This notebook demonstrates comprehensive wind farm layout analysis using the windfarm_layout module.
We'll visualize:
- Terrain contours
- Internal roads
- Turbine locations
- Project boundary
''')

# Add a code cell with imports
imports_cell = nbf.v4.new_code_cell('''import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from windfarm_layout import plot_layers, create_plot, load_all_layers

%matplotlib inline
''')

# Add a code cell for loading data
load_data_cell = nbf.v4.new_code_cell('''# Load all GIS layers
geopackage_path = "internal_roads.gpkg"  # GeoPackage file in root directory
layer_dict = load_all_layers(geopackage_path)

# Read turbine coordinates
turbine_coords = pd.read_csv('output/turbine_coordinates.csv')
turbine_gdf = gpd.GeoDataFrame(
    turbine_coords, 
    geometry=gpd.points_from_xy(turbine_coords.x_coord, turbine_coords.y_coord)
)

print("Available layers:", list(layer_dict.keys()))
''')

# Add a code cell for creating the comprehensive plot
plot_cell = nbf.v4.new_code_cell('''# Create figure with specified size
plt.figure(figsize=(15, 10))

# Plot contour lines with labels
contours = layer_dict.get('contour_lines')
if contours is not None:
    contours.plot(color='gray', linewidth=0.5, alpha=0.7)
    # Add contour labels
    for idx, row in contours.iterrows():
        plt.annotate(
            text=str(int(row['elevation'])),
            xy=(row.geometry.centroid.x, row.geometry.centroid.y),
            fontsize=8,
            color='gray'
        )

# Plot internal roads
roads = layer_dict.get('internal_road_advanced')
if roads is not None:
    roads.plot(color='blue', linewidth=2, label='Internal Roads')

# Plot project boundary
boundary = layer_dict.get('project_boundary')
if boundary is not None:
    boundary.plot(color='brown', linewidth=1.5, linestyle='-', fill=False, label='Project Boundary')

# Plot turbine locations with buffer zones
turbine_buffer = 250  # meters
for _, turbine in turbine_gdf.iterrows():
    circle = turbine.geometry.buffer(turbine_buffer)
    plt.fill(
        *circle.exterior.xy,
        alpha=0.2,
        color='lightgreen'
    )

# Plot turbine points
turbine_gdf.plot(
    color='red',
    marker='x',
    markersize=100,
    label='Turbines',
    ax=plt.gca()
)

# Customize the plot
plt.title('Wind Farm Planning Overview (Advanced Internal Road, Smoothed)')
plt.xlabel('Easting')
plt.ylabel('Northing')
plt.grid(True, linestyle='--', alpha=0.3)
plt.legend()

# Ensure proper aspect ratio
plt.axis('equal')

# Show the plot
plt.show()
''')

# Add cells to notebook
nb.cells = [markdown_cell, imports_cell, load_data_cell, plot_cell]

# Write the notebook to a file
with open('windfarm_layout.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("Created windfarm_layout.ipynb successfully!") 