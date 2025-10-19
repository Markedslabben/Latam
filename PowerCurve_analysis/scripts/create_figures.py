"""
Create all figures for power curve analysis with validation plots.

Figure 1: Wind speed histogram + Weibull fit + Power curves (dual y-axes)
Validation plots for each analysis phase
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.special import gamma

# Add latam_hybrid to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'latam_hybrid'))

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10


def load_results(results_dir: Path):
    """Load all analysis results."""

    wind_stats = pd.read_csv(results_dir / 'wind_statistics.csv')
    table1 = pd.read_csv(results_dir / 'table1_timeseries_aep.csv')
    table2 = pd.read_csv(results_dir / 'table2_weibull_aep.csv')
    table3 = pd.read_csv(results_dir / 'table3_sector_management_aep.csv')

    return wind_stats, table1, table2, table3


def load_wind_data(data_path: Path):
    """Load wind data for plotting."""

    df = pd.read_csv(
        data_path,
        sep=r'\s+',
        skiprows=3,
        header=0
    )

    # Create datetime index
    df['datetime'] = pd.to_datetime(
        df['YYYYMMDD'].astype(str) + ' ' + df['HHMM'].astype(str).str.zfill(4),
        format='%Y%m%d %H%M'
    )
    df = df.set_index('datetime')

    # Rename columns
    df = df.rename(columns={
        'M(m/s)': 'ws',
        'D(deg)': 'wd',
    })

    return df[['ws', 'wd']]


def load_power_curves(data_dir: Path):
    """Load all power curves."""

    power_curves = {}

    # Nordex N164
    df = pd.read_csv(data_dir / 'Nordex N164.csv', header=None, names=['ws', 'power', 'ct'])
    power_curves['Nordex N164'] = df

    # V162-6.2
    df = pd.read_csv(data_dir / 'V162_6.2.csv', header=None, names=['ws', 'power', 'ct'])
    power_curves['V162-6.2'] = df

    # V163-4.5
    df = pd.read_csv(data_dir / 'V163_4.5.csv', header=None, names=['ws', 'power', 'ct'])
    power_curves['V163-4.5'] = df

    return power_curves


def create_figure1_dual_axis(wind_data, wind_stats, power_curves, figures_dir):
    """
    Create Figure 1: Wind speed histogram + Weibull + Power curves.

    Dual y-axes:
    - Left axis: Frequency (histogram and Weibull)
    - Right axis: Power in kW (power curves)
    """

    fig, ax1 = plt.subplots(figsize=(16, 10))

    # Extract Weibull parameters
    A = wind_stats[wind_stats['Parameter'] == 'Weibull A (m/s)']['Value'].values[0]
    k = wind_stats[wind_stats['Parameter'] == 'Weibull k']['Value'].values[0]

    # Wind speed data
    ws = wind_data['ws'].values

    # =========================================================================
    # LEFT Y-AXIS: FREQUENCY (Histogram and Weibull)
    # =========================================================================

    # Create histogram with many bins for precision
    n_bins = 60  # Fine resolution: 0.5 m/s bins from 0-30 m/s
    counts, bin_edges, patches = ax1.hist(
        ws,
        bins=n_bins,
        range=(0, 30),
        density=True,  # Normalize to probability density
        alpha=0.6,
        color='steelblue',
        edgecolor='black',
        linewidth=0.5,
        label='Measured wind speed distribution'
    )

    # Plot Weibull fit on same axis
    ws_weibull = np.linspace(0, 30, 500)
    weibull_pdf = stats.weibull_min.pdf(ws_weibull, k, scale=A)

    ax1.plot(
        ws_weibull,
        weibull_pdf,
        'r-',
        linewidth=3,
        label=f'Weibull fit (A={A:.2f} m/s, k={k:.2f})',
        zorder=5
    )

    # Left y-axis labels
    ax1.set_xlabel('Wind Speed (m/s)', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Frequency (Probability Density)', fontsize=14, fontweight='bold', color='steelblue')
    ax1.tick_params(axis='y', labelcolor='steelblue')
    ax1.grid(True, alpha=0.3)

    # =========================================================================
    # RIGHT Y-AXIS: POWER CURVES (kW)
    # =========================================================================

    ax2 = ax1.twinx()

    # Color scheme for power curves
    colors = {
        'Nordex N164': '#2E7D32',      # Dark green
        'V162-6.2': '#1976D2',          # Blue
        'V163-4.5': '#F57C00',          # Orange
    }

    linestyles = {
        'Nordex N164': '-',
        'V162-6.2': '--',
        'V163-4.5': '-.',
    }

    # Plot power curves
    for turbine_name, pc_df in power_curves.items():
        ax2.plot(
            pc_df['ws'],
            pc_df['power'],
            linestyle=linestyles[turbine_name],
            linewidth=2.5,
            color=colors[turbine_name],
            label=f'{turbine_name} power curve',
            zorder=10
        )

    # Right y-axis labels
    ax2.set_ylabel('Power Output (kW)', fontsize=14, fontweight='bold', color='darkgreen')
    ax2.tick_params(axis='y', labelcolor='darkgreen')

    # =========================================================================
    # FORMATTING
    # =========================================================================

    # Title
    plt.title(
        'Figure 1: Wind Speed Distribution, Weibull Fit, and Turbine Power Curves\n'
        f'Site: Dominican Republic, Hub Height: 164m, Data: {len(ws)} hourly records',
        fontsize=16,
        fontweight='bold',
        pad=20
    )

    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc='upper right',
        fontsize=11,
        framealpha=0.95,
        edgecolor='black'
    )

    # Set x-axis limits
    ax1.set_xlim(0, 30)

    # Add text box with statistics
    stats_text = (
        f'Wind Statistics:\n'
        f'Mean: {ws.mean():.2f} m/s\n'
        f'Std: {ws.std():.2f} m/s\n'
        f'Max: {ws.max():.2f} m/s\n'
        f'Data points: {len(ws):,}'
    )

    ax1.text(
        0.02, 0.98,
        stats_text,
        transform=ax1.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    )

    plt.tight_layout()

    # Save figure
    output_path = figures_dir / 'figure1_wind_distribution_power_curves.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved Figure 1 to {output_path}")

    plt.close()


def create_validation_weibull_fit(wind_data, wind_stats, figures_dir):
    """Validation: Q-Q plot to check Weibull fit quality."""

    A = wind_stats[wind_stats['Parameter'] == 'Weibull A (m/s)']['Value'].values[0]
    k = wind_stats[wind_stats['Parameter'] == 'Weibull k']['Value'].values[0]

    ws = wind_data['ws'].values
    ws_clean = ws[ws > 0]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Q-Q plot
    theoretical_quantiles = stats.weibull_min.ppf(
        np.linspace(0.01, 0.99, 100),
        k,
        scale=A
    )

    sample_quantiles = np.percentile(ws_clean, np.linspace(1, 99, 100))

    ax1.scatter(theoretical_quantiles, sample_quantiles, alpha=0.5, s=30)
    ax1.plot([0, 30], [0, 30], 'r--', label='Perfect fit')
    ax1.set_xlabel('Theoretical Quantiles (Weibull)', fontsize=12)
    ax1.set_ylabel('Sample Quantiles (Measured)', fontsize=12)
    ax1.set_title('Q-Q Plot: Weibull Fit Quality', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # CDF comparison
    sorted_ws = np.sort(ws_clean)
    empirical_cdf = np.arange(1, len(sorted_ws) + 1) / len(sorted_ws)
    theoretical_cdf = stats.weibull_min.cdf(sorted_ws, k, scale=A)

    ax2.plot(sorted_ws, empirical_cdf, 'b-', label='Empirical CDF', linewidth=2, alpha=0.7)
    ax2.plot(sorted_ws, theoretical_cdf, 'r--', label='Weibull CDF', linewidth=2)
    ax2.set_xlabel('Wind Speed (m/s)', fontsize=12)
    ax2.set_ylabel('Cumulative Probability', fontsize=12)
    ax2.set_title('CDF Comparison', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.suptitle('Validation: Weibull Distribution Fit Quality', fontsize=16, fontweight='bold')
    plt.tight_layout()

    output_path = figures_dir / 'validation_weibull_fit.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved Weibull validation to {output_path}")

    plt.close()


def create_validation_wind_rose(wind_data, figures_dir):
    """Validation: Wind rose to visualize directional distribution."""

    from matplotlib import cm

    fig = plt.figure(figsize=(12, 12))
    ax = fig.add_subplot(111, projection='polar')

    # Convert wind direction to radians
    wd_rad = np.deg2rad(wind_data['wd'].values)
    ws = wind_data['ws'].values

    # Create wind rose bins
    n_dir_bins = 16  # 16 direction sectors (22.5° each)
    n_speed_bins = 6

    dir_bins = np.linspace(0, 2*np.pi, n_dir_bins + 1)
    speed_bins = np.linspace(0, ws.max(), n_speed_bins + 1)

    # Create histogram
    width = 2 * np.pi / n_dir_bins

    # Colors for speed ranges
    colors = cm.YlOrRd(np.linspace(0.3, 0.9, n_speed_bins))

    for i in range(n_speed_bins):
        # Filter by speed range
        mask = (ws >= speed_bins[i]) & (ws < speed_bins[i+1])
        wd_filtered = wd_rad[mask]

        if len(wd_filtered) == 0:
            continue

        # Count occurrences in each direction bin
        counts, _ = np.histogram(wd_filtered, bins=dir_bins)

        # Convert to percentage
        percentages = counts / len(wd_rad) * 100

        # Plot bars
        theta = dir_bins[:-1]
        ax.bar(
            theta,
            percentages,
            width=width,
            bottom=0.0 if i == 0 else ax.patches[-n_dir_bins].get_height() if i > 0 else 0,
            color=colors[i],
            edgecolor='white',
            linewidth=0.5,
            label=f'{speed_bins[i]:.1f}-{speed_bins[i+1]:.1f} m/s',
            alpha=0.8
        )

    # Formatting
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_title('Wind Rose: Directional Distribution\n', fontsize=16, fontweight='bold', pad=20)

    # Add sector management zones
    sector1 = [(60, 120)]
    sector2 = [(240, 300)]

    for s_min, s_max in sector1 + sector2:
        ax.axvline(np.deg2rad(s_min), color='green', linestyle='--', linewidth=2, alpha=0.7)
        ax.axvline(np.deg2rad(s_max), color='green', linestyle='--', linewidth=2, alpha=0.7)

    ax.text(0.5, 1.08, 'Green dashed lines: Allowed sectors (60-120°, 240-300°)',
            ha='center', transform=ax.transAxes, fontsize=11, color='green', fontweight='bold')

    ax.legend(loc='upper left', bbox_to_anchor=(1.1, 1.0), fontsize=10)

    plt.tight_layout()

    output_path = figures_dir / 'validation_wind_rose.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved wind rose to {output_path}")

    plt.close()


def create_validation_shear_profile(figures_dir):
    """Validation: Wind shear profile visualization."""

    # Shear coefficient from analysis
    alpha = 0.1846

    # Reference height and wind speed
    h_ref = 164.0  # m
    v_ref = 6.61   # m/s (from analysis)

    # Heights to plot
    heights = np.linspace(50, 200, 100)

    # Calculate wind speeds using power law
    wind_speeds = v_ref * (heights / h_ref) ** alpha

    fig, ax = plt.subplots(figsize=(10, 8))

    ax.plot(wind_speeds, heights, 'b-', linewidth=3, label=f'Power law (α={alpha:.4f})')

    # Mark hub heights
    hub_heights = [125, 145, 164]
    hub_names = ['V162/V163 @ 125m', 'V162/V163 @ 145m', 'Nordex N164 @ 164m']
    colors = ['orange', 'blue', 'green']

    for h, name, color in zip(hub_heights, hub_names, colors):
        v = v_ref * (h / h_ref) ** alpha
        ax.plot(v, h, 'o', markersize=12, color=color, label=name, zorder=10)
        ax.axhline(h, color=color, linestyle='--', alpha=0.3)

    # Mark reference point
    ax.plot(v_ref, h_ref, 's', markersize=15, color='red', label='Reference measurement', zorder=11)

    ax.set_xlabel('Wind Speed (m/s)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Height Above Ground (m)', fontsize=14, fontweight='bold')
    ax.set_title(f'Validation: Wind Shear Profile\n'
                 f'Power Law with α = {alpha:.4f} (Moderately Rough Terrain)',
                 fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', fontsize=11)

    plt.tight_layout()

    output_path = figures_dir / 'validation_shear_profile.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved shear profile to {output_path}")

    plt.close()


def create_comparison_chart(table1, table2, table3, figures_dir):
    """Create comparison bar chart for all three analysis methods."""

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    x = np.arange(len(table1))
    width = 0.25

    # Panel 1: AEP Comparison
    ax = axes[0, 0]
    ax.bar(x - width, table1['AEP (GWh/yr)'], width, label='Time Series', alpha=0.8)
    ax.bar(x, table2['AEP (GWh/yr)'], width, label='Weibull', alpha=0.8)
    ax.bar(x + width, table3['AEP (GWh/yr)'], width, label='Sector Mgmt', alpha=0.8)
    ax.set_ylabel('AEP (GWh/yr)', fontweight='bold')
    ax.set_title('Annual Energy Production Comparison', fontweight='bold', fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(table1['Configuration'], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Panel 2: Capacity Factor
    ax = axes[0, 1]
    ax.bar(x - width, table1['Capacity Factor (%)'], width, label='Time Series', alpha=0.8)
    ax.bar(x, table2['Capacity Factor (%)'], width, label='Weibull', alpha=0.8)
    ax.bar(x + width, table3['Capacity Factor (%)'], width, label='Sector Mgmt', alpha=0.8)
    ax.set_ylabel('Capacity Factor (%)', fontweight='bold')
    ax.set_title('Capacity Factor Comparison', fontweight='bold', fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(table1['Configuration'], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Panel 3: Full Load Hours
    ax = axes[1, 0]
    ax.bar(x - width, table1['Full Load Hours (hr/yr)'], width, label='Time Series', alpha=0.8)
    ax.bar(x, table2['Full Load Hours (hr/yr)'], width, label='Weibull', alpha=0.8)
    ax.bar(x + width, table3['Full Load Hours (hr/yr)'], width, label='Sector Mgmt', alpha=0.8)
    ax.set_ylabel('Full Load Hours (hr/yr)', fontweight='bold')
    ax.set_title('Full Load Hours Comparison', fontweight='bold', fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(table1['Configuration'], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Panel 4: Normalized AEP
    ax = axes[1, 1]
    ax.bar(x - width, table1['Normalized AEP'], width, label='Time Series', alpha=0.8)
    ax.bar(x, table2['Normalized AEP'], width, label='Weibull', alpha=0.8)
    ax.bar(x + width, table3['Normalized AEP'], width, label='Sector Mgmt', alpha=0.8)
    ax.axhline(1.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Nordex N164 baseline')
    ax.set_ylabel('Normalized AEP (relative to Nordex N164)', fontweight='bold')
    ax.set_title('Normalized Production Comparison', fontweight='bold', fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(table1['Configuration'], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle('Power Curve Performance Comparison: All Analysis Methods',
                 fontsize=18, fontweight='bold')
    plt.tight_layout()

    output_path = figures_dir / 'figure2_performance_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved comparison chart to {output_path}")

    plt.close()


def main():
    """Create all figures."""

    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "latam_hybrid" / "Inputdata"
    results_dir = project_root / "PowerCurve_analysis" / "results"
    figures_dir = project_root / "PowerCurve_analysis" / "figures"

    figures_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("CREATING FIGURES AND VALIDATION PLOTS")
    print("=" * 80)

    # Load data
    print("\nLoading data...")
    wind_stats, table1, table2, table3 = load_results(results_dir)
    wind_data = load_wind_data(data_dir / "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
    power_curves = load_power_curves(data_dir)

    print("\nCreating figures...")

    # Main Figure 1: Dual-axis plot
    print("\n1. Creating Figure 1 (dual-axis: frequency + power curves)...")
    create_figure1_dual_axis(wind_data, wind_stats, power_curves, figures_dir)

    # Validation plots
    print("\n2. Creating validation: Weibull fit quality...")
    create_validation_weibull_fit(wind_data, wind_stats, figures_dir)

    print("\n3. Creating validation: Wind rose...")
    create_validation_wind_rose(wind_data, figures_dir)

    print("\n4. Creating validation: Shear profile...")
    create_validation_shear_profile(figures_dir)

    # Comparison chart
    print("\n5. Creating Figure 2: Performance comparison...")
    create_comparison_chart(table1, table2, table3, figures_dir)

    print("\n" + "=" * 80)
    print("ALL FIGURES CREATED SUCCESSFULLY")
    print("=" * 80)
    print(f"Output directory: {figures_dir}")
    print("\nCreated files:")
    for f in sorted(figures_dir.glob("*.png")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
