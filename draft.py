# Imports
import geopandas as gpd
from pyogrio import list_layers
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import os
from shapely.geometry import LineString
import networkx as nx
from shapely.geometry import Point
from scipy.interpolate import splprep, splev
#import fiona
# Path to your GeoPackage file
fpath = 'Dominikanske republikk.gpkg'

# List all layers in the GeoPackage
layers = list_layers(fpath)
print("\nAvailable layers in the GeoPackage:")
for layer in layers:
    print(f"- {layer}")

# Function to read and display layer info
def read_layer(fpath, layer_name):
    """Read a layer from a GeoPackage file."""
    try:
        gdf = gpd.read_file(fpath, layer=layer_name)
        print(f"\nNumber of features: {len(gdf)}")
        print(f"Geometry type: {gdf.geometry.type.unique()}")
        print(f"CRS: {gdf.crs}")
        print(f"Columns: {list(gdf.columns)}")
        return gdf
    except Exception as e:
        print(f"Error reading layer {layer_name}: {str(e)}")
        return None

# Read each layer into a dictionary of GeoDataFrames
# Use the layer name as the key: gdf['output_layer'], gdf['contours'], etc.
gdf = {}
for layer in layers:
    layer_name = layer[0]
    print(f"\nProcessing layer: {layer_name}")
    gdf[layer_name] = read_layer(fpath, layer_name)

# Plot all layers together on one figure, except 'output_layer'
plt.figure(figsize=(15, 10))
ax = plt.gca()

# Plot planning area
if 'planning_area' in gdf and gdf['planning_area'] is not None:
    gdf['planning_area'].plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)

# Plot contours with height labels
if 'contours' in gdf and gdf['contours'] is not None:
    gdf['contours'].plot(ax=ax, cmap='viridis')
    for idx, row in gdf['contours'].iterrows():
        plt.annotate(text=str(int(row['ELEV'])), 
                    xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                    fontsize=8)

# Plot turbine distance (before turbine layout)
if 'Turbine_distance' in gdf and gdf['Turbine_distance'] is not None:
    gdf['Turbine_distance'].plot(ax=ax, color='green', alpha=0.3)

# Plot turbine layout LAST
if 'turbine_layout' in gdf and gdf['turbine_layout'] is not None and 'planning_area' in gdf and gdf['planning_area'] is not None:
    gdf_turbines = gdf['turbine_layout']
    planning_area = gdf['planning_area'].geometry.iloc[0]
    # Find the southernmost turbine (min y)
    start_idx = gdf_turbines.geometry.y.idxmin()
    start_point = gdf_turbines.loc[start_idx].geometry
    # Order turbines by nearest neighbor (greedy)
    remaining = gdf_turbines.drop(index=start_idx).copy()
    ordered_points = [start_point]
    current_point = start_point
    while not remaining.empty:
        distances = remaining.geometry.distance(current_point)
        next_idx = distances.idxmin()
        next_point = remaining.loc[next_idx].geometry
        ordered_points.append(next_point)
        current_point = next_point
        remaining = remaining.drop(index=next_idx)
    # Create grid points inside planning area
    x_min, y_min, x_max, y_max = planning_area.bounds
    grid_spacing = 5  # meters
    x_vals = np.arange(x_min, x_max, grid_spacing)
    y_vals = np.arange(y_min, y_max, grid_spacing)
    grid_points = [Point(x, y) for x in x_vals for y in y_vals if planning_area.contains(Point(x, y))]
    print(f"Grid points generated (inside planning area): {len(grid_points)}")
    # Build graph
    G = nx.Graph()
    point_set = set((p.x, p.y) for p in grid_points)
    for pt in grid_points:
        for dx, dy in [(-grid_spacing,0),(grid_spacing,0),(0,-grid_spacing),(0,grid_spacing)]:
            neighbor = Point(pt.x+dx, pt.y+dy)
            if (neighbor.x, neighbor.y) in point_set:
                G.add_edge((pt.x, pt.y), (neighbor.x, neighbor.y), weight=pt.distance(neighbor))
    # Pathfinding between turbines
    all_path_coords = []
    for i in range(len(ordered_points)-1):
        start = ordered_points[i]
        end = ordered_points[i+1]
        # Snap to nearest grid points
        start_node = min(grid_points, key=lambda p: p.distance(start))
        end_node = min(grid_points, key=lambda p: p.distance(end))
        try:
            path = nx.shortest_path(G, source=(start_node.x, start_node.y), target=(end_node.x, end_node.y), weight='weight')
            all_path_coords.extend(path if i == 0 else path[1:])  # avoid duplicate points
            print(f"Path found between turbine {i} and {i+1}, length: {len(path)}")
        except Exception as e:
            print(f"No path found between turbine {i} and {i+1}: {e}")
    # Create LineString for the internal road
    road_line = LineString(all_path_coords)
    # Moving average smoothing with very aggressive window size
    if len(all_path_coords) > 3:
        window_size = 21  # Very large window size for maximum smoothing
        x, y = zip(*all_path_coords)
        x = np.array(x)
        y = np.array(y)
        
        # Pad the arrays to handle endpoints
        x_pad = np.pad(x, (window_size//2, window_size//2), mode='edge')
        y_pad = np.pad(y, (window_size//2, window_size//2), mode='edge')
        
        # Calculate moving average
        x_smooth = np.convolve(x_pad, np.ones(window_size)/window_size, mode='valid')
        y_smooth = np.convolve(y_pad, np.ones(window_size)/window_size, mode='valid')
        
        smoothed_coords = list(zip(x_smooth, y_smooth))
        road_line = LineString(smoothed_coords)
        print(f"Applied very aggressive moving average smoothing to the internal road (window size: {window_size})")
    else:
        print("Not enough points for smoothing.")
    gdf_road = gpd.GeoDataFrame({'geometry': [road_line]}, crs=gdf_turbines.crs)
    gdf['internal_roads'] = gdf_road
    gdf_turbines.plot(ax=ax, color='red', marker='*', markersize=25)
    gdf['internal_roads'].plot(ax=ax, color='blue', linewidth=5, label='Internal Road (advanced, smoothed)')
    plt.title("Wind Farm Planning Overview (Advanced Internal Road, Smoothed)")
    plt.savefig("plots/turbine_layout_with_advanced_internal_road.png", bbox_inches='tight', dpi=300)
    print("Advanced internal road (smoothed) plotted and saved as 'plots/turbine_layout_with_advanced_internal_road.png'")

# Custom legend
legend_elements = [
    mpatches.Patch(facecolor='none', edgecolor='red', linewidth=2, label='Planning Area'),
    Line2D([0], [0], color='blue', lw=2, label='Contours'),
    mpatches.Patch(facecolor='green', edgecolor='green', alpha=0.3, label='Turbine Distance'),
    Line2D([0], [0], marker='*', color='w', markerfacecolor='red', markersize=25, label='Turbine Layout', linestyle='None'),
    mpatches.Patch(facecolor='brown', edgecolor='brown', linewidth=3, label='Internal Road')
]
plt.legend(handles=legend_elements, loc='best')

# Ensure the 'plots' directory exists
os.makedirs('plots', exist_ok=True)

plt.title("Wind Farm Planning Overview")

plt.savefig("plots/turbine_layout_with_internal_road.png", bbox_inches='tight', dpi=300)
print("Turbine layout with internal road plotted and saved as 'plots/turbine_layout_with_internal_road.png'")

# Now you can access any layer's data using gdf dictionary
# For example: gdf['turbine_layout'] will give you the turbine layout GeoDataFrame

if 'internal_roads' in gdf and gdf['internal_roads'] is not None:
    gdf['internal_roads'].plot(ax=ax, color='blue', linewidth=5, label='Internal Road (offset)')



