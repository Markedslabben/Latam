"""
Diagnostic script to analyze sector management losses per turbine.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from latam_hybrid.wind import WindSite
from latam_hybrid.wind.turbine import TurbineModel
from latam_hybrid.wind.layout import TurbineLayout
from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG
from latam_hybrid.core.data_models import WindData

def main():
    """Diagnose sector management losses."""

    print("=" * 70)
    print("SECTOR MANAGEMENT LOSS DIAGNOSIS")
    print("=" * 70)
    print()

    # Configuration
    ANALYSIS_YEAR = 2020

    # File paths
    project_root = Path(__file__).parent.parent
    wind_data_path = project_root / "latam_hybrid" / "Inputdata" / "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    turbine_path = project_root / "latam_hybrid" / "Inputdata" / "Nordex N164.csv"
    layout_path = project_root / "latam_hybrid" / "Inputdata" / "Turbine_layout_13.csv"
    losses_path = project_root / "latam_hybrid" / "Inputdata" / "losses.csv"

    # Load and filter wind data
    turbine_df = pd.read_csv(turbine_path, header=None, names=['ws', 'power', 'ct'])
    temp_turbine_path = project_root / "scripts" / "temp_nordex_n164.csv"
    turbine_df.to_csv(temp_turbine_path, index=False)

    site = WindSite.from_file(
        str(wind_data_path),
        source_type='vortex',
        height=164.0,
        skiprows=3,
        column_mapping={'ws': 'M(m/s)', 'wd': 'D(deg)'}
    )

    # Filter to year 2020
    years_from_2014 = ANALYSIS_YEAR - 2014
    start_idx = 4 + (years_from_2014 * 8760)
    leap_days = sum(1 for y in range(2014, ANALYSIS_YEAR)
                   if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0))
    start_idx += leap_days * 24
    is_leap = ((ANALYSIS_YEAR % 4 == 0 and ANALYSIS_YEAR % 100 != 0) or
              (ANALYSIS_YEAR % 400 == 0))
    year_hours = 8784 if is_leap else 8760
    end_idx = start_idx + year_hours

    filtered_timeseries = site.wind_data.timeseries.iloc[start_idx:end_idx].copy()
    filtered_wind_data = WindData(
        timeseries=filtered_timeseries,
        height=site.wind_data.height,
        timezone_offset=site.wind_data.timezone_offset,
        source=site.wind_data.source,
        metadata=site.wind_data.metadata
    )
    object.__setattr__(site, 'wind_data', filtered_wind_data)

    # Check sector availability from actual wind data
    print("1. SECTOR AVAILABILITY ANALYSIS")
    print("-" * 70)

    from latam_hybrid.wind.sector_management import calculate_sector_availability

    availability = calculate_sector_availability(
        site.wind_data.timeseries,
        SECTOR_MANAGEMENT_CONFIG.turbine_sectors
    )

    print(f"Restricted turbines: {list(SECTOR_MANAGEMENT_CONFIG.turbine_sectors.keys())}")
    print(f"Allowed sectors: 60-120° and 240-300° (120° total out of 360°)")
    print(f"Theoretical availability: {120/360:.1%}")
    print()

    print("Actual availability from wind data:")
    for turbine_id in sorted(availability.keys()):
        avail = availability[turbine_id]
        curtailment = 1 - avail
        print(f"  Turbine {turbine_id:2d}: {avail:.1%} available, {curtailment:.1%} curtailed")

    avg_availability = np.mean(list(availability.values()))
    print(f"\n  Average availability: {avg_availability:.1%}")
    print()

    # Run simulation
    print("2. RUNNING SIMULATION")
    print("-" * 70)

    site = (
        site
        .with_turbine(
            TurbineModel.from_csv(
                str(temp_turbine_path),
                name="Nordex N164",
                hub_height=164,
                rotor_diameter=164,
                rated_power=7000
            )
        )
        .set_layout(
            TurbineLayout.from_csv(
                str(layout_path),
                x_column='x_coord',
                y_column='y_coord',
                crs='EPSG:32719'
            )
        )
        .set_sector_management(SECTOR_MANAGEMENT_CONFIG)
    )

    result = (
        site
        .run_simulation(
            wake_model='Bastankhah_Gaussian',
            simulation_method='timeseries',
            compute_losses=True
        )
        .apply_losses(loss_config_file=str(losses_path))
        .calculate_production()
    )

    print("Simulation complete.")
    print()

    # Extract per-turbine data
    print("3. PER-TURBINE SECTOR LOSSES")
    print("-" * 70)

    ideal_per_turbine = np.array(result.metadata['ideal_per_turbine_gwh'])
    sector_loss_per_turbine = np.array(result.metadata['sector_loss_per_turbine_gwh'])

    print(f"{'Turbine':<10} {'Ideal (GWh)':<15} {'Sector Loss (GWh)':<20} {'Loss %':<10} {'Status'}")
    print("-" * 70)

    for i in range(len(ideal_per_turbine)):
        turbine_id = i + 1
        ideal = ideal_per_turbine[i]
        sector_loss = sector_loss_per_turbine[i]
        loss_pct = (sector_loss / ideal * 100) if ideal > 0 else 0

        status = "RESTRICTED" if turbine_id in SECTOR_MANAGEMENT_CONFIG.turbine_sectors else "Unrestricted"

        print(f"{turbine_id:<10} {ideal:<15.3f} {sector_loss:<20.3f} {loss_pct:<10.1f} {status}")

    print("-" * 70)
    print(f"{'TOTAL':<10} {ideal_per_turbine.sum():<15.3f} {sector_loss_per_turbine.sum():<20.3f}")
    print()

    # Farm-level analysis
    print("4. FARM-LEVEL ANALYSIS")
    print("-" * 70)

    total_ideal = ideal_per_turbine.sum()
    total_sector_loss = sector_loss_per_turbine.sum()
    farm_level_pct = (total_sector_loss / total_ideal * 100) if total_ideal > 0 else 0

    # Calculate for restricted turbines only
    restricted_indices = [tid - 1 for tid in SECTOR_MANAGEMENT_CONFIG.turbine_sectors.keys()]
    restricted_ideal = ideal_per_turbine[restricted_indices].sum()
    restricted_sector_loss = sector_loss_per_turbine[restricted_indices].sum()
    restricted_loss_pct = (restricted_sector_loss / restricted_ideal * 100) if restricted_ideal > 0 else 0

    print(f"Total farm ideal production: {total_ideal:.2f} GWh/yr")
    print(f"Total sector losses: {total_sector_loss:.2f} GWh/yr")
    print(f"Farm-level sector loss: {farm_level_pct:.2f}%")
    print()
    print(f"Restricted turbines (n={len(restricted_indices)}):")
    print(f"  Ideal production: {restricted_ideal:.2f} GWh/yr")
    print(f"  Sector losses: {restricted_sector_loss:.2f} GWh/yr")
    print(f"  Average loss per restricted turbine: {restricted_loss_pct:.2f}%")
    print()

    # Expected calculation
    print("5. EXPECTED vs ACTUAL")
    print("-" * 70)

    expected_loss_per_restricted = ideal_per_turbine.mean() * (1 - avg_availability)
    expected_total_sector_loss = expected_loss_per_restricted * len(restricted_indices)
    expected_farm_pct = (expected_total_sector_loss / total_ideal * 100)

    print(f"Expected sector loss per restricted turbine:")
    print(f"  Ideal × (1 - availability) = {ideal_per_turbine.mean():.3f} × {1-avg_availability:.1%} = {expected_loss_per_restricted:.3f} GWh")
    print()
    print(f"Expected total farm sector loss:")
    print(f"  {len(restricted_indices)} turbines × {expected_loss_per_restricted:.3f} GWh = {expected_total_sector_loss:.2f} GWh")
    print(f"  Farm-level: {expected_farm_pct:.2f}%")
    print()
    print(f"Actual farm-level: {farm_level_pct:.2f}%")
    print(f"Difference: {abs(expected_farm_pct - farm_level_pct):.2f} percentage points")
    print()

    print("=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
