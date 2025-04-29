"""GIS-based wind farm planning and analysis module.

This module provides functionality for processing and analyzing GIS data for wind farm planning,
including reading GeoPackage layers, creating internal road networks, and visualizing the layout.
Key features include:
- Reading and organizing GIS layers from GeoPackage files
- Creating optimized internal road networks between turbines
- Plotting and visualizing wind farm components
- Exporting processed data to various formats
"""

# Standard library imports
import os

# Third-party imports
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import networkx as nx
import numpy as np
from pyogrio import list_layers
from shapely.geometry import LineString, Point
import pandas as pd

# Constants
GEOPACKAGE_PATH = 'Dominikanske republikk.gpkg'

# ============================================================================
# 1. INPUT DATA READING
# ============================================================================

def read_gis_layer(geopackage_path: str, layer_name: str) -> gpd.GeoDataFrame:
    """Read a single layer from a GeoPackage file.

    Args:
        geopackage_path (str): Path to the GeoPackage file
        layer_name (str): Name of the layer to read

    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing the layer data

    Raises:
        ValueError: If layer cannot be read
    """
    try:
        gdf = gpd.read_file(geopackage_path, layer=layer_name)
        print(f"\nLayer: {layer_name}")
        print(f"Number of features: {len(gdf)}")
        if 'geometry' in gdf.columns:
            print(f"Geometry type: {gdf.geometry.type.unique()}")
            print(f"CRS: {gdf.crs}")
        else:
            print("Non-spatial table (no geometry column)")
        print(f"Columns: {list(gdf.columns)}")
        return gdf
    except (IOError, ValueError) as e:
        print(f"Error reading layer {layer_name}: {str(e)}")
        return None

def load_all_layers(geopackage_path: str) -> dict:
    """Load all layers from a GeoPackage file into a dictionary.

    Args:
        geopackage_path (str): Path to the GeoPackage file

    Returns:
        dict: Dictionary of layer names to GeoDataFrames
    """
    # Define layers to skip
    skip_layers = ['qgis_projects']
    
    layers = list_layers(geopackage_path)
    print("\nAvailable layers in the GeoPackage:")
    for layer in layers:
        print(f"- {layer}")

    layer_dict = {}
    for layer in layers:
        layer_name = layer[0]
        if layer_name in skip_layers:
            print(f"\nSkipping layer: {layer_name} (known issues)")
            continue
            
        print(f"\nProcessing layer: {layer_name}")
        layer_dict[layer_name] = read_gis_layer(geopackage_path, layer_name)

    return layer_dict

# ============================================================================
# 2. DATA ORGANIZATION
# ============================================================================

def create_internal_roads(gdf_turbines: gpd.GeoDataFrame, planning_area: gpd.GeoDataFrame,
                        grid_spacing: float = 5) -> gpd.GeoDataFrame:
    """Create internal roads connecting turbines using a grid-based pathfinding approach.

    Args:
        gdf_turbines (gpd.GeoDataFrame): GeoDataFrame containing turbine locations
        planning_area (gpd.GeoDataFrame): GeoDataFrame containing planning area
        grid_spacing (float): Spacing between grid points in meters

    Returns:
        gpd.GeoDataFrame: GeoDataFrame containing the internal roads
    """
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
    planning_geom = planning_area.geometry.iloc[0]
    x_min, y_min, x_max, y_max = planning_geom.bounds
    x_vals = np.arange(x_min, x_max, grid_spacing)
    y_vals = np.arange(y_min, y_max, grid_spacing)
    grid_points = [Point(x, y) for x in x_vals for y in y_vals
                  if planning_geom.contains(Point(x, y))]
    print(f"Grid points generated (inside planning area): {len(grid_points)}")

    # Build graph
    graph = nx.Graph()
    point_set = set((p.x, p.y) for p in grid_points)
    for pt in grid_points:
        for dx, dy in [(-grid_spacing,0), (grid_spacing,0), (0,-grid_spacing), (0,grid_spacing)]:
            neighbor = Point(pt.x+dx, pt.y+dy)
            if (neighbor.x, neighbor.y) in point_set:
                graph.add_edge((pt.x, pt.y), (neighbor.x, neighbor.y),
                             weight=pt.distance(neighbor))

    # Pathfinding between turbines
    all_path_coords = []
    for i in range(len(ordered_points)-1):
        start_point = ordered_points[i]
        end_point = ordered_points[i+1]
        start_node = min(grid_points, key=lambda p: p.distance(start_point))
        end_node = min(grid_points, key=lambda p: p.distance(end_point))
        try:
            path = nx.shortest_path(graph, source=(start_node.x, start_node.y),
                                  target=(end_node.x, end_node.y), weight='weight')
            all_path_coords.extend(path if i == 0 else path[1:])
            print(f"Path found between turbine {i} and {i+1}, length: {len(path)}")
        except nx.NetworkXNoPath as e:
            print(f"No path found between turbine {i} and {i+1}: {e}")

    # Smooth the road path
    road_line = smooth_road_path(all_path_coords)

    return gpd.GeoDataFrame({'geometry': [road_line]}, crs=gdf_turbines.crs)

def smooth_road_path(coords: list, window_size: int = 21) -> LineString:
    """Smooth a road path using moving average.

    Args:
        coords (list): List of coordinate tuples
        window_size (int): Size of the moving average window

    Returns:
        LineString: Smoothed road path
    """
    if len(coords) <= 3:
        print("Not enough points for smoothing.")
        return LineString(coords)

    x, y = zip(*coords)
    x = np.array(x)
    y = np.array(y)

    # Pad arrays
    x_pad = np.pad(x, (window_size//2, window_size//2), mode='edge')
    y_pad = np.pad(y, (window_size//2, window_size//2), mode='edge')

    # Calculate moving average
    x_smooth = np.convolve(x_pad, np.ones(window_size)/window_size, mode='valid')
    y_smooth = np.convolve(y_pad, np.ones(window_size)/window_size, mode='valid')

    smoothed_coords = list(zip(x_smooth, y_smooth))
    return LineString(smoothed_coords)

# ============================================================================
# 3. PLOTTING FUNCTIONS
# ============================================================================

def create_plot(figsize: tuple = (15, 10)) -> tuple:
    """Create a new matplotlib figure and axes.

    Args:
        figsize (tuple): Figure size in inches

    Returns:
        tuple: (figure, axes) tuple
    """
    fig = plt.figure(figsize=figsize)
    ax = plt.gca()
    return fig, ax

def plot_layers(layer_dict: dict, layers_to_plot: list = None, ax: plt.Axes = None,
                save_path: str = None) -> plt.Axes:
    """Plot selected layers from the GeoDataFrame dictionary.

    Args:
        layer_dict (dict): Dictionary of layer names to GeoDataFrames
        layers_to_plot (list): List of layer names to plot. If None, plot all layers
        ax (plt.Axes): Matplotlib axes to plot on. If None, create new axes
        save_path (str): Path to save the plot. If None, don't save

    Returns:
        plt.Axes: The matplotlib axes object with the plot
    """
    if ax is None:
        _, ax = create_plot()

    if layers_to_plot is None:
        layers_to_plot = list(layer_dict.keys())

    legend_elements = []

    # Plot each layer with specific styling
    for layer in layers_to_plot:
        if layer not in layer_dict or layer_dict[layer] is None:
            continue

        if layer == 'planning_area':
            layer_dict[layer].plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
            legend_elements.append(mpatches.Patch(facecolor='none', edgecolor='red',
                                                linewidth=2, label='Planning Area'))

        elif layer == 'contours':
            layer_dict[layer].plot(ax=ax, cmap='viridis')
            for _, row in layer_dict[layer].iterrows():
                plt.annotate(text=str(int(row['ELEV'])),
                           xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                           fontsize=8)
            legend_elements.append(Line2D([0], [0], color='blue', lw=2, label='Contours'))

        elif layer == 'Turbine_distance':
            layer_dict[layer].plot(ax=ax, color='green', alpha=0.3)
            legend_elements.append(mpatches.Patch(facecolor='green', edgecolor='green',
                                                alpha=0.3, label='Turbine Distance'))

        elif layer == 'turbine_layout':
            layer_dict[layer].plot(ax=ax, color='red', marker='*', markersize=25)
            legend_elements.append(Line2D([0], [0], marker='*', color='w',
                                        markerfacecolor='red', markersize=25,
                                        label='Turbine Layout', linestyle='None'))

        elif layer == 'internal_roads':
            layer_dict[layer].plot(ax=ax, color='blue', linewidth=5)
            legend_elements.append(mpatches.Patch(facecolor='brown', edgecolor='brown',
                                                linewidth=3, label='Internal Road'))

    # Add legend and title
    plt.legend(handles=legend_elements, loc='best')
    plt.title("Wind Farm Planning Overview")

    # Save plot if path provided
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        print(f"Plot saved as '{save_path}'")

    return ax

# ============================================================================
# 4. DATA EXPORT FUNCTIONS
# ============================================================================

def export_layer_to_file(gdf: gpd.GeoDataFrame, output_path: str,
                        driver: str = 'GPKG') -> None:
    """Export a GeoDataFrame to a file.

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame to export
        output_path (str): Path to save the file
        driver (str): Output format driver (e.g., 'GPKG', 'ESRI Shapefile')
    """
    try:
        gdf.to_file(output_path, driver=driver)
        print(f"Successfully exported to {output_path}")
    except (IOError, ValueError) as e:
        print(f"Error exporting to {output_path}: {str(e)}")

def get_layer_data(layer_dict: dict, layer_name: str) -> gpd.GeoDataFrame:
    """Retrieve a specific layer from the GeoDataFrame dictionary.

    Args:
        layer_dict (dict): Dictionary of layer names to GeoDataFrames
        layer_name (str): Name of the layer to retrieve

    Returns:
        gpd.GeoDataFrame: The requested layer's GeoDataFrame
    """
    if layer_name in layer_dict:
        return layer_dict[layer_name]

    print(f"Layer '{layer_name}' not found in the data dictionary")
    return None

def export_turbine_coordinates(gdf: gpd.GeoDataFrame, output_path: str) -> None:
    """Export turbine coordinates to a CSV file.

    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing turbine point geometries
        output_path (str): Path to save the CSV file
    """
    try:
        # Extract x, y coordinates from point geometries
        coords_df = pd.DataFrame({
            'turbine_id': range(1, len(gdf) + 1),
            'x_coord': gdf.geometry.x,
            'y_coord': gdf.geometry.y
        })
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to CSV
        coords_df.to_csv(output_path, index=False)
        print(f"Successfully exported turbine coordinates to {output_path}")
    except Exception as e:
        print(f"Error exporting turbine coordinates: {str(e)}")

# ============================================================================
# MAIN EXECUTION (if run as script)
# ============================================================================

if __name__ == "__main__":
    # Example usage
    # 1. Load all layers
    layer_dict = load_all_layers(GEOPACKAGE_PATH)

    # 2. Create internal roads if needed
    if all(layer in layer_dict for layer in ['turbine_layout', 'planning_area']):
        layer_dict['internal_roads'] = create_internal_roads(
            layer_dict['turbine_layout'],
            layer_dict['planning_area']
        )

    # 3. Create and save plot
    plot_layers(layer_dict, save_path="plots/wind_farm_overview.png")

    # 4. Export turbine coordinates
    if 'turbine_layout' in layer_dict:
        export_turbine_coordinates(
            layer_dict['turbine_layout'],
            'output/turbine_coordinates.csv'
        )

    # 5. Example of data export
    if 'internal_roads' in layer_dict:
        export_layer_to_file(
            layer_dict['internal_roads'],
            'output/internal_roads.gpkg'
        )



