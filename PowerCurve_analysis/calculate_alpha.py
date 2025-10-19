"""
Calculate wind shear coefficient alpha from wind speed measurements at different heights
Using the power law: V/V_ref = (H/H_ref)^alpha
"""

import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# Data
heights = np.array([50, 100, 150, 200])  # meters
velocities = np.array([6.28, 7.11, 7.66, 8.1])  # m/s

# Reference values
H_ref = 100  # m
V_ref = 7.11  # m/s

print("Wind Shear Coefficient (Alpha) Calculation")
print("=" * 60)
print(f"\nReference: H_ref = {H_ref} m, V_ref = {V_ref} m/s")
print("\nData points:")
for h, v in zip(heights, velocities):
    print(f"  H = {h:3d} m, V = {v:.2f} m/s")

# Method 1: Calculate alpha for each individual point (excluding reference)
print("\n" + "=" * 60)
print("Method 1: Individual alpha values (excluding reference point)")
print("=" * 60)

alphas = []
for h, v in zip(heights, velocities):
    if h != H_ref:  # Skip reference point
        # alpha = ln(V/V_ref) / ln(H/H_ref)
        alpha = np.log(v / V_ref) / np.log(h / H_ref)
        alphas.append(alpha)
        print(f"H = {h:3d} m: alpha = {alpha:.4f}")

mean_alpha = np.mean(alphas)
std_alpha = np.std(alphas)
print(f"\nMean alpha: {mean_alpha:.4f} ± {std_alpha:.4f}")

# Method 2: Least squares fit using all points
print("\n" + "=" * 60)
print("Method 2: Least squares fit (all points)")
print("=" * 60)

# Define power law function
def power_law(h, alpha):
    return V_ref * (h / H_ref) ** alpha

# Fit the data
popt, pcov = curve_fit(power_law, heights, velocities)
alpha_fit = popt[0]
alpha_error = np.sqrt(pcov[0, 0])

print(f"Best-fit alpha: {alpha_fit:.4f} ± {alpha_error:.4f}")

# Calculate R² (coefficient of determination)
v_predicted = power_law(heights, alpha_fit)
ss_res = np.sum((velocities - v_predicted) ** 2)
ss_tot = np.sum((velocities - np.mean(velocities)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

print(f"R² = {r_squared:.6f}")

# Show predicted vs actual
print("\nPredicted vs Actual:")
print(f"{'Height (m)':<12} {'Actual (m/s)':<15} {'Predicted (m/s)':<18} {'Error (%)':<10}")
print("-" * 60)
for h, v_actual, v_pred in zip(heights, velocities, v_predicted):
    error_pct = 100 * (v_pred - v_actual) / v_actual
    print(f"{h:<12} {v_actual:<15.2f} {v_pred:<18.2f} {error_pct:>8.2f}%")

# Method 3: Linear regression on log-transformed data
print("\n" + "=" * 60)
print("Method 3: Linear regression (log-log plot)")
print("=" * 60)

# ln(V/V_ref) = alpha * ln(H/H_ref)
ln_v_ratio = np.log(velocities / V_ref)
ln_h_ratio = np.log(heights / H_ref)

# Linear fit: y = alpha * x
alpha_linreg = np.sum(ln_h_ratio * ln_v_ratio) / np.sum(ln_h_ratio ** 2)
print(f"Linear regression alpha: {alpha_linreg:.4f}")

# Alternative using numpy polyfit
coeffs = np.polyfit(ln_h_ratio, ln_v_ratio, 1)
alpha_polyfit = coeffs[0]
intercept = coeffs[1]
print(f"Polyfit alpha: {alpha_polyfit:.4f}")
print(f"Intercept: {intercept:.6f} (should be ~0)")

# Visualization
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: Wind speed profile
h_fine = np.linspace(40, 210, 100)
v_fit = V_ref * (h_fine / H_ref) ** alpha_fit

ax1.plot(velocities, heights, 'o', markersize=10, label='Measured data', color='#1f77b4')
ax1.plot(v_fit, h_fine, '-', linewidth=2,
         label=f'Power law (α = {alpha_fit:.4f})', color='#ff7f0e')
ax1.axhline(H_ref, color='gray', linestyle='--', alpha=0.5, label=f'Reference height ({H_ref} m)')
ax1.set_xlabel('Wind Speed (m/s)', fontsize=12)
ax1.set_ylabel('Height (m)', fontsize=12)
ax1.set_title('Wind Speed Profile', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=10)

# Plot 2: Log-log plot
ax2.plot(ln_h_ratio, ln_v_ratio, 'o', markersize=10, label='Data points', color='#1f77b4')
ln_h_fine = np.linspace(min(ln_h_ratio), max(ln_h_ratio), 100)
ln_v_fit = alpha_fit * ln_h_fine
ax2.plot(ln_h_fine, ln_v_fit, '-', linewidth=2,
         label=f'Linear fit (slope = {alpha_fit:.4f})', color='#ff7f0e')
ax2.set_xlabel('ln(H/H_ref)', fontsize=12)
ax2.set_ylabel('ln(V/V_ref)', fontsize=12)
ax2.set_title('Log-Log Plot', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.legend(fontsize=10)
ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
ax2.axvline(0, color='gray', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('wind_shear_alpha.png', dpi=300, bbox_inches='tight')
print("\n" + "=" * 60)
print("Plot saved as: wind_shear_alpha.png")
print("=" * 60)

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Recommended alpha: {alpha_fit:.4f}")
print(f"\nTypical values for reference:")
print("  alpha = 1/7 = 0.143 (neutral stability, flat terrain)")
print("  alpha = 0.20 (moderately rough terrain)")
print("  alpha = 0.30 (very rough terrain/urban)")
print(f"\nYour terrain: alpha = {alpha_fit:.4f}")

if alpha_fit < 0.15:
    terrain_type = "smooth/flat terrain (low surface roughness)"
elif alpha_fit < 0.22:
    terrain_type = "moderately rough terrain (crops, scattered obstacles)"
else:
    terrain_type = "rough terrain (forests, buildings)"

print(f"Terrain classification: {terrain_type}")

# Extrapolation example
print("\n" + "=" * 60)
print("Wind Speed Extrapolation Examples (using alpha = {:.4f}):".format(alpha_fit))
print("=" * 60)
test_heights = [10, 30, 80, 120, 150, 200]
for h_test in test_heights:
    v_extrapolated = V_ref * (h_test / H_ref) ** alpha_fit
    print(f"  At {h_test:3d} m: V = {v_extrapolated:.2f} m/s")

# plt.show()  # Commented out to avoid blocking in non-interactive mode
