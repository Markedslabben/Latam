"""
Plot production per turbine with stacked losses for Nordex N164 simulation.

Creates a stacked bar chart showing:
- Bottom (100%): Net production with all losses applied
- Stacked: Sector management losses
- Stacked: Wake losses
- Stacked: Other losses (availability, electrical, environmental, etc.)
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from latam_hybrid.wind import WindSite
from latam_hybrid.wind.turbine import TurbineModel
from latam_hybrid.wind.layout import TurbineLayout
from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG
from latam_hybrid.core.data_models import WindData

# Color palette from legacy code
PALETTE = {
    'sky_blue':    '#4DADEC',  # Net production
    'moss_green':  '#68A357',  # Sector management loss
    'sunset_orange': '#E67E22',# Wake loss
    'violet':      '#8E44AD',  # Other losses
    'slate_grey':  '#707B7C',  # Grid lines
}

def main():
    """Generate turbine production plot with stacked losses."""

    # ========================================================================
    # CONFIGURATION: Year to analyze (for faster testing)
    # ========================================================================
    ANALYSIS_YEAR = 2020  # Set to specific year (e.g., 2020) or None for full dataset

    print("=" * 70)
    print("GENERATING TURBINE PRODUCTION PLOT")
    print("=" * 70)
    print()

    # File paths
    project_root = Path(__file__).parent.parent
    wind_data_path = project_root / "latam_hybrid" / "Inputdata" / "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    turbine_path = project_root / "latam_hybrid" / "Inputdata" / "Nordex N164.csv"
    layout_path = project_root / "latam_hybrid" / "Inputdata" / "Turbine_layout_13.csv"
    losses_path = project_root / "latam_hybrid" / "Inputdata" / "losses.csv"

    # Output filename includes year for clarity
    year_suffix = f"_{ANALYSIS_YEAR}" if ANALYSIS_YEAR else "_full"
    output_path = project_root / "latam_hybrid" / "claudedocs" / f"Production_per_turbine_N164_timeseries{year_suffix}.png"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load turbine CSV (no headers - need to add them)
        turbine_df = pd.read_csv(turbine_path, header=None, names=['ws', 'power', 'ct'])
        temp_turbine_path = project_root / "scripts" / "temp_nordex_n164.csv"
        turbine_df.to_csv(temp_turbine_path, index=False)

        print("Running simulation to get turbine-level production data...")
        print()

        # Load wind data
        site = WindSite.from_file(
            str(wind_data_path),
            source_type='vortex',
            height=164.0,
            skiprows=3,
            column_mapping={'ws': 'M(m/s)', 'wd': 'D(deg)'}
        )

        # Filter to specific year if requested (for faster testing)
        # Note: Vortex file starts at 2013-12-31 20:00 UTC
        # Data is hourly, so we can calculate row indices for specific years
        if ANALYSIS_YEAR is not None:
            # Calculate start index for requested year
            # File starts: 2013-12-31 20:00
            # 2014-01-01 00:00 is at index 4 (4 hours offset)
            years_from_2014 = ANALYSIS_YEAR - 2014
            start_idx = 4 + (years_from_2014 * 8760)  # 4 hours offset + years * hours_per_year

            # For leap years, add extra days
            # Count leap years between 2014 and ANALYSIS_YEAR
            leap_days = sum(1 for y in range(2014, ANALYSIS_YEAR)
                           if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0))
            start_idx += leap_days * 24

            # One year of data (account for leap year)
            is_leap = ((ANALYSIS_YEAR % 4 == 0 and ANALYSIS_YEAR % 100 != 0) or
                      (ANALYSIS_YEAR % 400 == 0))
            year_hours = 8784 if is_leap else 8760

            end_idx = start_idx + year_hours

            # Filter timeseries
            filtered_timeseries = site.wind_data.timeseries.iloc[start_idx:end_idx].copy()

            print(f"Filtered to year {ANALYSIS_YEAR} (indices {start_idx}:{end_idx}): " +
                  f"{len(filtered_timeseries)} hours")
        else:
            filtered_timeseries = site.wind_data.timeseries.copy()
            print(f"Using full dataset: {len(filtered_timeseries)} hours")

        print()

        # Create filtered WindData object
        filtered_wind_data = WindData(
            timeseries=filtered_timeseries,
            height=site.wind_data.height,
            timezone_offset=site.wind_data.timezone_offset,
            source=site.wind_data.source,
            metadata=site.wind_data.metadata
        )
        object.__setattr__(site, 'wind_data', filtered_wind_data)

        # Build the site with turbine and layout
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

        # Run simulation and apply losses
        result_with_losses = (
            site
            .run_simulation(
                wake_model='Bastankhah_Gaussian',
                simulation_method='timeseries',
                compute_losses=True
            )
            .apply_losses(loss_config_file=str(losses_path))
            .calculate_production()
        )

        print("Simulation complete. Extracting PyWake result objects...")
        print()

        # Debug: Print all metadata keys
        print(f"Metadata keys available: {list(result_with_losses.metadata.keys())}")

        # Get PyWake simulation result object from metadata
        pywake_sim = result_with_losses.metadata.get('pywake_sim_result')

        if pywake_sim is None:
            print("WARNING: PyWake simulation result not found in metadata")
            print("Available metadata:", result_with_losses.metadata)
            print("\nFalling back to using turbine_production_gwh from result...")
            # We'll use the aggregated values instead

        # Extract per-turbine loss arrays from metadata (NEW format)
        # All values are in GWh/yr per turbine (absolute values, not percentages)

        ideal_per_turbine_gwh = np.array(result_with_losses.metadata.get('ideal_per_turbine_gwh', []))
        wake_loss_per_turbine = np.array(result_with_losses.metadata.get('wake_loss_per_turbine_gwh', []))
        sector_loss_per_turbine = np.array(result_with_losses.metadata.get('sector_loss_per_turbine_gwh', []))
        other_loss_per_turbine = np.array(result_with_losses.metadata.get('other_loss_per_turbine_gwh', []))
        turbine_production_net = np.array(result_with_losses.turbine_production_gwh)

        n_turbines = len(turbine_production_net)
        turbine_ids = list(range(1, n_turbines + 1))

        # Get farm-level loss percentages for display
        wake_loss_pct = float(result_with_losses.wake_loss_percent)
        sector_loss_pct = float(result_with_losses.sector_loss_percent)

        # Calculate other losses percentage
        loss_breakdown = result_with_losses.loss_breakdown
        other_losses_pct = 0.0
        if 'user_losses' in loss_breakdown:
            for loss_pct in loss_breakdown['user_losses'].values():
                other_losses_pct += float(loss_pct)

        print(f"Per-turbine statistics:")
        print(f"  Ideal production: {np.mean(ideal_per_turbine_gwh):.3f} GWh/yr (mean)")
        print(f"  Wake losses: {np.mean(wake_loss_per_turbine):.3f} GWh/yr (mean, {wake_loss_pct:.2f}% farm-level)")
        print(f"  Sector losses: {np.mean(sector_loss_per_turbine):.3f} GWh/yr (mean, {sector_loss_pct:.2f}% farm-level)")
        print(f"  Other losses: {np.mean(other_loss_per_turbine):.3f} GWh/yr (mean, {other_losses_pct:.2f}%)")
        print(f"  Net production: {np.mean(turbine_production_net):.3f} GWh/yr (mean)")
        print(f"  Total farm net: {np.sum(turbine_production_net):.2f} GWh/yr")

        # Verify stacking integrity
        stack_total = turbine_production_net + other_loss_per_turbine + sector_loss_per_turbine + wake_loss_per_turbine
        verification_error = np.max(np.abs(stack_total - ideal_per_turbine_gwh))
        print(f"\n  Stack verification: Max error = {verification_error:.6f} GWh (should be ~0)")
        print(f"  Total bar height will equal ideal production: {np.mean(stack_total):.3f} GWh/yr (mean)")
        print()

        # Create stacked bar plot
        print("Creating plot...")

        fig, ax = plt.subplots(figsize=(14, 7))

        # X-axis positions
        x = np.arange(n_turbines)
        width = 0.8

        # Stack the bars (bottom to top):
        # Total bar height = Ideal production (no losses)
        # 1. Net production (largest segment at bottom) - after ALL losses
        # 2. Other losses - stacked on net
        # 3. Sector management losses - stacked on other
        # 4. Wake losses - stacked on sector (smallest, top)
        #
        # Visual interpretation: Start from ideal production, losses "eat away" from top
        # Mathematical: ideal = net + other + sector + wake

        # All arrays are per-turbine annual production values (GWh/yr per turbine)
        segment1_net = turbine_production_net  # Net production (LARGEST, bottom)
        segment2_other = other_loss_per_turbine  # Other losses
        segment3_sector = sector_loss_per_turbine  # Sector losses
        segment4_wake = wake_loss_per_turbine  # Wake losses (smallest, top)

        # Create stacked bar plot - production at bottom, losses stacked on top
        bars1 = ax.bar(x, segment1_net, width,
                      label='Net Production',
                      color=PALETTE['sky_blue'])

        bars2 = ax.bar(x, segment2_other, width,
                      bottom=segment1_net,
                      label=f'Other Losses ({other_losses_pct:.1f}%)',
                      color=PALETTE['violet'])

        bars3 = ax.bar(x, segment3_sector, width,
                      bottom=segment1_net + segment2_other,
                      label=f'Sector mgmt loss ({sector_loss_pct:.1f}%)',
                      color=PALETTE['moss_green'])

        bars4 = ax.bar(x, segment4_wake, width,
                      bottom=segment1_net + segment2_other + segment3_sector,
                      label=f'Wake loss ({wake_loss_pct:.1f}%)',
                      color=PALETTE['sunset_orange'])

        # Add value labels on net production bars (largest segment)
        for i, (bar, val) in enumerate(zip(bars1, segment1_net)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height/2,
                   f'{val:.1f}',
                   ha='center', va='center', fontsize=12, color='white', fontweight='bold')

        # Add percentage labels on other loss bars
        for i, (bar, val) in enumerate(zip(bars2, segment2_other)):
            if val > 0.3:  # Only show if segment is large enough
                height = bar.get_height()
                y_pos = segment1_net[i] + height/2
                percentage = (val / ideal_per_turbine_gwh[i]) * 100
                ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                       f'{percentage:.1f}%',
                       ha='center', va='center', fontsize=10, color='white', fontweight='bold')

        # Add percentage labels on sector management loss bars
        for i, (bar, val) in enumerate(zip(bars3, segment3_sector)):
            if val > 0.3:  # Only show if segment is large enough
                height = bar.get_height()
                y_pos = segment1_net[i] + segment2_other[i] + height/2
                percentage = (val / ideal_per_turbine_gwh[i]) * 100
                ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                       f'{percentage:.1f}%',
                       ha='center', va='center', fontsize=10, color='white', fontweight='bold')

        # Add percentage labels on wake loss bars
        for i, (bar, val) in enumerate(zip(bars4, segment4_wake)):
            if val > 0.3:  # Only show if segment is large enough
                height = bar.get_height()
                y_pos = segment1_net[i] + segment2_other[i] + segment3_sector[i] + height/2
                percentage = (val / ideal_per_turbine_gwh[i]) * 100
                ax.text(bar.get_x() + bar.get_width()/2., y_pos,
                       f'{percentage:.1f}%',
                       ha='center', va='center', fontsize=10, color='white', fontweight='bold')

        # Formatting - all font sizes increased by 50%
        ax.set_xlabel('Turbine Number', fontsize=18, fontweight='bold')
        ax.set_ylabel('Annual Production [GWh/yr]', fontsize=18, fontweight='bold')

        # Title shows analysis period
        period_str = f"Year {ANALYSIS_YEAR}" if ANALYSIS_YEAR else "Full Dataset"
        ax.set_title(f'Annual Production per Turbine - Nordex N164 ({period_str})\n' +
                    f'Total Farm: {result_with_losses.aep_gwh:.2f} GWh/yr | ' +
                    f'Capacity Factor: {result_with_losses.capacity_factor*100:.1f}%',
                    fontsize=21, fontweight='bold', pad=20)

        # Set x-tick labels to turbine numbers (1-13)
        ax.set_xticks(x)
        ax.set_xticklabels(turbine_ids, fontsize=16)

        # Set y-tick label font size
        ax.tick_params(axis='y', labelsize=14)

        # Add grid
        ax.grid(axis='y', color=PALETTE['slate_grey'], alpha=0.3, linestyle='--', linewidth=0.5)
        ax.set_axisbelow(True)

        # Legend - positioned in lower right to avoid blocking data
        ax.legend(loc='lower right', fontsize=15, framealpha=0.9)

        # Tight layout
        plt.tight_layout()

        # Save plot
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_path}")
        print()

        # Also display
        plt.show()

        print("=" * 70)
        print("PLOT GENERATION COMPLETE")
        print("=" * 70)

    except Exception as e:
        print()
        print("=" * 70)
        print("ERROR DURING PLOT GENERATION")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
