"""
Test script for time series simulation with sector management and losses.

Tests the new latam_hybrid time series simulation implementation with:
- Nordex N164 (7.0 MW) turbine @ 164m
- 13-turbine layout
- Bastankhah-Gaussian wake model
- IEC 61400-1 NTM turbulence intensity
- Sector management (turbines 1,3,5,7,9,12 restricted)
- All losses from losses.csv

This script validates the implementation before integrating into reports.
"""

import sys
from pathlib import Path

# Add latam_hybrid to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'latam_hybrid'))

from latam_hybrid.wind import WindSite
from latam_hybrid.wind.turbine import TurbineModel
from latam_hybrid.wind.layout import TurbineLayout
from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG
import pandas as pd

def main():
    """Run test simulation with time series method."""

    print("=" * 70)
    print("LATAM HYBRID - TIME SERIES SIMULATION TEST")
    print("=" * 70)
    print()

    # File paths
    project_root = Path(__file__).parent.parent
    wind_data_path = project_root / "latam_hybrid" / "Inputdata" / "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    turbine_path = project_root / "latam_hybrid" / "Inputdata" / "Nordex N164.csv"
    layout_path = project_root / "latam_hybrid" / "Inputdata" / "Turbine_layout_13.csv"
    losses_path = project_root / "latam_hybrid" / "Inputdata" / "losses.csv"

    print("Configuration:")
    print(f"  Wind data: {wind_data_path.name}")
    print(f"  Turbine: Nordex N164 (7.0 MW) @ 164m")
    print(f"  Layout: 13 turbines")
    print(f"  Wake model: Bastankhah-Gaussian")
    print(f"  Simulation method: Time Series")
    print(f"  Time period: First year only (8760 hours)")
    print(f"  Turbulence: IEC 61400-1 NTM (variable)")
    print(f"  Sector management: Active (6 turbines restricted)")
    print()

    # Create and run simulation
    print("Loading wind data and running simulation...")
    print("Using first year only for faster testing...")
    print()

    try:
        # Load turbine CSV (no headers - need to add them)
        turbine_df = pd.read_csv(turbine_path, header=None, names=['ws', 'power', 'ct'])
        # Save with headers to temp file
        temp_turbine_path = project_root / "scripts" / "temp_nordex_n164.csv"
        turbine_df.to_csv(temp_turbine_path, index=False)

        # Load wind data and filter to first year only (for testing)
        from latam_hybrid.core.data_models import WindData

        site = WindSite.from_file(
            str(wind_data_path),
            source_type='vortex',
            height=164.0,
            skiprows=3,  # Skip header rows
            column_mapping={'ws': 'M(m/s)', 'wd': 'D(deg)'}  # Map standard names to Vortex columns
        )

        # Filter to first year only (8760 hours) - create new WindData object
        filtered_timeseries = site.wind_data.timeseries.iloc[:8760].copy()
        filtered_wind_data = WindData(
            timeseries=filtered_timeseries,
            height=site.wind_data.height,
            timezone_offset=site.wind_data.timezone_offset,
            source=site.wind_data.source,
            metadata=site.wind_data.metadata
        )

        # Replace wind_data using object.__setattr__ (since WindSite is frozen)
        object.__setattr__(site, 'wind_data', filtered_wind_data)

        result = (
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
                    crs='EPSG:32719'  # UTM Zone 19S for Latin America region
                )
            )
            .set_sector_management(SECTOR_MANAGEMENT_CONFIG)
            .run_simulation(
                wake_model='Bastankhah_Gaussian',
                simulation_method='timeseries',
                compute_losses=True
            )
            .apply_losses(loss_config_file=str(losses_path))
            .calculate_production()
        )

        print("=" * 70)
        print("SIMULATION RESULTS")
        print("=" * 70)
        print()

        # Print simulation parameters
        print("SIMULATION PARAMETERS")
        print("-" * 70)
        print(f"Wake model: {result.wake_model.value}")
        print(f"Number of turbines: {len(result.turbine_production_gwh)}")
        print(f"Total capacity: {result.metadata.get('total_capacity_mw', 'N/A'):.1f} MW")
        print()

        # Print gross AEP (before non-wake losses)
        gross_aep = result.gross_aep_gwh if hasattr(result, 'gross_aep_gwh') and result.gross_aep_gwh is not None else result.aep_gwh
        gross_cf = (gross_aep * 1000) / (result.metadata.get('total_capacity_mw', 91.0) * 8760) if gross_aep else 0

        print("GROSS AEP (with wake + sector effects, before other losses)")
        print("-" * 70)
        print(f"Farm total: {gross_aep:.2f} GWh/yr")
        print(f"Capacity factor: {gross_cf * 100:.2f}%")
        print()

        # Print loss breakdown
        print("LOSS BREAKDOWN")
        print("-" * 70)

        # Wake losses
        print(f"Wake losses: {result.wake_loss_percent:.2f}%")

        # Sector losses
        if result.sector_loss_percent > 0:
            print(f"Sector curtailment: {result.sector_loss_percent:.2f}%")
        else:
            print(f"Sector curtailment: 0.00% (no sector management)")

        # Other losses
        if hasattr(result, 'loss_breakdown'):
            loss_breakdown = result.loss_breakdown

            # User-specified losses
            user_losses = loss_breakdown.get('user_losses', {})
            for loss_name, loss_pct in user_losses.items():
                print(f"{loss_name.replace('_', ' ').title()}: {loss_pct:.2f}%")

            # Total loss
            total_loss_pct = loss_breakdown.get('total_loss_percentage', 0)
            print(f"{'=' * 40}")
            print(f"TOTAL LOSSES: {total_loss_pct:.2f}%")

        print()

        # Print per-turbine production
        print("PER-TURBINE ANNUAL PRODUCTION")
        print("-" * 70)
        import numpy as np
        turbine_prod = np.array(result.turbine_production_gwh)
        # Ensure 1D array and flatten if needed
        turbine_prod = turbine_prod.flatten()
        for i, prod in enumerate(turbine_prod, start=1):
            print(f"Turbine {i:2d}: {float(prod):.3f} GWh/yr")
        print(f"{'=' * 40}")
        print(f"Sum of turbines: {float(turbine_prod.sum()):.2f} GWh/yr")
        print()

        # Print net AEP
        print("NET AEP (after all losses)")
        print("-" * 70)

        # After apply_losses(), aep_gwh is the net AEP
        # gross_aep_gwh contains the AEP before non-wake losses
        if hasattr(result, 'gross_aep_gwh') and result.gross_aep_gwh is not None:
            print(f"Final production: {result.aep_gwh:.2f} GWh/yr")
            print(f"Net capacity factor: {result.capacity_factor * 100:.2f}%")
            # Calculate full load hours
            total_capacity_mw = result.metadata.get('total_capacity_mw', 91.0)
            full_load_hours = (result.aep_gwh * 1000) / total_capacity_mw
            print(f"Full load hours: {full_load_hours:.0f} hr/yr")
        else:
            print(f"Net AEP: {result.aep_gwh:.2f} GWh/yr (use .apply_losses() for detailed breakdown)")

        print()
        print("=" * 70)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)

        return result

    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR DURING SIMULATION")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()
