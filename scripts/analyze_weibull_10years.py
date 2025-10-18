"""
Analyze 10 years of wind data to calculate Weibull distribution parameters.
Calculates A (scale) and k (shape) parameters aggregated across all sectors.
"""

import sys
import os

# Get the project root directory (parent of scripts folder)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from site_galvian.create_site import create_site_from_vortex, create_wind_distribution
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def analyze_10year_weibull(n_sectors=12, include_leap_year=False):
    """
    Analyze 10 years of wind data and compute Weibull parameters.

    Args:
        n_sectors (int): Number of wind direction sectors
        include_leap_year (bool): Whether to include Feb 29th data

    Returns:
        dict: Dictionary containing Weibull parameters and statistics
    """
    print("=" * 80)
    print("10-YEAR WIND DISTRIBUTION ANALYSIS (2014-2024)")
    print("=" * 80)
    print(f"Data source: Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
    print(f"Number of sectors: {n_sectors}")
    print(f"Include leap years: {include_leap_year}")
    print()

    # Load full 10-year dataset (2014-2024)
    print("Loading 10 years of wind data...")
    time_site = create_site_from_vortex(
        "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt",
        start="2014-01-01 00:00",
        end="2024-12-31 23:59",
        include_leap_year=include_leap_year
    )

    total_hours = len(time_site.ds.wind_speed.values)
    print(f"Total data points: {total_hours:,} hours")
    print(f"Expected hours: {10 * 365 * 24:,} (10 years without leap days)")
    print()

    # Calculate Weibull parameters for each sector
    print("Calculating Weibull distribution parameters per sector...")
    freq, A, k, wd_centers, TI, weibull_fits = create_wind_distribution(
        time_site,
        n_sectors=n_sectors
    )

    # Calculate overall (omnidirectional) Weibull parameters
    print("\nCalculating omnidirectional (all sectors combined) parameters...")
    all_ws = time_site.ds.wind_speed.values
    import scipy.stats
    c_all, loc_all, scale_all = scipy.stats.weibull_min.fit(all_ws, floc=0)
    A_all = scale_all
    k_all = c_all

    # Calculate statistics
    mean_ws = np.mean(all_ws)
    median_ws = np.median(all_ws)
    std_ws = np.std(all_ws)

    print()
    print("=" * 80)
    print("OMNIDIRECTIONAL WEIBULL PARAMETERS (ALL SECTORS COMBINED)")
    print("=" * 80)
    print(f"Weibull A (scale parameter): {A_all:.3f} m/s")
    print(f"Weibull k (shape parameter): {k_all:.3f}")
    print()
    print("Wind Speed Statistics:")
    print(f"  Mean wind speed: {mean_ws:.3f} m/s")
    print(f"  Median wind speed: {median_ws:.3f} m/s")
    print(f"  Std deviation: {std_ws:.3f} m/s")
    print()

    # Print sector-by-sector results
    print("=" * 80)
    print("WEIBULL PARAMETERS BY SECTOR")
    print("=" * 80)
    print(f"{'Sector':<8} {'Dir (°)':<10} {'Freq (%)':<10} {'A (m/s)':<10} {'k':<10} {'TI':<10}")
    print("-" * 80)

    for i in range(n_sectors):
        sector_name = f"{i+1}"
        dir_range = f"{wd_centers[i]:.0f}"
        freq_pct = freq[i] * 100
        print(f"{sector_name:<8} {dir_range:<10} {freq_pct:<10.2f} {A[i]:<10.3f} {k[i]:<10.3f} {TI[i]:<10.3f}")

    print("-" * 80)
    print(f"{'TOTAL':<8} {'ALL':<10} {100.0:<10.2f} {A_all:<10.3f} {k_all:<10.3f} {'-':<10}")
    print()

    # Calculate weighted average parameters
    A_weighted = np.sum(freq * A)
    k_weighted = np.sum(freq * k)

    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Frequency-weighted average A: {A_weighted:.3f} m/s")
    print(f"Frequency-weighted average k: {k_weighted:.3f}")
    print()
    print(f"Most frequent sector: {np.argmax(freq)+1} ({wd_centers[np.argmax(freq)]:.0f}°) at {freq[np.argmax(freq)]*100:.2f}%")
    print(f"Least frequent sector: {np.argmin(freq)+1} ({wd_centers[np.argmin(freq)]:.0f}°) at {freq[np.argmin(freq)]*100:.2f}%")
    print(f"Highest A: Sector {np.argmax(A)+1} ({wd_centers[np.argmax(A)]:.0f}°) with A={np.max(A):.3f} m/s")
    print(f"Lowest A: Sector {np.argmin(A)+1} ({wd_centers[np.argmin(A)]:.0f}°) with A={np.min(A):.3f} m/s")
    print()

    # Create results dictionary
    results = {
        'omnidirectional': {
            'A': A_all,
            'k': k_all,
            'mean_ws': mean_ws,
            'median_ws': median_ws,
            'std_ws': std_ws
        },
        'by_sector': {
            'frequency': freq,
            'A': A,
            'k': k,
            'wd_centers': wd_centers,
            'TI': TI
        },
        'weighted_average': {
            'A': A_weighted,
            'k': k_weighted
        },
        'total_hours': total_hours
    }

    return results, time_site

if __name__ == "__main__":
    results, time_site = analyze_10year_weibull(n_sectors=12, include_leap_year=False)

    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)
