"""
Fix wind rose to include polar coordinates (radial axis) and angle labels.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
wind_file = os.path.join(base_dir, 'latam_hybrid', 'Inputdata', 'vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt')
figures_dir = os.path.join(os.path.dirname(__file__), '..', 'figures')
os.makedirs(figures_dir, exist_ok=True)
df = pd.read_csv(wind_file, sep=r'\s+', skiprows=4, usecols=[0, 1, 2, 3],
                 names=['Date', 'Time', 'WS', 'WD'])

# Calculate wind rose
wd_bins = np.arange(0, 361, 10)  # 10-degree bins
wd_labels = (wd_bins[:-1] + wd_bins[1:]) / 2
ws_bins = [0, 4, 8, 12, 16, 20, 30]
ws_labels = ['0-4 m/s', '4-8 m/s', '8-12 m/s', '12-16 m/s', '16-20 m/s', '>20 m/s']

# Digitize wind direction and speed
wd_digitized = np.digitize(df['WD'], wd_bins) - 1
ws_digitized = np.digitize(df['WS'], ws_bins) - 1

# Count occurrences
wind_rose = np.zeros((len(wd_labels), len(ws_labels)))
for i, j in zip(wd_digitized, ws_digitized):
    if 0 <= i < len(wd_labels) and 0 <= j < len(ws_labels):
        wind_rose[i, j] += 1

# Convert to percentage
wind_rose_pct = (wind_rose / len(df)) * 100

# Create polar plot with proper axes
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='polar')

# Set theta direction (clockwise from north)
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)

# Convert degrees to radians
theta = np.deg2rad(wd_labels)
theta = np.append(theta, theta[0])  # Close the circle

# Colors for different wind speed bins
colors = ['#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c', '#08306b']

# Plot stacked bars
width = np.deg2rad(10)  # Bar width
bottom = np.zeros(len(theta))

for i, (ws_label, color) in enumerate(zip(ws_labels, colors)):
    values = np.append(wind_rose_pct[:, i], wind_rose_pct[0, i])  # Close the circle
    bars = ax.bar(theta, values, width=width, bottom=bottom, color=color,
                  alpha=0.8, label=ws_label, edgecolor='black', linewidth=0.5)
    bottom += values

# Customize radial axis (percentage)
ax.set_rlabel_position(90)
ax.set_yticks([2, 4, 6, 8, 10])
ax.set_yticklabels(['2%', '4%', '6%', '8%', '10%'], fontsize=10)
ax.set_ylim(0, max(wind_rose_pct.sum(axis=1)) * 1.1)

# Customize angular axis (degrees)
angle_labels = ['N\n0°', 'NE\n45°', 'E\n90°', 'SE\n135°', 'S\n180°', 'SW\n225°', 'W\n270°', 'NW\n315°']
ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
ax.set_xticklabels(angle_labels, fontsize=11)

# Add legend
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=10, title='Wind Speed')

# Add title
ax.set_title('Wind Rose - Directional Distribution\n11-Year Average (164m hub height)',
             fontsize=14, fontweight='bold', pad=20)

# Add grid
ax.grid(True, linestyle='--', alpha=0.5)

# Add prohibited sector shading
# Sector 1: 60-120 degrees
theta_sector1 = np.linspace(np.deg2rad(60), np.deg2rad(120), 100)
r_max = ax.get_ylim()[1]
ax.fill_between(theta_sector1, 0, r_max, color='red', alpha=0.15, label='Prohibited Sectors')

# Sector 2: 240-300 degrees
theta_sector2 = np.linspace(np.deg2rad(240), np.deg2rad(300), 100)
ax.fill_between(theta_sector2, 0, r_max, color='red', alpha=0.15)

# Add sector boundary lines
ax.plot([np.deg2rad(60), np.deg2rad(60)], [0, r_max], 'r--', linewidth=2, alpha=0.7)
ax.plot([np.deg2rad(120), np.deg2rad(120)], [0, r_max], 'r--', linewidth=2, alpha=0.7)
ax.plot([np.deg2rad(240), np.deg2rad(240)], [0, r_max], 'r--', linewidth=2, alpha=0.7)
ax.plot([np.deg2rad(300), np.deg2rad(300)], [0, r_max], 'r--', linewidth=2, alpha=0.7)

plt.tight_layout()
output_path = os.path.join(figures_dir, 'validation_wind_rose.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Created: {output_path}")
plt.close()
