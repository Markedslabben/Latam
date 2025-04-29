import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd

print("Starting site-wide shading analysis...")

# Read turbine positions and planning area
gdf_turbines = gpd.read_file('Dominikanske republikk.gpkg', layer='turbine_layout')
gdf_planning = gpd.read_file('Dominikanske republikk.gpkg', layer='planning_area')

print(f"Found {len(gdf_turbines)} turbine positions")

# Read pre-calculated shading results
shading_results = pd.read_csv('shading_analysis_results.csv')

# Extract distances and azimuths
distances = shading_results['Distance (m)'].values
azimuths = np.array([float(col) for col in shading_results.columns[1:]])  # Skip 'Distance (m)' column

# Convert the data into a 2D array (distances x azimuths)
combined_results = shading_results.iloc[:, 1:].values  # Skip 'Distance (m)' column

print("Creating visualization...")

# Create visualization
plt.figure(figsize=(15, 12))

# Create main plot
ax = plt.subplot(111)

# Plot planning area
gdf_planning.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2, label='Planning Area')

# Plot turbine positions
gdf_turbines.plot(ax=ax, color='red', marker='*', markersize=200, label='Turbines')

# Define specific contour levels
contour_levels = np.array([0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])

# Plot contours around each turbine
for idx, turbine in gdf_turbines.iterrows():
    # Create meshgrid centered on this turbine
    x_grid = np.linspace(turbine.geometry.x - 150, turbine.geometry.x + 150, 100)
    y_grid = np.linspace(turbine.geometry.y - 150, turbine.geometry.y + 150, 100)
    X, Y = np.meshgrid(x_grid, y_grid)
    
    # Calculate distances and angles from turbine
    dx = X - turbine.geometry.x
    dy = Y - turbine.geometry.y
    R = np.sqrt(dx**2 + dy**2)
    theta = np.arctan2(dx, dy)
    
    # Interpolate shading values
    Z = np.zeros_like(X)
    for i in range(len(x_grid)):
        for j in range(len(y_grid)):
            if R[j,i] <= max(distances):
                # Find nearest distance and angle in our calculated results
                d_idx = np.argmin(np.abs(distances - R[j,i]))
                a_idx = np.argmin(np.abs(azimuths - np.degrees(theta[j,i])))
                Z[j,i] = combined_results[d_idx, a_idx]
    
    # Create filled contours
    contour = ax.contour(X, Y, Z, levels=contour_levels, 
                        colors='black', alpha=0.5, linewidths=1)
    ax.clabel(contour, contour.levels, fmt='%.1f%%', fontsize=8, 
              inline=True, inline_spacing=10)

# Customize plot
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
ax.set_title('Site-Wide Wind Turbine Shadow Impact (%)', pad=20)

# Add legend
ax.legend()

# Save the plot
plt.savefig('site_shading_analysis.png', bbox_inches='tight', dpi=300)
print("Analysis complete. Results saved to 'site_shading_analysis.png'") 