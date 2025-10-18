import sys
print("Python path:")
for path in sys.path:
    print(f"  {path}")
print("\nTrying to import numpy...")
try:
    import numpy
    print(f"Numpy imported successfully from: {numpy.__file__}")
except ImportError as e:
    print(f"Import error: {str(e)}")
    raise

import os
import time
import psutil
import geopandas as gpd
import matplotlib.pyplot as plt
from datetime import datetime

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)

def list_gpkg_layers(gpkg_path):
    try:
        log(f"Python version: {sys.version}")
        log(f"Current working directory: {os.getcwd()}")
        log(f"Memory usage before opening geopackage: {get_memory_usage():.2f} MB")
        log(f"Attempting to list layers in: {gpkg_path}")
        
        if not os.path.exists(gpkg_path):
            log(f"Error: GeoPackage file not found at {gpkg_path}")
            return None
        
        layers = gpd.read_file(gpkg_path, layer='layer_list')
        log(f"Available layers: {', '.join(layers['layer_name'].tolist())}")
        log(f"Memory usage after listing layers: {get_memory_usage():.2f} MB")
        return layers['layer_name'].tolist()
    except Exception as e:
        log(f"Error listing layers: {str(e)}")
        return None

def analyze_layer(gdf, layer_name):
    try:
        log(f"\nAnalyzing layer: {layer_name}")
        log(f"Memory usage before analysis: {get_memory_usage():.2f} MB")
        log(f"Number of features: {len(gdf)}")
        log(f"Geometry types: {gdf.geometry.type.unique()}")
        bounds = gdf.total_bounds
        log(f"Geographic bounds: {bounds}")
        log(f"Memory usage after analysis: {get_memory_usage():.2f} MB")
    except Exception as e:
        log(f"Error analyzing layer {layer_name}: {str(e)}")

def load_and_plot_layers(gpkg_path):
    try:
        log("Starting layer loading and plotting process")
        start_time = time.time()
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(15, 10))
        
        # Define layers to plot and their styles
        layers_to_plot = [
            {'name': 'wind_turbines', 'color': 'red', 'alpha': 0.6},
            {'name': 'solar_panels', 'color': 'orange', 'alpha': 0.6},
            {'name': 'power_lines', 'color': 'blue', 'alpha': 0.4},
            {'name': 'substations', 'color': 'green', 'alpha': 0.6}
        ]
        
        # Plot each layer
        for layer_config in layers_to_plot:
            layer_name = layer_config['name']
            try:
                log(f"\nProcessing layer: {layer_name}")
                log(f"Memory usage before loading layer: {get_memory_usage():.2f} MB")
                
                # Load the layer
                gdf = gpd.read_file(gpkg_path, layer=layer_name)
                log(f"Layer loaded successfully: {layer_name}")
                
                # Analyze the layer
                analyze_layer(gdf, layer_name)
                
                # Plot the layer
                gdf.plot(
                    ax=ax,
                    color=layer_config['color'],
                    alpha=layer_config['alpha'],
                    label=layer_name
                )
                
                log(f"Layer plotted successfully: {layer_name}")
                log(f"Memory usage after plotting layer: {get_memory_usage():.2f} MB")
                
            except Exception as e:
                log(f"Error processing layer {layer_name}: {str(e)}")
                continue
        
        # Customize the plot
        ax.set_title('Energy Infrastructure Visualization')
        ax.legend()
        ax.grid(True)
        
        # Save the plot
        plt.savefig('gis_layers_visualization.png')
        log("Plot saved successfully")
        
        # Calculate and log total execution time
        execution_time = time.time() - start_time
        log(f"\nTotal execution time: {execution_time:.2f} seconds")
        log(f"Final memory usage: {get_memory_usage():.2f} MB")
        
        print("Plot saved as 'gis_layers_visualization.png'")
        
    except Exception as e:
        log(f"Error in load_and_plot_layers: {str(e)}")

def main():
    log("Starting GIS visualization script")
    gpkg_path = 'data/energy_infrastructure.gpkg'
    
    # List available layers
    available_layers = list_gpkg_layers(gpkg_path)
    if available_layers is None:
        log("Failed to list layers. Exiting.")
        return
    
    # Load and plot layers
    load_and_plot_layers(gpkg_path)
    log("Script execution completed")

if __name__ == "__main__":
    main()