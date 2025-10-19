import geopandas as gpd
import matplotlib.pyplot as plt
import psutil
import os
import sys
import time
from datetime import datetime

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB

def log(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)

def analyze_layer(gdf, layer_name):
    try:
        log(f"\nAnalyzing layer: {layer_name}")
        log(f"Memory usage before analysis: {get_memory_usage():.2f} MB")
        log(f"Number of features: {len(gdf)}")
        log(f"Geometry types: {gdf.geometry.type.unique()}")
        log(f"CRS: {gdf.crs}")
        bounds = gdf.total_bounds
        log(f"Geographic bounds: {bounds}")
        log(f"Memory usage after analysis: {get_memory_usage():.2f} MB")
    except Exception as e:
        log(f"Error analyzing layer {layer_name}: {str(e)}")

def load_and_plot_layers(gpkg_path):
    try:
        log("Starting layer loading and plotting process")
        start_time = time.time()
        
        # Load output_layer
        log("\nProcessing output_layer")
        output_layer = gpd.read_file(gpkg_path, layer='output_layer')
        log("Original output_layer CRS:")
        analyze_layer(output_layer, 'output_layer')
        
        # Force conversion to EPSG:32619
        output_layer = output_layer.to_crs('EPSG:32619')
        log("After conversion to EPSG:32619:")
        analyze_layer(output_layer, 'output_layer')
        
        # Create interactive plot
        base = output_layer.explore(
            m=None,  # Create new map
            color='lightgreen',
            style_kwds={'fillOpacity': 0.3, 'weight': 2, 'color': 'darkgreen'},
            tooltip=False,
            name='Planning Area'
        )
        
        # Save the interactive plot
        base.save('gis_layers_visualization.html')
        log("Interactive plot saved successfully")
        
        # Create static plot
        fig, ax = plt.subplots(figsize=(15, 10))
        
        # Plot planning area
        output_layer.plot(
            ax=ax,
            color='lightgreen',
            alpha=0.3,
            edgecolor='darkgreen',
            linewidth=2,
            label='Planning Area'
        )
        
        # Set plot limits with buffer
        bounds = output_layer.total_bounds
        buffer = 100  # 100 meters buffer
        ax.set_xlim([bounds[0] - buffer, bounds[2] + buffer])
        ax.set_ylim([bounds[1] - buffer, bounds[3] + buffer])
        
        # Customize the plot
        ax.set_title('Project Planning Area (UTM Zone 19N)')
        ax.legend()
        ax.grid(True)
        
        # Add coordinate system info and scale
        ax.text(0.02, 0.04, 'Coordinate System: UTM Zone 19N (EPSG:32619)', transform=ax.transAxes, fontsize=8)
        ax.text(0.02, 0.02, f'Scale: Buffer = {buffer}m', transform=ax.transAxes, fontsize=8)
        
        # Save the static plot
        plt.savefig('gis_layers_visualization.png', dpi=300, bbox_inches='tight')
        log("Static plot saved successfully")
        
        # Calculate and log total execution time
        execution_time = time.time() - start_time
        log(f"\nTotal execution time: {execution_time:.2f} seconds")
        log(f"Final memory usage: {get_memory_usage():.2f} MB")
        
        print("Plots saved as:")
        print("1. gis_layers_visualization.html (interactive)")
        print("2. gis_layers_visualization.png (static)")
        
    except Exception as e:
        log(f"Error in load_and_plot_layers: {str(e)}")
        raise e

def main():
    log("Starting GIS visualization script")
    gpkg_path = 'Dominikanske republikk.gpkg'
    
    # Load and plot layers
    load_and_plot_layers(gpkg_path)
    log("Script execution completed")

if __name__ == "__main__":
    main()