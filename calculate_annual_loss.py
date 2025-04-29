import numpy as np
from shading_loss import calculate_annual_shading_loss
import pandas as pd

# Location parameters
latitude = 19.71811  # degrees
longitude = -71.35603  # degrees
altitude = 300  # meters

# Wind turbine dimensions (example for a 6MW turbine)
tower_height = 120  # meters
tower_diameter = 6  # meters

# Convert 100m east to local coordinates
# PV array is 100m east of turbine
tower_location = (0, 0)  # origin
pv_location = (100, 0)  # 100m east

# Calculate annual shading loss
results, annual_loss = calculate_annual_shading_loss(
    latitude=latitude,
    longitude=longitude,
    altitude=altitude,
    tower_height=tower_height,
    tower_diameter=tower_diameter,
    tower_location=tower_location,
    pv_location=pv_location,
    year=2024  # Current year
)

# Print results
print("\nAnnual Shading Analysis Results:")
print(f"Turbine Location: {latitude:.5f}°N, {longitude:.5f}°W")
print(f"PV Array Location: 100m east of turbine")
print(f"\nTotal Annual Energy Loss: {annual_loss*100:.2f}%")

# Display monthly statistics
monthly_stats = results.groupby(pd.Grouper(freq='M'))['shading_loss'].mean()
print("\nMonthly Average Loss Percentages:")
for idx, loss in monthly_stats.items():
    month_name = idx.strftime('%B')
    print(f"{month_name}: {loss*100:.2f}%") 