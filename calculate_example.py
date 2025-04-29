import pandas as pd
from shading_loss import calculate_tower_shadow, calculate_annual_shading_loss

# Location parameters
latitude = 19.71811  # degrees
longitude = -71.35603  # degrees (corrected from -135603)
altitude = 300  # meters

# Tower parameters
tower_height = 80  # meters (typical height for a 6MW turbine)
tower_diameter = 4  # meters (typical diameter)

# Tower base location in local coordinates
tower_location = (0, 0)  # origin of local coordinate system

# PV location - 100m east of tower
pv_location = (100, 0)  # 100m east in local coordinates

# Calculate shading for current day
today = pd.Timestamp.now().date()
times = pd.date_range(today, today + pd.Timedelta(days=1), 
                     freq='1H', tz='UTC', inclusive='left')

print("Calculating shading for current 24-hour period...")
daily_results = calculate_tower_shadow(
    latitude, longitude, altitude, times,
    tower_height, tower_diameter,
    tower_location, pv_location
)

# Print summary of current day
shaded_hours = daily_results['is_shaded'].sum()
max_loss = daily_results['shading_loss'].max() * 100
avg_loss = daily_results['shading_loss'].mean() * 100

print(f"\nDaily Analysis Results:")
print(f"Hours with shading: {shaded_hours:.1f}")
print(f"Maximum shading loss: {max_loss:.1f}%")
print(f"Average shading loss: {avg_loss:.1f}%")

# Calculate annual shading loss
print("\nCalculating annual shading loss...")
annual_results, annual_loss = calculate_annual_shading_loss(
    latitude, longitude, altitude,
    tower_height, tower_diameter,
    tower_location, pv_location,
    year=2024
)

print(f"\nAnnual Analysis Results:")
print(f"Annual energy loss fraction: {annual_loss:.2%}")

# Analyze seasonal variations
seasonal_losses = []
for month in range(1, 13):
    mask = annual_results.index.month == month
    monthly_loss = (annual_results.loc[mask, 'ghi'] * 
                   annual_results.loc[mask, 'shading_loss']).sum() / \
                  annual_results.loc[mask, 'ghi'].sum()
    seasonal_losses.append(monthly_loss)

print("\nMonthly Shading Loss Variations:")
for month, loss in enumerate(seasonal_losses, 1):
    print(f"Month {month}: {loss:.2%}") 