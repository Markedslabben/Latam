# Draft

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Point
import numpy as np
import matplotlib.pyplot as plt

# Load the planning area shapefile
gdf = gpd.read_file(r'C:\Users\klaus\klauspython\Latam\Inputdata\GISdata\planningarea.shp')

# Get the exterior boundary as a LineString
boundary = gdf.geometry.iloc[0].exterior
coords = list(boundary.coords)

# Find the minimum x value (westernmost)
min_x = min([pt[0] for pt in coords])
tol = 1 # Tolerance for floating point comparison (adjust as needed, e.g., 0.1 for meters)

# Find all segments where both endpoints are close to min_x (i.e., nearly vertical western border)
western_segments = [
    LineString([coords[i], coords[i+1]])
    for i in range(len(coords)-1)
    if abs(coords[i][0] - min_x) < tol and abs(coords[i+1][0] - min_x) < tol
]

if not western_segments:
    raise ValueError("No western border segment found. Try increasing the tolerance or inspect the polygon.")

# Use the longest western segment (in case there are several)
western_border = max(western_segments, key=lambda seg: seg.length)

# Now, place 10 turbines along this line, starting 20m from the southern end
total_length = western_border.length
usable_length = total_length - 20  # 20m offset at the start
n_turbines = 10
n_intervals = n_turbines - 1
spacing = usable_length / n_intervals

print(f"Total western border length: {total_length:.2f} m")
print(f"Usable length (after 20m offset): {usable_length:.2f} m")
print(f"Spacing between turbines: {spacing:.2f} m")

# Generate turbine points
turbine_points = []
for i in range(n_turbines):
    distance_along = 20 + i * spacing
    point = western_border.interpolate(distance_along)
    turbine_points.append(point)

# Create a GeoDataFrame of turbine locations
turbine_gdf = gpd.GeoDataFrame(geometry=turbine_points, crs=gdf.crs)
print(turbine_gdf)

# Plot the planning area
fig, ax = plt.subplots(figsize=(8, 10))
gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=2, label='Planning Area')

# Optionally, plot the boundary as a line
x, y = boundary.xy
ax.plot(x, y, color='blue', linewidth=1, label='Boundary')

# Plot the western border segment
xw, yw = western_border.xy
ax.plot(xw, yw, color='red', linewidth=3, label='Western Border')

# Plot turbine points
turbine_gdf.plot(ax=ax, color='green', marker='o', markersize=60, label='Turbines')

ax.set_title('Planning Area with Western Border and Turbine Locations')
ax.set_xlabel('Easting')
ax.set_ylabel('Northing')
ax.legend()
plt.axis('equal')
plt.show()