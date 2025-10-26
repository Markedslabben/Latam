"""
Create per-turbine production graphs showing losses for each turbine in the layout.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Paths
results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
figures_dir = os.path.join(os.path.dirname(__file__), '..', 'figures')
os.makedirs(figures_dir, exist_ok=True)

# Configuration mapping
configs = {
    'Nordex_N164_164m': 'Nordex N164 @ 164m',
    'V162-6.2_145m': 'Vestas V162-6.2 @ 145m',
    'V163-4.5_145m': 'Vestas V163-4.5 @ 145m',
    'V162-6.2_125m': 'Vestas V162-6.2 @ 125m',
    'V163-4.5_125m': 'Vestas V163-4.5 @ 125m'
}

colors = {
    'net': '#4CAF50',
    'wake': '#FF9800',
    'sector': '#F44336',
    'other': '#9E9E9E'
}

for config_key, config_name in configs.items():
    # Load per-turbine data
    csv_path = os.path.join(results_dir, f'per_turbine_{config_key}.csv')
    df = pd.read_csv(csv_path)

    # Remove TOTAL row
    df = df[df['Turbine_ID'] != 'TOTAL'].copy()
    df['Turbine_ID'] = df['Turbine_ID'].astype(int)

    # Create figure with single subplot
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))

    # Stacked bar chart (Production breakdown)
    turbines = df['Turbine_ID'].values
    x = np.arange(len(turbines))
    width = 0.7

    # Calculate values (in GWh)
    net_prod = df['Net_Production_GWh'].values
    wake_loss = df['Wake_Loss_GWh'].values
    sector_loss = df['Sector_Loss_GWh'].values
    other_loss = df['Other_Loss_GWh'].values

    # Stacked bars (from bottom to top)
    p1 = ax.bar(x, net_prod, width, label='Net Production',
                color=colors['net'], alpha=0.9, edgecolor='black')
    p2 = ax.bar(x, wake_loss, width, bottom=net_prod, label='Wake Loss',
                color=colors['wake'], alpha=0.9, edgecolor='black')
    p3 = ax.bar(x, sector_loss, width, bottom=net_prod+wake_loss, label='Sector Loss',
                color=colors['sector'], alpha=0.9, edgecolor='black')
    p4 = ax.bar(x, other_loss, width, bottom=net_prod+wake_loss+sector_loss, label='Other Loss',
                color=colors['other'], alpha=0.9, edgecolor='black')

    ax.set_ylabel('Energy Production (GWh/yr)', fontsize=30, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'A{t}' for t in turbines], fontsize=25)
    ax.set_xlabel('Turbine ID', fontsize=30, fontweight='bold')
    ax.legend(loc='lower right', fontsize=27.5)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.tick_params(axis='y', labelsize=25)
    ax.set_ylim(0, max(df['Ideal_Production_GWh']) * 1.1)

    # Add value labels on each segment (2.5x larger fonts)
    # Net production (centered in green bar)
    for i, val in enumerate(net_prod):
        if val > 0.5:  # Only label if segment is large enough
            ax.text(i, val/2, f'{val:.1f}', ha='center', va='center',
                   fontsize=22.5, fontweight='bold', color='white')

    # Wake loss (centered in orange bar)
    for i, val in enumerate(wake_loss):
        if val > 0.3:  # Only label if segment is large enough
            y_pos = net_prod[i] + val/2
            ax.text(i, y_pos, f'{val:.1f}', ha='center', va='center',
                   fontsize=20, fontweight='bold', color='white')

    # Sector loss (centered in red bar)
    for i, val in enumerate(sector_loss):
        if val > 0.3:  # Only label if segment is large enough
            y_pos = net_prod[i] + wake_loss[i] + val/2
            ax.text(i, y_pos, f'{val:.1f}', ha='center', va='center',
                   fontsize=20, fontweight='bold', color='white')

    # Other loss (centered in gray bar)
    for i, val in enumerate(other_loss):
        if val > 0.3:  # Only label if segment is large enough
            y_pos = net_prod[i] + wake_loss[i] + sector_loss[i] + val/2
            ax.text(i, y_pos, f'{val:.1f}', ha='center', va='center',
                   fontsize=20, fontweight='bold', color='white')

    plt.tight_layout()
    output_path = os.path.join(figures_dir, f'per_turbine_{config_key}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Created: {output_path}")
    plt.close()

print("\nAll per-turbine graphs created successfully!")
