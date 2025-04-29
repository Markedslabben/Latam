# Wind Turbine Tower Shading Calculator

This package provides functions to calculate the shading loss from wind turbine towers on solar PV arrays. It uses the pvlib library for solar position and clear sky irradiance calculations.

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Here's a basic example of how to use the shading loss calculator:

```python
import pandas as pd
from shading_loss import calculate_tower_shadow, calculate_annual_shading_loss

# Example parameters
latitude = 40.0  # degrees
longitude = -80.0  # degrees
altitude = 100  # meters
tower_height = 80  # meters
tower_diameter = 4  # meters
tower_location = (0, 0)  # (x, y) coordinates in meters
pv_location = (20, 30)  # (x, y) coordinates in meters

# Calculate shading for a specific time period
times = pd.date_range('2024-01-01', '2024-01-02', freq='1H', tz='UTC')
results = calculate_tower_shadow(
    latitude, longitude, altitude, times,
    tower_height, tower_diameter,
    tower_location, pv_location
)

# Calculate annual shading loss
annual_results, annual_loss = calculate_annual_shading_loss(
    latitude, longitude, altitude,
    tower_height, tower_diameter,
    tower_location, pv_location,
    year=2024
)

print(f"Annual energy loss fraction: {annual_loss:.2%}")
```

## Functions

### calculate_tower_shadow()

Calculates the shading loss from a wind turbine tower on a PV array for specific times.

Returns a DataFrame containing:
- shadow_length: Length of tower shadow in meters
- shadow_width: Width of tower shadow in meters
- is_shaded: Boolean indicating if PV point is shaded
- shading_loss: Fraction of irradiance lost due to shading (0-1)
- ghi: Global horizontal irradiance (W/m²)
- dni: Direct normal irradiance (W/m²)
- dhi: Diffuse horizontal irradiance (W/m²)

### calculate_annual_shading_loss()

Calculates annual shading losses from a wind turbine tower.

Returns:
1. DataFrame containing hourly shading results for the year
2. Annual energy loss fraction due to shading

## Notes

- The calculations assume a cylindrical tower and clear sky conditions
- The shading model assumes complete blocking of direct radiation when shaded
- Diffuse radiation is not affected by shading in this model
- Coordinates are in a local coordinate system with arbitrary origin
- Time series should be in UTC to match pvlib's solar position calculations
