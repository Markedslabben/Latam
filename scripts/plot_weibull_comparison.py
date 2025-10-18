"""
Compare omnidirectional vs frequency-weighted Weibull distributions.
Explains why k parameters differ between approaches.
"""

import sys
import os

# Get the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from site_galvian.create_site import create_site_from_vortex, create_wind_distribution
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.stats import weibull_min
from scipy.special import gamma
import pandas as pd

def weibull_pdf(ws, A, k):
    """Calculate Weibull probability density function."""
    return weibull_min.pdf(ws, k, loc=0, scale=A)

def main():
    print("Loading 10-year wind data...")
    time_site = create_site_from_vortex(
        "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt",
        start="2014-01-01 00:00",
        end="2024-12-31 23:59",
        include_leap_year=False
    )

    # Get all wind speeds
    all_ws = time_site.ds.wind_speed.values

    # Calculate sector-based parameters
    print("Calculating sector-based Weibull parameters...")
    freq, A_sectors, k_sectors, wd_centers, TI, weibull_fits = create_wind_distribution(
        time_site,
        n_sectors=12
    )

    # Calculate omnidirectional parameters (from all data)
    print("Calculating omnidirectional Weibull parameters...")
    c_all, loc_all, scale_all = weibull_min.fit(all_ws, floc=0)
    A_omni = scale_all
    k_omni = c_all

    # Calculate frequency-weighted average parameters
    A_weighted = np.sum(freq * A_sectors)
    k_weighted = np.sum(freq * k_sectors)

    print("\n" + "="*80)
    print("WEIBULL PARAMETER COMPARISON")
    print("="*80)
    print(f"\n1. OMNIDIRECTIONAL (fitted to all wind speeds):")
    print(f"   A = {A_omni:.3f} m/s")
    print(f"   k = {k_omni:.3f}")
    print(f"\n2. FREQUENCY-WEIGHTED AVERAGE (average of sector parameters):")
    print(f"   A = {A_weighted:.3f} m/s")
    print(f"   k = {k_weighted:.3f}")
    print(f"\n3. DIFFERENCE:")
    print(f"   Delta A = {abs(A_omni - A_weighted):.3f} m/s ({abs(A_omni - A_weighted)/A_omni*100:.1f}%)")
    print(f"   Delta k = {abs(k_omni - k_weighted):.3f} ({abs(k_omni - k_weighted)/k_omni*100:.1f}%)")
    print("\n" + "="*80)

    print("\nWHY THE DIFFERENCE IN k?")
    print("="*80)
    print("• Omnidirectional k is LOWER (2.226) because:")
    print("  - Fits ONE distribution to ALL wind speeds from all directions")
    print("  - Captures full variability including differences BETWEEN sectors")
    print("  - Mixing sectors with different mean speeds creates more spread")
    print("\n• Frequency-weighted k is HIGHER (3.029) because:")
    print("  - Averages k from individual sectors (each sector is more consistent)")
    print("  - Each sector has less variability WITHIN itself")
    print("  - Loses information about differences BETWEEN sectors")
    print("\n• Both account for direction frequency:")
    print("  - Omnidirectional: implicitly (more data points from frequent directions)")
    print("  - Weighted: explicitly (freq used as weights in averaging)")
    print("="*80)

    # Create comprehensive comparison plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Wind speed range for plotting
    ws_range = np.linspace(0, 25, 500)

    # Plot 1: Histogram + Both Weibull fits
    ax1 = axes[0, 0]
    ax1.hist(all_ws, bins=50, density=True, alpha=0.6, color='gray',
             label='Measured data', edgecolor='black')
    ax1.plot(ws_range, weibull_pdf(ws_range, A_omni, k_omni),
             'r-', linewidth=2.5, label=f'Omnidirectional\n(A={A_omni:.2f}, k={k_omni:.2f})')
    ax1.plot(ws_range, weibull_pdf(ws_range, A_weighted, k_weighted),
             'b--', linewidth=2.5, label=f'Frequency-weighted\n(A={A_weighted:.2f}, k={k_weighted:.2f})')
    ax1.set_xlabel('Wind Speed (m/s)', fontsize=11)
    ax1.set_ylabel('Probability Density', fontsize=11)
    ax1.set_title('Comparison: Omnidirectional vs Frequency-Weighted Weibull', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 25)

    # Plot 2: Cumulative Distribution Function
    ax2 = axes[0, 1]
    sorted_ws = np.sort(all_ws)
    cumulative = np.arange(1, len(sorted_ws) + 1) / len(sorted_ws)
    ax2.plot(sorted_ws, cumulative, 'gray', linewidth=1.5, label='Measured data', alpha=0.7)
    ax2.plot(ws_range, weibull_min.cdf(ws_range, k_omni, loc=0, scale=A_omni),
             'r-', linewidth=2.5, label=f'Omnidirectional (k={k_omni:.2f})')
    ax2.plot(ws_range, weibull_min.cdf(ws_range, k_weighted, loc=0, scale=A_weighted),
             'b--', linewidth=2.5, label=f'Freq-weighted (k={k_weighted:.2f})')
    ax2.set_xlabel('Wind Speed (m/s)', fontsize=11)
    ax2.set_ylabel('Cumulative Probability', fontsize=11)
    ax2.set_title('Cumulative Distribution Function', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 25)

    # Plot 3: Sector k parameters to show why weighted average is higher
    ax3 = axes[1, 0]
    x_pos = np.arange(len(k_sectors))
    colors = ['green' if f > 0.1 else 'lightblue' for f in freq]
    bars = ax3.bar(x_pos, k_sectors, color=colors, edgecolor='black', alpha=0.7)
    ax3.axhline(y=k_omni, color='r', linestyle='-', linewidth=2.5,
                label=f'Omnidirectional k={k_omni:.2f}')
    ax3.axhline(y=k_weighted, color='b', linestyle='--', linewidth=2.5,
                label=f'Weighted avg k={k_weighted:.2f}')
    ax3.set_xlabel('Sector Number', fontsize=11)
    ax3.set_ylabel('Shape Parameter k', fontsize=11)
    ax3.set_title('k Parameter by Sector (Green = High Frequency)', fontsize=12, fontweight='bold')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels([f'{i+1}\n{int(wd_centers[i])}°' for i in range(len(k_sectors))], fontsize=9)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Sector A parameters with frequency
    ax4 = axes[1, 1]
    ax4_twin = ax4.twinx()

    bars = ax4.bar(x_pos, A_sectors, color=colors, edgecolor='black', alpha=0.7, label='A (scale)')
    ax4.axhline(y=A_omni, color='r', linestyle='-', linewidth=2.5,
                label=f'Omnidirectional A={A_omni:.2f}')
    ax4.axhline(y=A_weighted, color='b', linestyle='--', linewidth=2.5,
                label=f'Weighted avg A={A_weighted:.2f}')

    line = ax4_twin.plot(x_pos, freq * 100, 'ko-', linewidth=2, markersize=6,
                         label='Frequency (%)')

    ax4.set_xlabel('Sector Number', fontsize=11)
    ax4.set_ylabel('Scale Parameter A (m/s)', fontsize=11, color='black')
    ax4_twin.set_ylabel('Frequency (%)', fontsize=11, color='black')
    ax4.set_title('A Parameter by Sector with Frequency', fontsize=12, fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f'{i+1}\n{int(wd_centers[i])}°' for i in range(len(A_sectors))], fontsize=9)

    # Combine legends
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc='upper right')

    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # Save plot
    output_path = 'plots/weibull_comparison_omni_vs_weighted.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    plt.close()

    # Create summary table
    print("\n" + "="*80)
    print("SECTOR DETAILS")
    print("="*80)
    summary_data = []
    for i in range(len(k_sectors)):
        summary_data.append({
            'Sector': i + 1,
            'Direction': f"{int(wd_centers[i])}°",
            'Frequency (%)': f"{freq[i]*100:.2f}",
            'A (m/s)': f"{A_sectors[i]:.3f}",
            'k': f"{k_sectors[i]:.3f}",
            'Mean WS (m/s)': f"{A_sectors[i] * gamma(1 + 1/k_sectors[i]):.2f}"
        })

    df_summary = pd.DataFrame(summary_data)
    print(df_summary.to_string(index=False))
    print("="*80)

if __name__ == "__main__":
    main()
