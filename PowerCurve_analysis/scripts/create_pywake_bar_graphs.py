"""
Create bar graphs for PyWake simulation results with losses (11-year timeseries).
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

# Paths
results_dir = os.path.join(os.path.dirname(__file__), '..', 'results')
figures_dir = os.path.join(os.path.dirname(__file__), '..', 'figures')
os.makedirs(figures_dir, exist_ok=True)

# Load 11-year results
df_full = pd.read_csv(os.path.join(results_dir, 'table4_pywake_with_losses_full.csv'))

# Extract configurations (remove @ symbol for cleaner display)
configs = [c.replace(' @ ', '\n') for c in df_full['Configuration']]
colors = ['#2E7D32', '#1976D2', '#D32F2F', '#7B1FA2', '#F57C00']

# Create figure with 3 subplots (removed normalized production as it's redundant with FLH)
fig = plt.figure(figsize=(14, 10))
gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, :])  # Loss breakdown spans both columns
fig.suptitle('PyWake Simulation Results - 11-Year Average with Comprehensive Losses',
             fontsize=16, fontweight='bold', y=0.995)

# 1. Net AEP
ax = ax1
bars = ax.bar(range(len(configs)), df_full['Net AEP (GWh/yr)'], color=colors, alpha=0.8, edgecolor='black')
ax.set_ylabel('Net AEP (GWh/yr)', fontsize=11, fontweight='bold')
ax.set_title('Net Annual Energy Production\n(After all losses)', fontsize=12, fontweight='bold')
ax.set_xticks(range(len(configs)))
ax.set_xticklabels(configs, fontsize=9, rotation=0)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, max(df_full['Net AEP (GWh/yr)']) * 1.15)
# Add value labels
for i, (bar, val) in enumerate(zip(bars, df_full['Net AEP (GWh/yr)'])):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# 2. Capacity Factor
ax = ax2
bars = ax.bar(range(len(configs)), df_full['Capacity Factor (%)'], color=colors, alpha=0.8, edgecolor='black')
ax.set_ylabel('Capacity Factor (%)', fontsize=11, fontweight='bold')
ax.set_title('Capacity Factor\n(Net production / Rated capacity)', fontsize=12, fontweight='bold')
ax.set_xticks(range(len(configs)))
ax.set_xticklabels(configs, fontsize=9, rotation=0)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(0, max(df_full['Capacity Factor (%)']) * 1.15)
# Add value labels
for i, (bar, val) in enumerate(zip(bars, df_full['Capacity Factor (%)'])):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{val:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

# 3. Loss Breakdown (Stacked) - Now spans full width
ax = ax3
wake_loss = df_full['Wake Loss (%)']
sector_loss = df_full['Sector Loss (%)']
other_loss = df_full['Other Loss (%)']
net_pct = 100 - df_full['Total Loss (%)']

x = np.arange(len(configs))
width = 0.6

p1 = ax.bar(x, net_pct, width, label='Net Production', color='#4CAF50', alpha=0.9, edgecolor='black')
p2 = ax.bar(x, wake_loss, width, bottom=net_pct, label='Wake Loss', color='#FF9800', alpha=0.9, edgecolor='black')
p3 = ax.bar(x, sector_loss, width, bottom=net_pct+wake_loss, label='Sector Loss', color='#F44336', alpha=0.9, edgecolor='black')
p4 = ax.bar(x, other_loss, width, bottom=net_pct+wake_loss+sector_loss, label='Other Loss', color='#9E9E9E', alpha=0.9, edgecolor='black')

ax.set_ylabel('Percentage (%)', fontsize=11, fontweight='bold')
ax.set_title('Loss Breakdown (Stacked)\nGross Production = 100%', fontsize=12, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(configs, fontsize=9, rotation=0)
ax.legend(loc='upper right', fontsize=9)
ax.set_ylim(0, 105)
ax.grid(axis='y', alpha=0.3, linestyle='--')

plt.tight_layout()
output_path = os.path.join(figures_dir, 'figure3_pywake_results_with_losses.png')
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Created: {output_path}")
plt.close()

print("\nBar graphs created successfully!")
