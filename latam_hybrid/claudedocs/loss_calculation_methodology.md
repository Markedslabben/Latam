# Wind Farm Loss Calculation Methodology

## Overview

This document describes the methodology used by the `latam_hybrid` framework for calculating per-turbine and farm-level energy losses in wind farm simulations.

**Last Updated**: 2025-10-26
**Framework Version**: 0.1.0

---

## Loss Categories

The framework calculates four main categories of losses:

1. **Wake Losses**: Energy reduction due to turbine-to-turbine wake interactions
2. **Sector Management Losses**: Energy reduction from directional curtailment
3. **Other Losses**: Availability, electrical, environmental, and other user-specified losses
4. **Net Production**: Final energy output after all losses

---

## Calculation Architecture

### Dual Simulation Approach

Per-turbine losses are calculated using **two PyWake simulations**:

```
Simulation 1 (with wake model):
  → Captures wake effects and turbine-to-turbine interactions
  → Provides realistic production per turbine

Simulation 2 (without wake model):
  → Assumes each turbine operates independently (no wakes)
  → Provides "ideal" production baseline
```

**Key Code Reference**: `latam_hybrid/wind/site.py:302-341`

```python
if compute_losses:
    # Simulation 1: With wake model (realistic)
    sim_res = pywake_site.calc_wf(...)
    aep_with_wake = self._get_aep_per_turbine(sim_res)

    # Simulation 2: Without wake model (ideal)
    sim_res_nowake = pywake_site.calc_wf(..., wake_model=NoWakeDeficit())
    ideal_aep = self._get_aep_per_turbine(sim_res_nowake)

    # Calculate per-turbine wake losses
    wake_loss_per_turbine = ideal_aep - aep_with_wake
```

---

## Loss Cascade

Losses are applied in a **cascading sequence** to prevent amplification:

```
                 ┌─────────────────────────┐
                 │  Ideal Production       │  (No losses)
                 │  (Sim 2: NoWakeDeficit) │
                 └───────────┬─────────────┘
                             │
                 ┌───────────▼─────────────┐
                 │  Wake Losses            │  ideal - production_with_wake
                 └───────────┬─────────────┘
                             │
                 ┌───────────▼─────────────┐
                 │  Production with Wake   │  (Sim 1: Wake model)
                 └───────────┬─────────────┘
                             │
                 ┌───────────▼─────────────┐
                 │  Sector Losses          │  Energy-based calculation
                 └───────────┬─────────────┘
                             │
                 ┌───────────▼─────────────┐
                 │  Production after Sector│
                 └───────────┬─────────────┘
                             │
                 ┌───────────▼─────────────┐
                 │  Other Losses           │  Availability, electrical, etc.
                 └───────────┬─────────────┘
                             │
                 ┌───────────▼─────────────┐
                 │  Net Production         │  Final output
                 └─────────────────────────┘
```

**Mathematical Representation**:

```
ideal_production = ideal_aep_per_turbine
wake_loss = ideal_production - production_with_wake

production_after_wake = production_with_wake
sector_loss = (calculated from energy-based method, see below)

production_after_sector = production_after_wake - sector_loss
remaining_factor = losses.calculate_total_loss_factor()  # e.g., 0.912 for 8.8% losses
other_loss = production_after_sector × (1 - remaining_factor)

net_production = production_after_sector × remaining_factor
```

**Verification**:
```python
# Check loss cascade integrity
ideal - wake_loss - sector_loss - other_loss ≈ net_production
```

---

## Wake Loss Calculation (Per-Turbine)

### Method

Wake losses are calculated by comparing **ideal** vs **realistic** production for each turbine:

```python
# Per turbine i:
wake_loss[i] = ideal_aep[i] - aep_with_wake[i]
```

### Key Characteristics

- **TRUE per-turbine variation**: Turbines experience different wake losses based on:
  - Position in layout (upstream vs downstream)
  - Dominant wind direction frequency
  - Distance to neighboring turbines
  - Wake deficit model (Bastankhah-Gaussian, NOJ, etc.)

- **Farm-level wake loss percentage**:
  ```python
  wake_loss_percent = (sum(wake_loss) / sum(ideal_aep)) × 100
  ```

### Code Reference

`latam_hybrid/wind/site.py:302-341`

---

## Sector Management Loss Calculation (Per-Turbine)

### Method: Energy-Based Calculation

**IMPORTANT**: Sector losses are calculated based on **actual energy lost in prohibited wind directions**, NOT simple time availability.

#### Implementation (for Timeseries simulations):

```python
# Get hourly power production per turbine from PyWake (in Watts)
power_timeseries = sim_result.Power.values  # Shape: (n_turbines, n_timesteps)
wind_directions = wind_data.timeseries['wd'].values

# For each restricted turbine
for turbine_id, allowed_sectors in sector_config.items():
    turbine_idx = turbine_id - 1

    # Calculate energy produced in PROHIBITED sectors
    prohibited_energy_wh = 0.0
    for t, wd in enumerate(wind_directions):
        if not is_direction_in_sectors(wd, allowed_sectors):
            # Wind is in prohibited sector - this energy is LOST
            prohibited_energy_wh += power_timeseries[turbine_idx, t]

    # Convert from Wh to GWh
    sector_loss_per_turbine[turbine_idx] = prohibited_energy_wh / 1e9

    # Subtract lost energy from turbine production
    aep_per_turbine[turbine_idx] -= sector_loss_per_turbine[turbine_idx]
```

### Why Energy-Based, Not Time-Based?

**Time-Based (WRONG)**:
```python
# Assumes uniform energy distribution across all directions
availability = time_in_allowed_sectors / total_time  # e.g., 71.6%
sector_loss = production × (1 - availability)  # WRONG! Assumes uniform wind
```

**Energy-Based (CORRECT)**:
```python
# Accounts for wind speed and frequency variations by direction
sector_loss = sum(power[t] for t if wd[t] in prohibited_sectors)
```

**Example**: If allowed sectors (60-120°, 240-300°) have higher wind speeds than prohibited sectors:
- Time-based: 28.4% of time → 28.4% energy loss (WRONG)
- Energy-based: Actual energy in prohibited sectors = 5.87% (CORRECT)

### Key Characteristics

- **Direction-specific**: Only restricted turbines have sector losses
- **Wind distribution aware**: Captures actual energy in prohibited directions
- **Wake effects included**: Uses power from wake simulation (not ideal)
- **Farm-level sector loss percentage**:
  ```python
  sector_loss_percent = (sum(sector_loss) / sum(ideal_aep)) × 100
  ```

### Code Reference

`latam_hybrid/wind/site.py:738-839`

#### Weibull Method (Fallback)

For Weibull-based simulations (no timeseries), a **time-based approximation** is used:

```python
availability = calculate_sector_availability(wind_data, sector_config)
sector_loss_per_turbine[i] = aep[i] × (1 - availability[i])
```

**Note**: This is less accurate than energy-based calculation but necessary when hourly data is unavailable.

---

## Other Losses Calculation (Per-Turbine)

### Method

Other losses are applied uniformly to all turbines as a **remaining production factor**:

```python
# Load losses from configuration file (e.g., losses.csv)
loss_config = {
    'availability': 0.03,      # 3% downtime
    'electrical': 0.02,        # 2% electrical losses
    'environmental': 0.01,     # 1% environmental (icing, soiling)
    'grid_curtailment': 0.028  # 2.8% curtailment
}

# Calculate total loss factor (multiplicative, not additive)
total_loss_factor = (1 - 0.03) × (1 - 0.02) × (1 - 0.01) × (1 - 0.028)
                  = 0.97 × 0.98 × 0.99 × 0.972
                  = 0.912  # 8.8% total loss

# Apply to each turbine
for i in range(n_turbines):
    production_before_other = production_after_sector[i]

    # Calculate other loss
    other_loss_per_turbine[i] = production_before_other × (1 - total_loss_factor)

    # Calculate net production
    net_production[i] = production_before_other × total_loss_factor
```

### CRITICAL BUG FIX (2025-10-26)

**Bug**: Other losses and net production were **swapped** in the original implementation:

```python
# WRONG (before fix):
remaining_factor = losses.calculate_total_loss_factor()  # Returns 0.912
other_loss = production × remaining_factor  # WRONG! 91.2% as loss
net = production × (1 - remaining_factor)    # WRONG! 8.8% as net

# CORRECT (after fix):
remaining_factor = losses.calculate_total_loss_factor()  # Returns 0.912
net = production × remaining_factor          # CORRECT! 91.2% remains
other_loss = production × (1 - remaining_factor)  # CORRECT! 8.8% lost
```

**Impact**: Before the fix, net production showed 1.5-2.2 GWh instead of ~18-20 GWh out of 25 GWh total.

### Key Characteristics

- **Uniform application**: Same loss percentages for all turbines
- **Multiplicative**: Losses compound, not add
- **Applied to remaining energy**: After wake and sector losses
- **Farm-level calculation**: Same as per-turbine percentages

### Code Reference

`latam_hybrid/wind/site.py:441-447`

---

## Metadata Structure

All per-turbine loss data is stored in `WindSimulationResult.metadata`:

```python
result.metadata = {
    'ideal_per_turbine_gwh': [25.2, 24.8, ...],        # GWh/yr per turbine
    'wake_loss_per_turbine_gwh': [2.5, 3.1, ...],      # GWh/yr per turbine
    'sector_loss_per_turbine_gwh': [0.0, 2.8, ...],    # GWh/yr per turbine
    'other_loss_per_turbine_gwh': [2.0, 1.9, ...],     # GWh/yr per turbine
    'pywake_sim_result': <xarray.SimulationResult>,    # Full PyWake result
    'total_capacity_mw': 91.0,                         # Farm capacity
}

result.turbine_production_gwh = [20.7, 17.0, ...]     # Net GWh/yr per turbine
result.aep_gwh = 234.5                                 # Total farm net GWh/yr
result.wake_loss_percent = 10.2                        # Farm-level %
result.sector_loss_percent = 5.87                      # Farm-level %
```

**All values in absolute GWh/yr** (not percentages).

---

## Usage Examples

### Running Simulation with Loss Tracking

```python
from latam_hybrid.wind import WindSite
from latam_hybrid.wind.turbine import TurbineModel
from latam_hybrid.wind.layout import TurbineLayout
from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG

# Load site and configuration
site = WindSite.from_file(
    wind_data_path,
    source_type='vortex',
    height=164.0
)

# Run simulation with loss tracking
result = (
    site
    .with_turbine(TurbineModel.from_csv(...))
    .set_layout(TurbineLayout.from_csv(...))
    .set_sector_management(SECTOR_MANAGEMENT_CONFIG)
    .run_simulation(
        wake_model='Bastankhah_Gaussian',
        simulation_method='timeseries',
        compute_losses=True  # CRITICAL: Enables per-turbine loss tracking
    )
    .apply_losses(loss_config_file='losses.csv')
    .calculate_production()
)
```

### Accessing Loss Data

```python
import numpy as np

# Extract per-turbine losses
ideal = np.array(result.metadata['ideal_per_turbine_gwh'])
wake_loss = np.array(result.metadata['wake_loss_per_turbine_gwh'])
sector_loss = np.array(result.metadata['sector_loss_per_turbine_gwh'])
other_loss = np.array(result.metadata['other_loss_per_turbine_gwh'])
net = np.array(result.turbine_production_gwh)

# Verify loss cascade
residual = ideal - wake_loss - sector_loss - other_loss - net
print(f"Max residual: {np.max(np.abs(residual)):.6f} GWh")  # Should be ~0

# Farm-level summary
print(f"Total farm net: {result.aep_gwh:.2f} GWh/yr")
print(f"Wake losses: {result.wake_loss_percent:.2f}%")
print(f"Sector losses: {result.sector_loss_percent:.2f}%")
print(f"Capacity factor: {result.capacity_factor * 100:.2f}%")
```

### Exporting to Tables

```python
from latam_hybrid.output import export_per_turbine_losses_table

# Export to CSV
export_per_turbine_losses_table(
    result,
    "output/turbine_losses.csv",
    format='csv'
)

# Export to Excel
export_per_turbine_losses_table(
    result,
    "output/turbine_losses.xlsx",
    format='excel'
)

# Export to Markdown
export_per_turbine_losses_table(
    result,
    "output/turbine_losses.md",
    format='markdown'
)
```

---

## Validation and Testing

### Verification Checks

```python
# 1. Loss cascade integrity
ideal - wake - sector - other ≈ net
max_error < 1e-6 GWh

# 2. Unrestricted turbines have zero sector losses
for turbine_id in unrestricted_turbines:
    assert sector_loss[turbine_id - 1] == 0.0

# 3. Farm-level percentages match sum of per-turbine
farm_wake_pct = sum(wake_loss) / sum(ideal) * 100
assert abs(farm_wake_pct - result.wake_loss_percent) < 0.01

# 4. Capacity factor calculation
rated_power_kw = total_capacity_mw * 1000 / n_turbines
cf = (net_production_gwh * 1000) / (rated_power_kw * 8760)
assert 0 <= cf <= 1
```

### Unit Tests

See `tests/test_loss_calculations.py` for comprehensive unit tests.

---

## References

### Code Files

- `latam_hybrid/wind/site.py` - Main loss calculation logic
- `latam_hybrid/wind/losses.py` - Loss configuration and total loss factor
- `latam_hybrid/wind/sector_management.py` - Sector management utilities
- `latam_hybrid/output/export.py` - Table export functions

### Scripts

- `scripts/plot_turbine_production_N164.py` - Visualization of per-turbine losses
- `scripts/test_timeseries_N164.py` - Console output validation
- `scripts/diagnose_sector_losses.py` - Sector loss diagnostics

### Bug Fixes Log

- **2025-10-26**: Fixed swapped other losses calculation (site.py:441-447)
- **2025-10-26**: Changed sector losses from time-based to energy-based (site.py:738-839)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-26 | 1.0 | Initial documentation with bug fixes |
