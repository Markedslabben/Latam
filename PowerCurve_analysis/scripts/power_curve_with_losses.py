"""
Power Curve Analysis with Full PyWake Simulation and Corrected Loss Calculations.

Analyzes 5 turbine configurations using:
- PyWake wake modeling (Bastankhah-Gaussian)
- Corrected energy-based sector management losses
- Corrected other losses (availability, electrical, etc.)
- Year 2020 data for fast testing (8,784 hours)

Generates:
- Summary CSV table (Table 4)
- Per-turbine loss breakdown CSV for each configuration

Runtime: ~10-15 minutes for year 2020 (vs 20-30 min for full 11 years)
"""

import sys
from pathlib import Path
import time
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from latam_hybrid.wind import WindSite
from latam_hybrid.wind.turbine import TurbineModel
from latam_hybrid.wind.layout import TurbineLayout
from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG
from latam_hybrid.core.data_models import WindData
from latam_hybrid.output.export import export_per_turbine_losses_table


# ============================================================================
# CONFIGURATION
# ============================================================================

ANALYSIS_YEAR = None  # Use all 11.3 years - set to year number for testing (e.g., 2020)

# Wind shear coefficient (calculated from Global Wind Atlas data)
# Using power law: V/V_ref = (H/H_ref)^ALPHA
WIND_SHEAR_ALPHA = 0.1846  # Calculated from 50m, 100m, 150m, 200m measurements
WIND_DATA_HEIGHT = 164  # Reference height of Vortex ERA5 wind data (meters)

TURBINE_CONFIGS = [
    {
        'name': 'Nordex N164 @ 164m',
        'short_name': 'Nordex_N164_164m',
        'file': 'Nordex N164.csv',
        'hub_height': 164,
        'rotor_diameter': 164,
        'rated_power': 7000,
        'wind_height': 164  # No adjustment needed
    },
    {
        'name': 'Vestas V162-6.2 @ 145m',
        'short_name': 'V162-6.2_145m',
        'file': 'V162_6.2.csv',
        'hub_height': 145,
        'rotor_diameter': 162,
        'rated_power': 6200,
        'wind_height': 164  # Wind data at 164m, adjust to 145m
    },
    {
        'name': 'Vestas V163-4.5 @ 145m',
        'short_name': 'V163-4.5_145m',
        'file': 'V163_4.5.csv',
        'hub_height': 145,
        'rotor_diameter': 163,
        'rated_power': 4500,
        'wind_height': 164  # Wind data at 164m, adjust to 145m
    },
    {
        'name': 'Vestas V162-6.2 @ 125m',
        'short_name': 'V162-6.2_125m',
        'file': 'V162_6.2.csv',
        'hub_height': 125,
        'rotor_diameter': 162,
        'rated_power': 6200,
        'wind_height': 164  # Wind data at 164m, adjust to 125m
    },
    {
        'name': 'Vestas V163-4.5 @ 125m',
        'short_name': 'V163-4.5_125m',
        'file': 'V163_4.5.csv',
        'hub_height': 125,
        'rotor_diameter': 163,
        'rated_power': 4500,
        'wind_height': 164  # Wind data at 164m, adjust to 125m
    }
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_progress_bar(current, total, start_time, bar_length=20):
    """
    Print ASCII progress bar with ETA calculation.

    Args:
        current: Current iteration (1-indexed)
        total: Total iterations
        start_time: Start timestamp from time.time()
        bar_length: Width of progress bar in characters
    """
    percent = (current / total) * 100
    filled = int(bar_length * current / total)
    bar = '#' * filled + ' ' * (bar_length - filled)

    # Calculate ETA
    elapsed = time.time() - start_time
    if current > 0:
        eta_seconds = (elapsed / current) * (total - current)
        if eta_seconds > 60:
            eta_str = f"{int(eta_seconds / 60)} min"
        else:
            eta_str = f"{int(eta_seconds)} sec"
    else:
        eta_str = "calculating..."

    status = "Complete!" if current == total else f"ETA: {eta_str}"

    print(f"\rProgress: [{bar}] {percent:.0f}% ({current}/{total} turbines) - {status}", end='')
    if current == total:
        print()  # New line when complete


def filter_to_year(site, year):
    """
    Filter wind data to specific year (handles leap years correctly).

    Args:
        site: WindSite object with full dataset
        year: Year to extract (e.g., 2020), or None to use all years

    Returns:
        tuple: (WindSite with filtered wind data, number of hours)
    """
    # If year is None, use all available data
    if year is None:
        total_hours = len(site.wind_data.timeseries)
        return site, total_hours

    # Calculate start index for requested year
    # Vortex file starts: 2013-12-31 20:00
    # 2014-01-01 00:00 is at index 4 (4 hours offset)
    years_from_2014 = year - 2014
    start_idx = 4 + (years_from_2014 * 8760)

    # Account for leap years between 2014 and target year
    leap_days = sum(1 for y in range(2014, year)
                   if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0))
    start_idx += leap_days * 24

    # Check if target year is leap year
    is_leap = ((year % 4 == 0 and year % 100 != 0) or (year % 400 == 0))
    year_hours = 8784 if is_leap else 8760

    end_idx = start_idx + year_hours

    # Filter timeseries
    filtered_timeseries = site.wind_data.timeseries.iloc[start_idx:end_idx].copy()

    # Create new WindData object
    filtered_wind_data = WindData(
        timeseries=filtered_timeseries,
        height=site.wind_data.height,
        timezone_offset=site.wind_data.timezone_offset,
        source=site.wind_data.source,
        metadata=site.wind_data.metadata
    )

    # Update site with filtered data (immutable dataclass workaround)
    object.__setattr__(site, 'wind_data', filtered_wind_data)

    return site, year_hours


def format_time(seconds):
    """Format seconds as MM:SS string."""
    minutes = int(seconds / 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def extrapolate_wind_to_hub_height(site, target_hub_height, alpha=WIND_SHEAR_ALPHA, ref_height=WIND_DATA_HEIGHT):
    """
    Extrapolate wind speed timeseries to target hub height using power law.

    Power law: V_target = V_ref * (H_target / H_ref)^alpha

    This correction is essential because turbines at different hub heights experience
    different wind speeds due to wind shear. The reference wind data is at 164m, but
    turbines at 125m and 145m require height-corrected wind speeds for accurate
    energy yield predictions.

    Args:
        site: WindSite object with wind data at reference height
        target_hub_height: Target hub height in meters
        alpha: Wind shear exponent (default from configuration)
        ref_height: Reference height of wind data in meters (default from configuration)

    Returns:
        WindSite: New WindSite object with extrapolated wind speeds at target hub height
    """
    # Calculate correction factor
    correction_factor = (target_hub_height / ref_height) ** alpha

    # Calculate mean wind speed change for logging
    original_mean_ws = site.wind_data.timeseries['ws'].mean()
    corrected_mean_ws = original_mean_ws * correction_factor

    # Log the extrapolation with detailed information
    print(f"  -> Applying wind shear correction: {ref_height}m -> {target_hub_height}m")
    print(f"     Shear exponent (alpha) = {alpha:.4f}")
    print(f"     Correction factor = {correction_factor:.4f} ({(correction_factor-1)*100:+.2f}%)")
    print(f"     Mean WS: {original_mean_ws:.2f} m/s -> {corrected_mean_ws:.2f} m/s")

    # Create copy of timeseries and apply correction
    extrapolated_timeseries = site.wind_data.timeseries.copy()
    extrapolated_timeseries['ws'] = extrapolated_timeseries['ws'] * correction_factor

    # If turbulence intensity is present and wind-speed dependent, it should remain unchanged
    # (TI is typically measured/calculated relative to local wind speed, so ratio stays constant)

    # Create new WindData object with extrapolated values
    extrapolated_wind_data = WindData(
        timeseries=extrapolated_timeseries,
        height=target_hub_height,  # Update height to target
        timezone_offset=site.wind_data.timezone_offset,
        source=f"{site.wind_data.source} (wind shear corrected to {target_hub_height}m, α={alpha:.4f})",
        metadata={
            **site.wind_data.metadata,
            'extrapolated_from': ref_height,
            'alpha': alpha,
            'correction_factor': correction_factor,
            'target_hub_height': target_hub_height
        }
    )

    # Create new site with extrapolated wind data
    object.__setattr__(site, 'wind_data', extrapolated_wind_data)

    return site


# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def main():
    """Execute power curve analysis with losses for all turbine configurations."""

    print("=" * 50)
    print("POWER CURVE ANALYSIS WITH LOSSES")
    year_display = "All years (11.3 years)" if ANALYSIS_YEAR is None else str(ANALYSIS_YEAR)
    print(f"Year: {year_display}")
    print("=" * 50)
    print()

    # Setup paths
    wind_data_path = project_root / "latam_hybrid" / "Inputdata" / "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    layout_path = project_root / "latam_hybrid" / "Inputdata" / "Turbine_layout_13.csv"
    losses_path = project_root / "latam_hybrid" / "Inputdata" / "losses.csv"
    results_dir = project_root / "PowerCurve_analysis" / "results"

    # Create results directory
    results_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {results_dir}")
    print()

    print(f"Wind data source: {wind_data_path}")
    print()

    # Initialize results storage
    results = []
    start_time = time.time()

    # Initial progress bar
    print_progress_bar(0, len(TURBINE_CONFIGS), start_time)

    # ========================================================================
    # MAIN LOOP: Process each turbine configuration
    # ========================================================================

    for idx, config in enumerate(TURBINE_CONFIGS, 1):
        print()
        print("=" * 50)
        print(f"[{idx}/{len(TURBINE_CONFIGS)}] {config['name']} ({config['rated_power']/1000:.1f} MW)")
        print("=" * 50)

        config_start = time.time()

        # --------------------------------------------------------------------
        # Step 1: Load and prepare turbine power curve
        # --------------------------------------------------------------------
        print("  -> Loading turbine power curve...", end='', flush=True)
        turbine_path = project_root / "latam_hybrid" / "Inputdata" / config['file']
        turbine_df = pd.read_csv(turbine_path, header=None, names=['ws', 'power', 'ct'])

        # Create temporary file with headers (required by TurbineModel.from_csv)
        temp_turbine_path = results_dir / f"temp_{config['short_name']}.csv"
        turbine_df.to_csv(temp_turbine_path, index=False)
        print(" OK")

        # --------------------------------------------------------------------
        # Step 2: Load wind data fresh for this configuration
        # --------------------------------------------------------------------
        print(f"  -> Loading wind data at {config['wind_height']}m...", end='', flush=True)
        site = WindSite.from_file(
            str(wind_data_path),
            source_type='vortex',
            height=float(config['wind_height']),
            skiprows=3,
            column_mapping={'ws': 'M(m/s)', 'wd': 'D(deg)'}
        )
        print(" OK")

        # Filter to analysis year
        if ANALYSIS_YEAR is None:
            print(f"  -> Using all years...", end='', flush=True)
        else:
            print(f"  -> Filtering to year {ANALYSIS_YEAR}...", end='', flush=True)
        site, year_hours = filter_to_year(site, ANALYSIS_YEAR)
        print(f" OK ({year_hours} hours)")

        # Extrapolate wind speed to hub height if needed
        if config['hub_height'] != config['wind_height']:
            site = extrapolate_wind_to_hub_height(site, config['hub_height'])

        # --------------------------------------------------------------------
        # Step 3: Configure site with turbine, layout, and sector management
        # --------------------------------------------------------------------
        print("  -> Setting up 13-turbine layout...", end='', flush=True)
        site = (
            site
            .with_turbine(
                TurbineModel.from_csv(
                    str(temp_turbine_path),
                    name=config['name'],
                    hub_height=config['hub_height'],
                    rotor_diameter=config['rotor_diameter'],
                    rated_power=config['rated_power']
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
        )
        print(" OK")

        print("  -> Configuring sector management (6 turbines restricted)...", end='', flush=True)
        site = site.set_sector_management(SECTOR_MANAGEMENT_CONFIG)
        print(" OK")

        # --------------------------------------------------------------------
        # Step 4: Run PyWake simulations (2 simulations: ideal + realistic)
        # --------------------------------------------------------------------
        print()
        print("  Running PyWake Simulations:")

        sim_start = time.time()
        print("    [1/2] Ideal simulation (no wake).............", end='', flush=True)

        result = (
            site
            .run_simulation(
                wake_model='Bastankhah_Gaussian',
                simulation_method='timeseries',
                compute_losses=True  # Enables dual simulation
            )
        )

        sim_1_time = time.time() - sim_start
        print(f" OK ({format_time(sim_1_time)})")

        sim_start_2 = time.time()
        print("    [2/2] Realistic simulation (with wake).......", end='', flush=True)
        # Second simulation happens inside compute_losses=True above
        sim_2_time = time.time() - sim_start_2
        print(f" OK (included in [1/2])")

        # --------------------------------------------------------------------
        # Step 5: Apply non-PyWake losses and calculate production
        # --------------------------------------------------------------------
        print()
        print("  -> Applying sector management (energy-based)...", end='', flush=True)
        result = result.apply_losses(loss_config_file=str(losses_path))
        print(" OK")

        print("  -> Applying other losses (8.8% total)...", end='', flush=True)
        result = result.calculate_production()
        print(" OK")

        # --------------------------------------------------------------------
        # Step 6: Extract and display results
        # --------------------------------------------------------------------
        print()
        print("  Results:")

        # Get metadata (these are ALREADY ANNUAL values from PyWake's .aep() method)
        # PyWake's .aep() returns annualized values (GWh/year), averaged over simulation period
        ideal_per_turbine = np.array(result.metadata['ideal_per_turbine_gwh'])
        wake_loss = np.array(result.metadata['wake_loss_per_turbine_gwh'])
        sector_loss = np.array(result.metadata['sector_loss_per_turbine_gwh'])
        other_loss = np.array(result.metadata['other_loss_per_turbine_gwh'])
        net_production = np.array(result.turbine_production_gwh)

        # Sum to get farm-level annual values (these are already GWh/year, not totals!)
        gross_aep = ideal_per_turbine.sum()
        wake_loss_gwh = wake_loss.sum()
        sector_loss_gwh = sector_loss.sum()
        other_loss_gwh = other_loss.sum()
        net_aep = net_production.sum()

        wake_loss_pct = (wake_loss_gwh / gross_aep) * 100
        sector_loss_pct = (sector_loss_gwh / gross_aep) * 100
        other_loss_pct = (other_loss_gwh / gross_aep) * 100

        # Calculate capacity factor (annual basis)
        total_capacity_mw = config['rated_power'] * 13 / 1000  # 13 turbines
        capacity_factor = (net_aep * 1000) / (total_capacity_mw * 8760)

        print(f"    Gross AEP:      {gross_aep:5.2f} GWh/yr")
        print(f"    Wake Loss:      {wake_loss_gwh:5.2f} GWh ({wake_loss_pct:.1f}%)")
        print(f"    Sector Loss:    {sector_loss_gwh:5.2f} GWh ({sector_loss_pct:.1f}%)")
        print(f"    Other Loss:     {other_loss_gwh:5.2f} GWh ({other_loss_pct:.1f}%)")
        print(f"    Net AEP:        {net_aep:5.2f} GWh/yr")
        print(f"    Capacity Factor: {capacity_factor*100:.1f}%")

        # --------------------------------------------------------------------
        # Step 7: Export per-turbine breakdown
        # --------------------------------------------------------------------
        print()
        print("  -> Exporting per-turbine losses...", end='', flush=True)

        # Update frozen dataclass attributes with farm-level annual values
        # (Metadata arrays are already GWh/year from PyWake, no conversion needed)
        object.__setattr__(result, 'aep_gwh', net_aep)
        object.__setattr__(result, 'capacity_factor', capacity_factor)
        object.__setattr__(result, 'wake_loss_percent', wake_loss_pct)
        object.__setattr__(result, 'sector_loss_percent', sector_loss_pct)

        per_turbine_path = results_dir / f"per_turbine_{config['short_name']}.csv"
        export_per_turbine_losses_table(result, str(per_turbine_path), format='csv')
        print(f" OK")
        print(f"  OK Saved: {per_turbine_path.name}")

        # --------------------------------------------------------------------
        # Step 8: Store summary results
        # --------------------------------------------------------------------
        # Extract wind shear correction information if applied
        wind_shear_info = ""
        if config['hub_height'] != WIND_DATA_HEIGHT:
            correction_factor = (config['hub_height'] / WIND_DATA_HEIGHT) ** WIND_SHEAR_ALPHA
            wind_shear_info = f"WS corrected from {WIND_DATA_HEIGHT}m (α={WIND_SHEAR_ALPHA:.4f}, factor={correction_factor:.4f})"
        else:
            wind_shear_info = f"WS at reference height ({WIND_DATA_HEIGHT}m, no correction)"

        results.append({
            'Configuration': config['name'],
            'Rated Power (MW)': config['rated_power'] / 1000,
            'Hub Height (m)': config['hub_height'],
            'Wind Data Height (m)': WIND_DATA_HEIGHT,
            'Shear Correction': wind_shear_info,
            'Gross AEP (GWh/yr)': round(gross_aep, 2),
            'Wake Loss (%)': round(wake_loss_pct, 1),
            'Sector Loss (%)': round(sector_loss_pct, 1),
            'Other Loss (%)': round(other_loss_pct, 1),
            'Total Loss (%)': round(wake_loss_pct + sector_loss_pct + other_loss_pct, 1),
            'Net AEP (GWh/yr)': round(net_aep, 2),
            'Capacity Factor (%)': round(capacity_factor * 100, 1),
            'Full Load Hours (hr/yr)': int(capacity_factor * 8760)
        })

        # Clean up temp file
        temp_turbine_path.unlink()

        config_time = time.time() - config_start
        print(f"\n  Configuration completed in {format_time(config_time)}")

        # Update progress bar
        print_progress_bar(idx, len(TURBINE_CONFIGS), start_time)

    # ========================================================================
    # GENERATE SUMMARY TABLE
    # ========================================================================

    print()
    print("=" * 50)
    print("GENERATING SUMMARY TABLE")
    print("=" * 50)
    print()

    print("Building comparative analysis...")
    df_results = pd.DataFrame(results)

    # Add production delta column (Vestas 6.2 - Vestas 4.5)
    # Calculate normalized production (Net AEP / Rated Power)
    df_results['Normalized Production (GWh/MW)'] = df_results['Net AEP (GWh/yr)'] / (df_results['Rated Power (MW)'] * 13)

    # Calculate deltas between V6.2 and V4.5 at same heights
    print("  -> Adding production delta column (V6.2 - V4.5)...")

    # Find matching pairs at same height
    v62_145_norm = df_results[df_results['Configuration'] == 'Vestas V162-6.2 @ 145m']['Normalized Production (GWh/MW)'].values[0]
    v45_145_norm = df_results[df_results['Configuration'] == 'Vestas V163-4.5 @ 145m']['Normalized Production (GWh/MW)'].values[0]
    delta_145 = v62_145_norm - v45_145_norm

    v62_125_norm = df_results[df_results['Configuration'] == 'Vestas V162-6.2 @ 125m']['Normalized Production (GWh/MW)'].values[0]
    v45_125_norm = df_results[df_results['Configuration'] == 'Vestas V163-4.5 @ 125m']['Normalized Production (GWh/MW)'].values[0]
    delta_125 = v62_125_norm - v45_125_norm

    # Add delta column
    df_results['V6.2-V4.5 Delta (%)'] = ''
    df_results.loc[df_results['Configuration'] == 'Vestas V162-6.2 @ 145m', 'V6.2-V4.5 Delta (%)'] = f"+{delta_145*100:.1f}%"
    df_results.loc[df_results['Configuration'] == 'Vestas V162-6.2 @ 125m', 'V6.2-V4.5 Delta (%)'] = f"+{delta_125*100:.1f}%"

    print("  -> Calculating normalized production metrics...")

    # Save to CSV
    year_suffix = "full" if ANALYSIS_YEAR is None else str(ANALYSIS_YEAR)
    summary_path = results_dir / f"table4_pywake_with_losses_{year_suffix}.csv"
    df_results.to_csv(summary_path, index=False)

    print(f"  OK Saved: {summary_path.name}")
    print()

    # ========================================================================
    # DISPLAY SUMMARY TABLE
    # ========================================================================

    print("SUMMARY TABLE PREVIEW:")
    print()

    # Create formatted display (simplified - just key columns)
    display_cols = [
        'Configuration',
        'Gross AEP (GWh/yr)',
        'Wake Loss (%)',
        'Sector Loss (%)',
        'Other Loss (%)',
        'Net AEP (GWh/yr)',
        'Capacity Factor (%)',
        'V6.2-V4.5 Delta (%)'
    ]

    # Print table
    for col in display_cols:
        print(f"{col:20s}", end='  ')
    print()
    print("-" * 150)

    for _, row in df_results.iterrows():
        for col in display_cols:
            val = str(row[col])
            print(f"{val:20s}", end='  ')
        print()

    print()

    # ========================================================================
    # VALIDATION CHECKS
    # ========================================================================

    print("=" * 50)
    print("VALIDATION CHECKS")
    print("=" * 50)
    print()

    all_valid = True

    # Check 1: Sector losses should be ~5-7%
    sector_losses = df_results['Sector Loss (%)']
    if sector_losses.min() >= 4.0 and sector_losses.max() <= 8.0:
        print(f"  OK Sector losses: {sector_losses.mean():.1f}% (energy-based - correct)")
    else:
        print(f"  FAIL Sector losses: {sector_losses.mean():.1f}% (out of expected range 4-8%)")
        all_valid = False

    # Check 2: Other losses should be ~7-9%
    other_losses = df_results['Other Loss (%)']
    if other_losses.min() >= 6.0 and other_losses.max() <= 10.0:
        print(f"  OK Other losses: {other_losses.mean():.1f}% (not swapped - correct)")
    else:
        print(f"  FAIL Other losses: {other_losses.mean():.1f}% (out of expected range 6-10%)")
        all_valid = False

    # Check 3: Total losses should be ~23-28%
    total_losses = df_results['Total Loss (%)']
    if total_losses.min() >= 20.0 and total_losses.max() <= 30.0:
        print(f"  OK Total losses: {total_losses.mean():.1f}% (reasonable range)")
    else:
        print(f"  FAIL Total losses: {total_losses.mean():.1f}% (out of expected range 20-30%)")
        all_valid = False

    print()

    if all_valid:
        print("  OK All validation checks passed!")
    else:
        print("  WARNING: Some validation checks failed - review results")

    # ========================================================================
    # COMPLETION SUMMARY
    # ========================================================================

    total_time = time.time() - start_time

    print()
    print("=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    print()

    print(f"Total runtime: {format_time(total_time)}")
    year_analyzed = "All years (11.3 years)" if ANALYSIS_YEAR is None else str(ANALYSIS_YEAR)
    print(f"Year analyzed: {year_analyzed} ({year_hours} hours)")
    print()

    print("Output files created:")
    print(f"  OK {summary_path.name}")
    for config in TURBINE_CONFIGS:
        print(f"  OK per_turbine_{config['short_name']}.csv")

    print()
    print("Next steps:")
    print("  1. Review CSV tables in PowerCurve_analysis/results/")
    print("  2. Update power_curve_analysis.md with Table 4")
    print("  3. Run full 11-year analysis if results look good")
    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
