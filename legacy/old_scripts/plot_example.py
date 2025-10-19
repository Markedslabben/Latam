"""Example of plotting turbine layout from coordinates."""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from windfarm_layout import plot_layers, create_plot

# Read the turbine coordinates
turbine_df = pd.read_csv('output/turbine_coordinates.csv')

# Convert to GeoDataFrame
geometry = gpd.points_from_xy(turbine_df.x_coord, turbine_df.y_coord)
turbine_gdf = gpd.GeoDataFrame(turbine_df, geometry=geometry, crs="EPSG:32619")

# Create a dictionary of layers (like the one used in draft.py)
layers_dict = {
    'turbine_layout': turbine_gdf
}

# Create a new plot
fig, ax = create_plot()

# Plot the layers
plot_layers(layers_dict, layers_to_plot=['turbine_layout'])

# Save the plot
plt.savefig('turbine_plot.png', dpi=300, bbox_inches='tight')

# Show the plot (this will display it in a window)
plt.show() 