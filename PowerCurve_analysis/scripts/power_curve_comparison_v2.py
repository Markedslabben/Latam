"""
Power Curve Performance Assessment using latam_hybrid framework.

Compares turbine performance (Nordex N164, V162-6.2, V163-4.5) using:
1. Time series AEP calculations
2. Weibull distribution AEP calculations
3. Sector management filtering (60-120° and 240-300°)

Uses existing latam_hybrid infrastructure for data loading and analysis.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from dataclasses import dataclass

# Add latam_hybrid to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'latam_hybrid'))

from latam_hybrid.input.wind_data_reader import VortexWindReader
from latam_hybrid.wind.turbine import TurbineModel
from latam_hybrid.core import WindData


@dataclass
class AnalysisConfig:
    """Configuration for power curve analysis."""

    # Paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "latam_hybrid" / "Inputdata"
    RESULTS_DIR = PROJECT_ROOT / "PowerCurve_analysis" / "results"
    FIGURES_DIR = PROJECT_ROOT / "PowerCurve_analysis" / "figures"

    # Wind data
    WIND_DATA_PATH = DATA_DIR / "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    WIND_HEIGHT = 164.0

    # Wind shear coefficient (from shear_estimate.md)
    ALPHA = 0.1846

    # Sector management (allowed wind directions)
    ALLOWED_SECTORS = [(60, 120), (240, 300)]

    # Turbine configurations to analyze
    TURBINE_CONFIGS = [
        {
            'name': 'Nordex N164',
            'file': 'Nordex N164.csv',
            'hub_height': 164,
            'rotor_diameter': 164,
            'rated_power': 7000,  # kW
        },
        {
            'name': 'V162-6.2 @ 125m',
            'file': 'V162_6.2.csv',
            'hub_height': 125,
            'rotor_diameter': 162,
            'rated_power': 6200,
        },
        {
            'name': 'V162-6.2 @ 145m',
            'file': 'V162_6.2.csv',
            'hub_height': 145,
            'rotor_diameter': 162,
            'rated_power': 6200,
        },
        {
            'name': 'V163-4.5 @ 125m',
            'file': 'V163_4.5.csv',
            'hub_height': 125,
            'rotor_diameter': 163,
            'rated_power': 4500,
        },
        {
            'name': 'V163-4.5 @ 145m',
            'file': 'V163_4.5.csv',
            'hub_height': 145,
            'rotor_diameter': 163,
            'rated_power': 4500,
        },
    ]


def load_vortex_data(config: AnalysisConfig) -> WindData:
    """
    Load Vortex wind data using latam_hybrid VortexWindReader.

    Returns:
        WindData object with timeseries at 164m height
    """
    print(f"Loading wind data from {config.WIND_DATA_PATH}")

    # Read Vortex data
    # Based on file inspection: YYYYMMDD HHMM  M(m/s) D(deg)  T(C)  De(k/m3) ...
    # Skip 3 header rows
    df = pd.read_csv(
        config.WIND_DATA_PATH,
        sep=r'\s+',
        skiprows=3,
        header=0
    )

    print(f"  Columns found: {df.columns.tolist()}")

    # Create datetime index from YYYYMMDD and HHMM columns
    df['datetime'] = pd.to_datetime(
        df['YYYYMMDD'].astype(str) + ' ' + df['HHMM'].astype(str).str.zfill(4),
        format='%Y%m%d %H%M'
    )
    df = df.set_index('datetime')

    # Rename columns to standard format
    df = df.rename(columns={
        'M(m/s)': 'ws',  # Wind speed
        'D(deg)': 'wd',  # Wind direction
    })

    # Keep only required columns
    df = df[['ws', 'wd']]

    # Create WindData object
    wind_data = WindData(
        timeseries=df,
        height=config.WIND_HEIGHT,
        timezone_offset=-4,  # UTC-04:00
        source="Vortex ERA5",
        metadata={
            'filepath': str(config.WIND_DATA_PATH),
            'height': config.WIND_HEIGHT,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
        }
    )

    print(f"✓ Loaded {len(df)} records from {df.index.min()} to {df.index.max()}")
    print(f"  Mean wind speed: {df['ws'].mean():.2f} m/s")

    # Calculate data coverage
    hours_in_11_years = 11 * 365.25 * 24
    coverage_pct = (len(df) / hours_in_11_years) * 100
    print(f"  Data coverage: {coverage_pct:.1f}% (expected ~11 years hourly)")

    return wind_data


def load_turbine_power_curve(filepath: Path, name: str, hub_height: float,
                             rotor_diameter: float) -> TurbineModel:
    """
    Load turbine power curve using latam_hybrid TurbineModel.

    Args:
        filepath: Path to power curve CSV
        name: Turbine name
        hub_height: Hub height in meters
        rotor_diameter: Rotor diameter in meters

    Returns:
        TurbineModel instance
    """
    # Power curves are in format: wind_speed,power,Ct (no header)
    # Read CSV manually first to add headers
    df = pd.read_csv(filepath, header=None, names=['ws', 'power', 'ct'])

    # Save to temporary file with headers
    temp_file = Path('/tmp/temp_power_curve.csv')
    df.to_csv(temp_file, index=False)

    # Load using TurbineModel
    turbine = TurbineModel.from_csv(
        temp_file,
        name=name,
        hub_height=hub_height,
        rotor_diameter=rotor_diameter,
        ws_column='ws',
        power_column='power',
        ct_column='ct'
    )

    # Clean up
    temp_file.unlink()

    return turbine


def calculate_weibull_parameters(wind_speeds: np.ndarray) -> Tuple[float, float, float]:
    """
    Fit Weibull distribution to wind speed data.

    Args:
        wind_speeds: Array of wind speed values

    Returns:
        Tuple of (A, k, vmean) where:
        - A: Weibull scale parameter
        - k: Weibull shape parameter
        - vmean: Mean wind speed from Weibull fit
    """
    # Remove zeros and NaNs
    ws_clean = wind_speeds[~np.isnan(wind_speeds) & (wind_speeds > 0)]

    # Fit Weibull distribution using maximum likelihood
    shape, loc, scale = stats.weibull_min.fit(ws_clean, floc=0)

    k = shape  # Shape parameter
    A = scale  # Scale parameter

    # Calculate mean from Weibull: vmean = A * Γ(1 + 1/k)
    from scipy.special import gamma
    vmean = A * gamma(1 + 1/k)

    return A, k, vmean


def adjust_wind_speed_height(ws: pd.Series, from_height: float,
                             to_height: float, alpha: float) -> pd.Series:
    """
    Adjust wind speed from one height to another using power law.

    Args:
        ws: Wind speed series at from_height
        from_height: Original measurement height (m)
        to_height: Target height (m)
        alpha: Wind shear coefficient

    Returns:
        Wind speed series at to_height
    """
    ws_adjusted = ws * (to_height / from_height) ** alpha
    return ws_adjusted


def calculate_aep_timeseries(ws: pd.Series, turbine: TurbineModel,
                            n_turbines: int = 13) -> Dict:
    """
    Calculate Annual Energy Production from time series.

    Args:
        ws: Wind speed time series
        turbine: TurbineModel instance
        n_turbines: Number of turbines

    Returns:
        Dictionary with AEP metrics
    """
    # Get power output for each wind speed
    power_kw = turbine.power_at_wind_speed(ws.values)

    # Calculate total energy (kWh)
    total_energy_kwh = power_kw.sum()  # Hourly data

    # Annualize (accounting for partial year if data < 1 year)
    hours_in_data = len(ws)
    hours_per_year = 8760
    years_of_data = hours_in_data / hours_per_year

    annual_energy_kwh = total_energy_kwh / years_of_data if years_of_data > 0 else 0

    # Scale to wind farm (n_turbines)
    farm_aep_kwh = annual_energy_kwh * n_turbines
    farm_aep_gwh = farm_aep_kwh / 1e6

    # Calculate capacity factor
    rated_power_mw = (turbine.rated_power * n_turbines) / 1000
    max_annual_gwh = rated_power_mw * hours_per_year / 1000
    capacity_factor = (farm_aep_gwh / max_annual_gwh) * 100 if max_annual_gwh > 0 else 0

    # Calculate full load hours
    full_load_hours = (farm_aep_gwh * 1e6) / (turbine.rated_power * n_turbines)

    return {
        'aep_gwh': farm_aep_gwh,
        'capacity_factor': capacity_factor,
        'full_load_hours': full_load_hours,
        'rated_power_mw': rated_power_mw,
    }


def calculate_aep_weibull(A: float, k: float, turbine: TurbineModel,
                         n_turbines: int = 13) -> Dict:
    """
    Calculate Annual Energy Production using Weibull distribution.

    Args:
        A: Weibull scale parameter
        k: Weibull shape parameter
        turbine: TurbineModel instance
        n_turbines: Number of turbines

    Returns:
        Dictionary with AEP metrics
    """
    # Get power curve
    ws_curve = turbine.spec.power_curve['ws'].values
    power_curve = turbine.spec.power_curve['power'].values

    # Calculate Weibull probability density for each wind speed
    ws_bins = np.arange(0, 30, 0.1)  # 0 to 30 m/s in 0.1 m/s steps
    weibull_pdf = stats.weibull_min.pdf(ws_bins, k, scale=A)

    # Interpolate power for wind speed bins
    power_bins = np.interp(ws_bins, ws_curve, power_curve, left=0, right=0)

    # Calculate expected power
    expected_power_kw = np.trapz(power_bins * weibull_pdf, ws_bins)

    # Annual energy (8760 hours)
    annual_energy_kwh = expected_power_kw * 8760

    # Scale to wind farm
    farm_aep_kwh = annual_energy_kwh * n_turbines
    farm_aep_gwh = farm_aep_kwh / 1e6

    # Calculate capacity factor
    rated_power_mw = (turbine.rated_power * n_turbines) / 1000
    max_annual_gwh = rated_power_mw * 8760 / 1000
    capacity_factor = (farm_aep_gwh / max_annual_gwh) * 100

    # Calculate full load hours
    full_load_hours = (farm_aep_gwh * 1e6) / (turbine.rated_power * n_turbines)

    return {
        'aep_gwh': farm_aep_gwh,
        'capacity_factor': capacity_factor,
        'full_load_hours': full_load_hours,
        'rated_power_mw': rated_power_mw,
    }


def filter_by_sectors(wind_data: WindData,
                     allowed_sectors: List[Tuple[float, float]]) -> WindData:
    """
    Filter wind data to only include allowed wind direction sectors.

    Args:
        wind_data: WindData object
        allowed_sectors: List of (min_deg, max_deg) tuples

    Returns:
        Filtered WindData object
    """
    df = wind_data.timeseries.copy()

    # Create mask for allowed sectors
    mask = pd.Series(False, index=df.index)
    for min_deg, max_deg in allowed_sectors:
        sector_mask = (df['wd'] >= min_deg) & (df['wd'] <= max_deg)
        mask = mask | sector_mask

    # Filter data
    df_filtered = df[mask]

    print(f"\nSector filtering: {len(df_filtered)} of {len(df)} records retained ({len(df_filtered)/len(df)*100:.1f}%)")

    # Create new WindData object
    filtered_data = WindData(
        timeseries=df_filtered,
        height=wind_data.height,
        timezone_offset=wind_data.timezone_offset,
        source=wind_data.source,
        metadata={
            **wind_data.metadata,
            'sector_filtered': True,
            'allowed_sectors': allowed_sectors,
        }
    )

    return filtered_data


def main():
    """Execute complete power curve performance assessment."""

    config = AnalysisConfig()

    # Create output directories
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("POWER CURVE PERFORMANCE ASSESSMENT")
    print("Using latam_hybrid framework")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # Phase 1: Load Data
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 1: DATA LOADING")
    print("=" * 80)

    wind_data = load_vortex_data(config)

    # -------------------------------------------------------------------------
    # Phase 2: Weibull Fitting
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 2: WIND STATISTICS AND WEIBULL FITTING")
    print("=" * 80)

    A, k, vmean_weibull = calculate_weibull_parameters(wind_data.timeseries['ws'].values)
    vmean_measured = wind_data.timeseries['ws'].mean()

    print(f"\nWeibull Parameters (at {config.WIND_HEIGHT}m):")
    print(f"  Scale parameter (A): {A:.3f} m/s")
    print(f"  Shape parameter (k): {k:.3f}")
    print(f"  Mean from Weibull:   {vmean_weibull:.3f} m/s")
    print(f"  Mean from data:      {vmean_measured:.3f} m/s")
    print(f"  Difference:          {abs(vmean_weibull - vmean_measured):.3f} m/s ({abs(vmean_weibull - vmean_measured)/vmean_measured*100:.2f}%)")

    # Save statistics
    stats_df = pd.DataFrame({
        'Parameter': ['Weibull A (m/s)', 'Weibull k', 'Mean WS Weibull (m/s)', 'Mean WS Measured (m/s)', 'Height (m)'],
        'Value': [A, k, vmean_weibull, vmean_measured, config.WIND_HEIGHT]
    })
    stats_df.to_csv(config.RESULTS_DIR / 'wind_statistics.csv', index=False)
    print(f"\n✓ Saved wind statistics")

    # -------------------------------------------------------------------------
    # Phase 3: AEP Calculations
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 3: AEP CALCULATIONS FOR ALL CONFIGURATIONS")
    print("=" * 80)

    results_timeseries = []
    results_weibull = []

    for turbine_config in config.TURBINE_CONFIGS:
        print(f"\n{turbine_config['name']}:")
        print(f"  Hub height: {turbine_config['hub_height']}m")

        # Load turbine power curve
        pc_file = config.DATA_DIR / turbine_config['file']
        turbine = load_turbine_power_curve(
            pc_file,
            name=turbine_config['name'],
            hub_height=turbine_config['hub_height'],
            rotor_diameter=turbine_config['rotor_diameter']
        )

        # Adjust wind speed to hub height
        ws_adjusted = adjust_wind_speed_height(
            wind_data.timeseries['ws'],
            from_height=config.WIND_HEIGHT,
            to_height=turbine_config['hub_height'],
            alpha=config.ALPHA
        )

        print(f"  Adjusted mean WS: {ws_adjusted.mean():.3f} m/s")

        # Calculate AEP using time series
        aep_ts = calculate_aep_timeseries(ws_adjusted, turbine, n_turbines=13)
        results_timeseries.append({
            'Configuration': turbine_config['name'],
            'AEP (GWh/yr)': aep_ts['aep_gwh'],
            'Full Load Hours (hr/yr)': aep_ts['full_load_hours'],
            'Capacity Factor (%)': aep_ts['capacity_factor'],
            'Rated Power (MW)': aep_ts['rated_power_mw'],
            'Normalized AEP': 0.0
        })

        print(f"  Time Series AEP: {aep_ts['aep_gwh']:.2f} GWh/yr, CF: {aep_ts['capacity_factor']:.1f}%")

        # Calculate Weibull parameters for adjusted wind speed
        A_adj, k_adj, _ = calculate_weibull_parameters(ws_adjusted.values)

        # Calculate AEP using Weibull
        aep_wb = calculate_aep_weibull(A_adj, k_adj, turbine, n_turbines=13)
        results_weibull.append({
            'Configuration': turbine_config['name'],
            'AEP (GWh/yr)': aep_wb['aep_gwh'],
            'Full Load Hours (hr/yr)': aep_wb['full_load_hours'],
            'Capacity Factor (%)': aep_wb['capacity_factor'],
            'Rated Power (MW)': aep_wb['rated_power_mw'],
            'Normalized AEP': 0.0
        })

        print(f"  Weibull AEP:     {aep_wb['aep_gwh']:.2f} GWh/yr, CF: {aep_wb['capacity_factor']:.1f}%")

    # Normalize AEP to Nordex N164 (first configuration)
    df_ts = pd.DataFrame(results_timeseries)
    df_ts['Normalized AEP'] = df_ts['AEP (GWh/yr)'] / df_ts.loc[0, 'AEP (GWh/yr)']

    df_wb = pd.DataFrame(results_weibull)
    df_wb['Normalized AEP'] = df_wb['AEP (GWh/yr)'] / df_wb.loc[0, 'AEP (GWh/yr)']

    # Save results
    print("\n" + "=" * 80)
    print("TABLE 1: TIME SERIES AEP RESULTS")
    print("=" * 80)
    print(df_ts.to_string(index=False))
    df_ts.to_csv(config.RESULTS_DIR / 'table1_timeseries_aep.csv', index=False)

    print("\n" + "=" * 80)
    print("TABLE 2: WEIBULL AEP RESULTS")
    print("=" * 80)
    print(df_wb.to_string(index=False))
    df_wb.to_csv(config.RESULTS_DIR / 'table2_weibull_aep.csv', index=False)

    # -------------------------------------------------------------------------
    # Phase 4: Sector Management Analysis
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 4: SECTOR MANAGEMENT ANALYSIS")
    print(f"Allowed sectors: {config.ALLOWED_SECTORS}")
    print("=" * 80)

    wind_data_sectors = filter_by_sectors(wind_data, config.ALLOWED_SECTORS)

    results_sectors = []

    for turbine_config in config.TURBINE_CONFIGS:
        # Load turbine
        pc_file = config.DATA_DIR / turbine_config['file']
        turbine = load_turbine_power_curve(
            pc_file,
            name=turbine_config['name'],
            hub_height=turbine_config['hub_height'],
            rotor_diameter=turbine_config['rotor_diameter']
        )

        # Adjust wind speed
        ws_adjusted = adjust_wind_speed_height(
            wind_data_sectors.timeseries['ws'],
            from_height=config.WIND_HEIGHT,
            to_height=turbine_config['hub_height'],
            alpha=config.ALPHA
        )

        # Calculate AEP with sector filtering
        aep_sector = calculate_aep_timeseries(ws_adjusted, turbine, n_turbines=13)

        results_sectors.append({
            'Configuration': turbine_config['name'],
            'AEP (GWh/yr)': aep_sector['aep_gwh'],
            'Full Load Hours (hr/yr)': aep_sector['full_load_hours'],
            'Capacity Factor (%)': aep_sector['capacity_factor'],
            'Rated Power (MW)': aep_sector['rated_power_mw'],
            'Normalized AEP': 0.0
        })

    df_sectors = pd.DataFrame(results_sectors)
    df_sectors['Normalized AEP'] = df_sectors['AEP (GWh/yr)'] / df_sectors.loc[0, 'AEP (GWh/yr)']

    print("\n" + "=" * 80)
    print("TABLE 3: SECTOR MANAGEMENT AEP RESULTS")
    print("=" * 80)
    print(df_sectors.to_string(index=False))
    df_sectors.to_csv(config.RESULTS_DIR / 'table3_sector_management_aep.csv', index=False)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {config.RESULTS_DIR}")


if __name__ == "__main__":
    main()
