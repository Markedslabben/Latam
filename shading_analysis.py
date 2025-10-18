import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shading_loss import calculate_annual_shading_loss

print("Starting shading analysis...")

# Location parameters
latitude = 19.71811
longitude = -71.35603
altitude = 300

print(f"Using location: lat={latitude}, lon={longitude}, alt={altitude}")

# Wind turbine parameters
tower_height = 164  # meters
tower_diameter_base = 6  # meters at base
tower_diameter_top = 3   # meters at top
tower_location = (0, 0)  # Center point

print(f"Tower parameters: height={tower_height}m, base={tower_diameter_base}m, top={tower_diameter_top}m")

# Create arrays for analysis
azimuths = np.arange(0, 361, 30)  # 0° to 360° in 30° steps
distances = np.arange(10, 151, 10)  # 10m to 150m in 10m steps

print(f"Analyzing {len(distances)} distances and {len(azimuths)} azimuth angles...")

# Initialize results array
results_array = np.zeros((len(distances), len(azimuths)))

# Calculate shading losses for each point
for i, distance in enumerate(distances):
    print(f"Processing distance {distance}m...")
    for j, azimuth in enumerate(azimuths):
        # Convert polar coordinates to cartesian
        angle_rad = np.radians(azimuth)
        x = distance * np.sin(angle_rad)
        y = distance * np.cos(angle_rad)
        pv_location = (x, y)
        
        # Calculate annual shading loss
        _, annual_loss = calculate_annual_shading_loss(
            latitude, longitude, altitude,
            tower_height, tower_diameter_base, tower_diameter_top,
            tower_location, pv_location
        )
        
        # Store result as percentage
        results_array[i, j] = annual_loss * 100

print("Calculations complete. Creating visualization...")

# Create DataFrame for saving results
results = pd.DataFrame(results_array, index=distances, columns=azimuths)
results.index.name = 'Distance (m)'
results.columns.name = 'Azimuth (°)'

# Save results to CSV
results.to_csv('shading_analysis_results.csv')
print("Results saved to shading_analysis_results.csv")

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
    results_array[:, -2:],  # Last two columns
    results_array,          # Original data
    results_array[:, :2]    # First two columns
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
ax.set_title('Wind Turbine Shadow Impact (%)\nDistance (m) vs. Direction\n' +
             f'Tower: {tower_height}m height, {tower_diameter_base}m base diameter, {tower_diameter_top}m top diameter',
             pad=20)

# Set the theta limits to show only the main 360 degrees
ax.set_thetamin(0)
ax.set_thetamax(360)

# Adjust radial ticks and grid
ax.set_rticks(np.arange(20, 151, 20))  # Show every 20m
ax.grid(True, alpha=0.3)  # Lighter grid

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

print("\nShading Analysis Results:\n")
print(f"Minimum shading loss: {np.min(results_array):.2f}%")
print(f"Maximum shading loss: {np.max(results_array):.2f}%")

print("\nMean shading loss by azimuth:")
print(results.mean())

print("\nMean shading loss by distance:")
print(results.mean(axis=1))

# Find optimal position
min_loss_idx = np.unravel_index(results_array.argmin(), results_array.shape)
optimal_distance = distances[min_loss_idx[0]]
optimal_azimuth = azimuths[min_loss_idx[1]]
min_loss = results_array[min_loss_idx]

print(f"\nOptimal position:")
print(f"Distance: {optimal_distance}m")
print(f"Azimuth: {optimal_azimuth}°")
print(f"Annual shading loss: {min_loss:.2f}%")

# Save plot
plt.savefig('shading_analysis_plot.png', dpi=300, bbox_inches='tight')
print("Plot saved as shading_analysis_plot.png")
plt.close() 