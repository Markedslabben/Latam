"""
Power Curve Performance Assessment for Dominican Republic Wind Site.

This script compares three turbine models (Nordex N164, Vestas V162-6.2, V163-4.5)
at different hub heights using 11 years of Vortex wind data.

Analysis includes:
1. Wind speed statistical analysis (Weibull fitting)
2. Hub height wind speed adjustment using shear coefficient
3. AEP calculations using time series and Weibull methods
4. Sector management impact assessment
5. Comprehensive visualizations and reporting

Author: Auto-generated for Latam Hybrid Project
Date: 2025-10-19
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.special import gamma
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Add latam_hybrid to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from latam_hybrid.input.wind_data_reader import read_wind_data
from latam_hybrid.wind.turbine import TurbineModel


# ============================================================================
# Configuration
# ============================================================================

class AnalysisConfig:
    """Configuration parameters for power curve analysis."""

    # File paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "latam_hybrid" / "Inputdata"
    OUTPUT_DIR = PROJECT_ROOT / "PowerCurve_analysis"
    FIGURES_DIR = OUTPUT_DIR / "figures"
    RESULTS_DIR = OUTPUT_DIR / "results"

    # Wind data
    WIND_DATA_PATH = DATA_DIR / "vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt"
    WIND_HEIGHT = 164.0  # meters

    # Turbine layouts and power curves
    LAYOUT_PATH = DATA_DIR / "Turbine_layout_13.csv"
    POWER_CURVES = {
        'Nordex_N164': DATA_DIR / 'Nordex N164.csv',
        'V162_6.2': DATA_DIR / 'V162_6.2.csv',
        'V163_4.5': DATA_DIR / 'V163_4.5.csv'
    }

    # Turbine configurations to analyze
    TURBINE_CONFIGS = [
        {'name': 'Nordex N164', 'file': 'Nordex_N164', 'hub_height': 164, 'rotor_diameter': 164, 'rated_power': 6200},
        {'name': 'V162-6.2 @ 125m', 'file': 'V162_6.2', 'hub_height': 125, 'rotor_diameter': 162, 'rated_power': 6200},
        {'name': 'V162-6.2 @ 145m', 'file': 'V162_6.2', 'hub_height': 145, 'rotor_diameter': 162, 'rated_power': 6200},
        {'name': 'V163-4.5 @ 125m', 'file': 'V163_4.5', 'hub_height': 125, 'rotor_diameter': 163, 'rated_power': 4500},
        {'name': 'V163-4.5 @ 145m', 'file': 'V163_4.5', 'hub_height': 145, 'rotor_diameter': 163, 'rated_power': 4500},
    ]

    # Wind shear coefficient (from shear_estimate.md)
    ALPHA = 0.1846  # Wind shear coefficient (moderately rough terrain)

    # Sector management (allowed wind directions in degrees)
    ALLOWED_SECTORS = [(60, 120), (240, 300)]

    # Weibull bins
    WS_BINS = np.arange(0, 30.5, 0.5)  # 0 to 30 m/s in 0.5 m/s increments


# ============================================================================
# Data Loading
# ============================================================================

def load_wind_data(config: AnalysisConfig) -> pd.DataFrame:
    """
    Load Vortex wind time series data.

    Returns:
        DataFrame with 'ws' (wind speed) and 'wd' (wind direction) columns
        indexed by datetime.
    """
    print(f"Loading wind data from {config.WIND_DATA_PATH}")

    # Read Vortex file directly - it has specific column names
    # Skip first 3 rows (metadata), then header is on row 4 (0-indexed row 3)
    try:
        # Read the file
        df = pd.read_csv(
            config.WIND_DATA_PATH,
            delim_whitespace=True,
            skiprows=3,  # Skip metadata lines
            header=0  # First line after skip is header
        )

        print(f"  Columns found: {df.columns.tolist()}")

        # Create datetime index from YYYYMMDD and HHMM columns
        df['datetime'] = pd.to_datetime(
            df['YYYYMMDD'].astype(str) + df['HHMM'].astype(str).str.zfill(4),
            format='%Y%m%d%H%M'
        )
        df = df.set_index('datetime')

        # Rename columns to standard names
        # M(m/s) is wind speed, D(deg) is wind direction
        df = df.rename(columns={
            'M(m/s)': 'ws',
            'D(deg)': 'wd'
        })

        # Keep only ws and wd columns
        df = df[['ws', 'wd']].copy()

        print(f"✓ Loaded {len(df):,} records from {df.index.min()} to {df.index.max()}")
        print(f"  Mean wind speed: {df['ws'].mean():.2f} m/s")
        print(f"  Data coverage: {len(df) / (11 * 365.25 * 24):.1%} (expected ~11 years hourly)")

        return df

    except Exception as e:
        raise ValueError(f"Failed to load Vortex wind data: {e}")


def load_turbine_power_curves(config: AnalysisConfig) -> Dict[str, pd.DataFrame]:
    """
    Load all turbine power curves from CSV files as DataFrames.

    Returns:
        Dictionary mapping file keys to DataFrames with power curve data.
    """
    print("\nLoading turbine power curves:")

    power_curves = {}

    for file_key, filepath in config.POWER_CURVES.items():
        print(f"  Loading {file_key} from {filepath.name}")

        # Read CSV manually to handle different formats
        df = pd.read_csv(filepath, header=None)
        df.columns = ['ws', 'power', 'ct']

        power_curves[file_key] = df

        print(f"    ✓ Rated power: {df['power'].max():.0f} kW")

    return power_curves


def create_turbine_model(power_curve_df: pd.DataFrame, name: str,
                        hub_height: float, rotor_diameter: float,
                        config: AnalysisConfig) -> TurbineModel:
    """
    Create a TurbineModel instance with specific configuration.

    Args:
        power_curve_df: DataFrame with ws, power, ct columns
        name: Turbine configuration name
        hub_height: Hub height in meters
        rotor_diameter: Rotor diameter in meters
        config: Analysis configuration

    Returns:
        TurbineModel instance
    """
    # Save power curve to temporary file
    temp_path = config.DATA_DIR / f"temp_{name.replace(' ', '_')}.csv"
    power_curve_df.to_csv(temp_path, index=False)

    # Create turbine model with correct specifications
    model = TurbineModel.from_csv(
        temp_path,
        name=name,
        hub_height=hub_height,
        rotor_diameter=rotor_diameter,
        ws_column='ws',
        power_column='power',
        ct_column='ct'
    )

    # Clean up temp file
    temp_path.unlink()

    return model


# ============================================================================
# Wind Statistics and Weibull Fitting
# ============================================================================

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
    # scipy.stats.weibull_min uses shape parameter c (=k) and scale parameter (=A)
    shape, loc, scale = stats.weibull_min.fit(ws_clean, floc=0)

    k = shape  # Shape parameter
    A = scale  # Scale parameter

    # Calculate mean wind speed from Weibull parameters
    # vmean = A * Gamma(1 + 1/k)
    vmean = A * gamma(1 + 1/k)

    return A, k, vmean


def create_wind_histogram(wind_speeds: np.ndarray, bins: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create histogram of wind speed data.

    Args:
        wind_speeds: Array of wind speed values
        bins: Bin edges for histogram

    Returns:
        Tuple of (bin_centers, frequency) where frequency is normalized to sum to 1
    """
    counts, edges = np.histogram(wind_speeds[~np.isnan(wind_speeds)], bins=bins)

    # Normalize to get frequency (probability)
    frequency = counts / counts.sum()

    # Calculate bin centers
    bin_centers = (edges[:-1] + edges[1:]) / 2

    return bin_centers, frequency


def weibull_probability(v: np.ndarray, A: float, k: float) -> np.ndarray:
    """
    Calculate Weibull probability density.

    Args:
        v: Wind speed values
        A: Weibull scale parameter
        k: Weibull shape parameter

    Returns:
        Probability density at each wind speed
    """
    return (k / A) * (v / A) ** (k - 1) * np.exp(-(v / A) ** k)


# ============================================================================
# Wind Speed Height Adjustment
# ============================================================================

def adjust_wind_speed_height(
    wind_speed: pd.Series,
    from_height: float,
    to_height: float,
    alpha: float
) -> pd.Series:
    """
    Adjust wind speed from one height to another using power law.

    V(h) = V(h_ref) * (h / h_ref)^alpha

    Args:
        wind_speed: Wind speed at reference height
        from_height: Reference height (m)
        to_height: Target height (m)
        alpha: Wind shear coefficient

    Returns:
        Adjusted wind speed at target height
    """
    height_ratio = to_height / from_height
    adjusted_ws = wind_speed * (height_ratio ** alpha)

    return adjusted_ws


# ============================================================================
# AEP Calculations
# ============================================================================

def calculate_aep_timeseries(
    wind_speeds: pd.Series,
    turbine_model: TurbineModel,
    n_turbines: int = 13
) -> Dict[str, float]:
    """
    Calculate Annual Energy Production using time series data.

    Args:
        wind_speeds: Time series of wind speeds (m/s)
        turbine_model: TurbineModel with power curve
        n_turbines: Number of turbines in the farm

    Returns:
        Dictionary with AEP metrics:
        - aep_gwh: Annual energy production (GWh/year)
        - full_load_hours: Full load hours (hours/year)
        - capacity_factor: Capacity factor (%)
        - rated_power_mw: Rated power (MW)
    """
    # Get power output for each timestamp
    power_kw = turbine_model.power_at_wind_speed(wind_speeds.values)

    # Calculate total energy (kWh) - hourly data, so each value is kWh
    total_energy_kwh = np.sum(power_kw)

    # Calculate number of years in dataset
    time_span_hours = len(wind_speeds)
    time_span_years = time_span_hours / 8760

    # Annual energy production for one turbine
    aep_single_turbine_gwh = (total_energy_kwh / time_span_years) / 1e6  # Convert to GWh

    # Total farm AEP
    aep_gwh = aep_single_turbine_gwh * n_turbines

    # Rated power
    rated_power_kw = turbine_model.rated_power
    rated_power_mw = rated_power_kw / 1000

    # Full load hours
    full_load_hours = (aep_single_turbine_gwh * 1e6) / rated_power_kw

    # Capacity factor
    capacity_factor = (full_load_hours / 8760) * 100

    return {
        'aep_gwh': aep_gwh,
        'full_load_hours': full_load_hours,
        'capacity_factor': capacity_factor,
        'rated_power_mw': rated_power_mw,
        'n_turbines': n_turbines
    }


def calculate_aep_weibull(
    A: float,
    k: float,
    turbine_model: TurbineModel,
    n_turbines: int = 13,
    hours_per_year: float = 8760
) -> Dict[str, float]:
    """
    Calculate Annual Energy Production using Weibull distribution.

    Args:
        A: Weibull scale parameter
        k: Weibull shape parameter
        turbine_model: TurbineModel with power curve
        n_turbines: Number of turbines
        hours_per_year: Hours in a year

    Returns:
        Dictionary with AEP metrics (same structure as calculate_aep_timeseries)
    """
    # Get power curve
    ws = turbine_model.spec.power_curve['ws'].values
    power = turbine_model.spec.power_curve['power'].values

    # Calculate Weibull probability for each wind speed bin
    # Use midpoints of power curve bins
    prob = weibull_probability(ws, A, k)

    # Calculate wind speed bin widths
    ws_diff = np.diff(ws)
    ws_diff = np.append(ws_diff, ws_diff[-1])  # Extend last bin

    # Average power weighted by Weibull probability
    average_power_kw = np.sum(power * prob * ws_diff)

    # Annual energy for one turbine
    aep_single_turbine_kwh = average_power_kw * hours_per_year
    aep_single_turbine_gwh = aep_single_turbine_kwh / 1e6

    # Total farm AEP
    aep_gwh = aep_single_turbine_gwh * n_turbines

    # Rated power
    rated_power_kw = turbine_model.rated_power
    rated_power_mw = rated_power_kw / 1000

    # Full load hours
    full_load_hours = aep_single_turbine_kwh / rated_power_kw

    # Capacity factor
    capacity_factor = (full_load_hours / hours_per_year) * 100

    return {
        'aep_gwh': aep_gwh,
        'full_load_hours': full_load_hours,
        'capacity_factor': capacity_factor,
        'rated_power_mw': rated_power_mw,
        'n_turbines': n_turbines
    }


# ============================================================================
# Sector Management
# ============================================================================

def filter_by_sectors(
    wind_data: pd.DataFrame,
    allowed_sectors: list
) -> pd.DataFrame:
    """
    Filter wind data to only include allowed wind direction sectors.

    Args:
        wind_data: DataFrame with 'ws' and 'wd' columns
        allowed_sectors: List of (min_deg, max_deg) tuples

    Returns:
        Filtered DataFrame
    """
    mask = pd.Series(False, index=wind_data.index)

    for min_deg, max_deg in allowed_sectors:
        sector_mask = (wind_data['wd'] >= min_deg) & (wind_data['wd'] <= max_deg)
        mask = mask | sector_mask

    filtered_data = wind_data[mask].copy()

    print(f"\nSector management filtering:")
    print(f"  Original records: {len(wind_data):,}")
    print(f"  Filtered records: {len(filtered_data):,}")
    print(f"  Data retention: {len(filtered_data)/len(wind_data):.1%}")

    return filtered_data


# ============================================================================
# Main Analysis
# ============================================================================

def main():
    """Execute complete power curve performance assessment."""

    config = AnalysisConfig()

    print("="*80)
    print("POWER CURVE PERFORMANCE ASSESSMENT")
    print("="*80)

    # -------------------------------------------------------------------------
    # Phase 1: Load Data
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 1: DATA LOADING")
    print("="*80)

    wind_data = load_wind_data(config)
    power_curves = load_turbine_power_curves(config)

    # -------------------------------------------------------------------------
    # Phase 2: Wind Statistics and Weibull Fitting
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 2: WIND STATISTICS AND WEIBULL FITTING")
    print("="*80)

    print("\nCalculating Weibull parameters...")
    A, k, vmean_weibull = calculate_weibull_parameters(wind_data['ws'].values)
    vmean_measured = wind_data['ws'].mean()

    print(f"\nWeibull Parameters:")
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
    print(f"\n✓ Saved wind statistics to {config.RESULTS_DIR / 'wind_statistics.csv'}")

    # -------------------------------------------------------------------------
    # Phase 3: AEP Calculations for All Configurations
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 3: AEP CALCULATIONS")
    print("="*80)

    # Prepare results storage
    results_timeseries = []
    results_weibull = []

    for turbine_config in config.TURBINE_CONFIGS:
        print(f"\nAnalyzing: {turbine_config['name']}")

        # Create turbine model with specific hub height and rotor diameter
        power_curve_df = power_curves[turbine_config['file']]
        turbine_model = create_turbine_model(
            power_curve_df,
            name=turbine_config['name'],
            hub_height=turbine_config['hub_height'],
            rotor_diameter=turbine_config['rotor_diameter'],
            config=config
        )

        # Adjust wind speed to hub height
        ws_adjusted = adjust_wind_speed_height(
            wind_data['ws'],
            from_height=config.WIND_HEIGHT,
            to_height=turbine_config['hub_height'],
            alpha=config.ALPHA
        )

        print(f"  Hub height: {turbine_config['hub_height']}m")
        print(f"  Adjusted mean WS: {ws_adjusted.mean():.3f} m/s")

        # Calculate AEP using time series
        aep_ts = calculate_aep_timeseries(ws_adjusted, turbine_model, n_turbines=13)

        results_timeseries.append({
            'Configuration': turbine_config['name'],
            'AEP (GWh/yr)': aep_ts['aep_gwh'],
            'Full Load Hours (hr/yr)': aep_ts['full_load_hours'],
            'Capacity Factor (%)': aep_ts['capacity_factor'],
            'Rated Power (MW)': aep_ts['rated_power_mw'],
            'Normalized AEP': 0.0  # Will be filled later
        })

        # Calculate Weibull parameters for adjusted wind speed
        A_adj, k_adj, _ = calculate_weibull_parameters(ws_adjusted.values)

        # Calculate AEP using Weibull
        aep_wb = calculate_aep_weibull(A_adj, k_adj, turbine_model, n_turbines=13)

        results_weibull.append({
            'Configuration': turbine_config['name'],
            'AEP (GWh/yr)': aep_wb['aep_gwh'],
            'Full Load Hours (hr/yr)': aep_wb['full_load_hours'],
            'Capacity Factor (%)': aep_wb['capacity_factor'],
            'Rated Power (MW)': aep_wb['rated_power_mw'],
            'Normalized AEP': 0.0  # Will be filled later
        })

        print(f"  Time Series AEP: {aep_ts['aep_gwh']:.2f} GWh/yr | CF: {aep_ts['capacity_factor']:.1f}%")
        print(f"  Weibull AEP:     {aep_wb['aep_gwh']:.2f} GWh/yr | CF: {aep_wb['capacity_factor']:.1f}%")

    # Convert to DataFrames
    df_ts = pd.DataFrame(results_timeseries)
    df_wb = pd.DataFrame(results_weibull)

    # Normalize to Nordex N164 (first configuration)
    baseline_aep_ts = df_ts.loc[0, 'AEP (GWh/yr)']
    baseline_aep_wb = df_wb.loc[0, 'AEP (GWh/yr)']

    df_ts['Normalized AEP'] = df_ts['AEP (GWh/yr)'] / baseline_aep_ts
    df_wb['Normalized AEP'] = df_wb['AEP (GWh/yr)'] / baseline_aep_wb

    # Save results
    df_ts.to_csv(config.RESULTS_DIR / 'table_1_timeseries_aep.csv', index=False)
    df_wb.to_csv(config.RESULTS_DIR / 'table_2_weibull_aep.csv', index=False)

    print("\n" + "="*80)
    print("TABLE 1: TIME SERIES AEP RESULTS")
    print("="*80)
    print(df_ts.to_string(index=False))

    print("\n" + "="*80)
    print("TABLE 2: WEIBULL AEP RESULTS")
    print("="*80)
    print(df_wb.to_string(index=False))

    # -------------------------------------------------------------------------
    # Phase 4: Sector Management Analysis
    # -------------------------------------------------------------------------
    print("\n" + "="*80)
    print("PHASE 4: SECTOR MANAGEMENT ANALYSIS")
    print("="*80)

    # Filter wind data by sectors
    wind_data_sectors = filter_by_sectors(wind_data, config.ALLOWED_SECTORS)

    results_sectors = []

    for turbine_config in config.TURBINE_CONFIGS:
        print(f"\nAnalyzing with sector management: {turbine_config['name']}")

        # Create turbine model with specific hub height and rotor diameter
        power_curve_df = power_curves[turbine_config['file']]
        turbine_model = create_turbine_model(
            power_curve_df,
            name=turbine_config['name'],
            hub_height=turbine_config['hub_height'],
            rotor_diameter=turbine_config['rotor_diameter'],
            config=config
        )

        # Adjust wind speed to hub height
        ws_adjusted = adjust_wind_speed_height(
            wind_data_sectors['ws'],
            from_height=config.WIND_HEIGHT,
            to_height=turbine_config['hub_height'],
            alpha=config.ALPHA
        )

        # Calculate AEP with sector filtering
        aep_sector = calculate_aep_timeseries(ws_adjusted, turbine_model, n_turbines=13)

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

    # Save results
    df_sectors.to_csv(config.RESULTS_DIR / 'table_3_sector_management_aep.csv', index=False)

    print("\n" + "="*80)
    print("TABLE 3: SECTOR MANAGEMENT AEP RESULTS")
    print("="*80)
    print(df_sectors.to_string(index=False))

    # Calculate curtailment
    print("\n" + "="*80)
    print("SECTOR MANAGEMENT IMPACT")
    print("="*80)
    for i, config_item in enumerate(config.TURBINE_CONFIGS):
        curtailment = (1 - df_sectors.loc[i, 'AEP (GWh/yr)'] / df_ts.loc[i, 'AEP (GWh/yr)']) * 100
        print(f"{config_item['name']}: {curtailment:.1f}% production loss due to sector management")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nResults saved to: {config.RESULTS_DIR}")
    print("  - wind_statistics.csv")
    print("  - table_1_timeseries_aep.csv")
    print("  - table_2_weibull_aep.csv")
    print("  - table_3_sector_management_aep.csv")


if __name__ == '__main__':
    main()
