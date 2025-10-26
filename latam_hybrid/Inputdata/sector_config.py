"""
Sector Management Configuration for Latam Hybrid Wind Farm Project

This file contains the sector management rules for turbines with noise restrictions.
Turbines 1, 3, 5, 7, 9, and 12 are restricted to specific wind direction sectors.

Configuration:
- Allowed sectors: 60-120° and 240-300°
- Turbines run ONLY when wind direction is within these sectors
- All other wind directions → turbines are stopped (zero production, no wakes)
"""

from latam_hybrid.core import SectorManagementConfig

# Project sector management configuration
# Turbines 1, 3, 5, 7, 9, 12 with noise restrictions
SECTOR_MANAGEMENT_CONFIG = SectorManagementConfig(
    turbine_sectors={
        1: [(60, 120), (240, 300)],   # Turbine 1: NE and SW sectors allowed
        3: [(60, 120), (240, 300)],   # Turbine 3: NE and SW sectors allowed
        5: [(60, 120), (240, 300)],   # Turbine 5: NE and SW sectors allowed
        7: [(60, 120), (240, 300)],   # Turbine 7: NE and SW sectors allowed
        9: [(60, 120), (240, 300)],   # Turbine 9: NE and SW sectors allowed
        12: [(60, 120), (240, 300)]   # Turbine 12: NE and SW sectors allowed
        # Turbines 2, 4, 6, 8, 10, 11, 13 have NO restrictions
    },
    metadata={
        'reason': 'Noise restrictions from nearby residents',
        'project': 'Latam Hybrid Wind Farm',
        'allowed_sectors_deg': '60-120, 240-300',
        'restricted_turbines': [1, 3, 5, 7, 9, 12]
    }
)


# Alternative: No sector management (for comparison)
NO_SECTOR_MANAGEMENT = None


# Usage example:
"""
from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG
from latam_hybrid.wind import WindSite

result = (
    WindSite.from_wind_data(wind_data)
    .with_turbine(turbine)
    .set_layout(layout)
    .set_sector_management(SECTOR_MANAGEMENT_CONFIG)  # Use project config
    .run_simulation(wake_model='NOJ')
    .apply_losses()
    .calculate_production()
)

print(f"Sector losses: {result.sector_loss_percent:.2f}%")
"""
