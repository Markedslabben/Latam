import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file
results = pd.read_csv('shading_analysis_results.csv', index_col=0)

# Convert index to numeric for distances
distances = results.index.astype(float)
azimuths = np.array([float(col) for col in results.columns])

# Create visualization
plt.figure(figsize=(12, 10))

# Create polar plot
ax = plt.subplot(111, projection='polar')

# Extend the data with padding on both sides to handle periodic boundary
pad_degrees = 30  # Add 30 degrees padding on each side
extended_azimuths = np.concatenate([
    azimuths[-2:] - 360,  # Add last two points before 0°
    azimuths,             # Original data
    azimuths[:2] + 360    # Add first two points after 360°
])
extended_results = np.column_stack([
    results.values[:, -2:],  # Last two columns
    results.values,          # Original data
    results.values[:, :2]    # First two columns
])

# Create meshgrid for plotting
T, R = np.meshgrid(np.radians(extended_azimuths), distances)

# Define specific contour levels
contour_levels = np.array([0, 0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])

# Create filled contours
pcm = ax.contourf(T, R, extended_results, levels=contour_levels, cmap='RdYlBu_r', extend='max')

# Add contour lines with labels
contour_lines = ax.contour(T, R, extended_results, levels=contour_levels, 
                          colors='black', alpha=0.7, linewidths=1.5)
ax.clabel(contour_lines, contour_lines.levels, fmt='%.1f%%', fontsize=9, 
          inline=True, inline_spacing=10)

# Customize plot
ax.set_theta_zero_location('N')  # 0 degrees at North
ax.set_theta_direction(-1)  # Clockwise
ax.set_rlabel_position(0)  # Move radial labels to 0 degrees
ax.set_title('Wind Turbine Shadow Impact (%)\nDistance (m) vs. Direction', pad=20)

# Set the theta limits to show only the main 360 degrees
ax.set_thetamin(0)
ax.set_thetamax(360)

# Adjust radial ticks and grid
ax.set_rticks(np.arange(20, 151, 20))  # Show every 20m
ax.grid(True, alpha=0.3)

# Add compass directions
directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
angles = np.arange(0, 2*np.pi, np.pi/4)
for direction, angle in zip(directions, angles):
    ax.text(angle, ax.get_rmax()*1.1, direction, 
            ha='center', va='center', fontsize=10)

# Add colorbar with adjusted position
cbar = plt.colorbar(pcm, pad=0.1)
cbar.set_label('Annual Shading Loss (%)', fontsize=10)
cbar.ax.tick_params(labelsize=9)

# Print analysis results
print("\nShading Analysis Results:\n")
print(f"Minimum shading loss: {np.min(results.values):.2f}%")
print(f"Maximum shading loss: {np.max(results.values):.2f}%")

print("\nMean shading loss by azimuth:")
print(results.mean())

print("\nMean shading loss by distance:")
print(results.mean(axis=1))

# Find optimal position
min_loss_idx = np.unravel_index(results.values.argmin(), results.values.shape)
optimal_distance = distances[min_loss_idx[0]]
optimal_azimuth = azimuths[min_loss_idx[1]]
min_loss = results.values[min_loss_idx]

print(f"\nOptimal position:")
print(f"Distance: {optimal_distance}m")
print(f"Azimuth: {optimal_azimuth}°")
print(f"Annual shading loss: {min_loss:.2f}%")

# Save plot
plt.savefig('shading_analysis_plot_contours.png', dpi=300, bbox_inches='tight')
print("Plot saved as shading_analysis_plot_contours.png")
plt.close() 