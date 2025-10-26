# Wind Farm Losses Module - Usage Guide

## Overview

The wind farm losses module implements WindPRO-compliant loss calculations using a multiplicative loss formula:

```
Loss_factor = (1 - l₁) × (1 - l₂) × ... × (1 - lₙ)
Net AEP = Gross AEP × Loss_factor
```

## Loss Categories

### Computed Losses (from simulations)
1. **Wake losses** - Calculated by PyWake simulation
2. **Curtailment from sector management** - Calculated by sector control module (future)

### User-Specified Losses (WindPRO defaults)
1. **Availability turbines**: 1.5% (default)
2. **Availability grid**: 1.5% (default)
3. **Electrical losses**: 2.0% (default)
4. **High hysteresis losses**: 0.3% (default)
5. **Environmental performance degradation**: 3.0% (default)
6. **Other losses**: 0.5% (default)

**Total default losses**: ~8.8% (excluding wake and curtailment)

### CSV Configuration

Default loss values are read from `latam_hybrid/Inputdata/losses.csv`. You can customize this file to change project-wide defaults:

```csv
loss_category,default_value,description,unit
availability_turbines,0.015,Turbine downtime for maintenance and repairs,fraction
availability_grid,0.015,Grid outages and maintenance,fraction
electrical_losses,0.020,Cable losses and transformer losses,fraction
high_hysteresis_losses,0.003,Power curve hysteresis effects,fraction
environmental_performance_degradation,0.030,Performance decline over project lifetime,fraction
other_losses,0.005,Miscellaneous unaccounted losses,fraction
```

**Priority system**: Manual overrides > CSV values > Built-in defaults

## Basic Usage

### Example 1: Using Default Losses

```python
from latam_hybrid.wind import WindSite

# Run simulation and apply default losses
result = (
    WindSite.from_wind_data(wind_data)
    .with_turbine(turbine)
    .set_layout(layout)
    .run_simulation(wake_model='NOJ')  # Computes wake losses
    .apply_losses()                     # Apply default WindPRO losses
    .calculate_production()
)

# Access results
print(f"Gross AEP: {result.gross_aep_gwh:.2f} GWh")
print(f"Net AEP: {result.aep_gwh:.2f} GWh")
print(f"Wake losses: {result.wake_loss_percent:.2f}%")
print(f"Total loss factor: {result.total_loss_factor:.4f}")

# Detailed loss breakdown
for loss_name, loss_data in result.loss_breakdown.items():
    print(f"{loss_name}: {loss_data['percentage']:.2f}%")
```

### Example 2: Custom Loss Values

```python
# Override specific loss values
result = (
    WindSite.from_wind_data(wind_data)
    .with_turbine(turbine)
    .set_layout(layout)
    .run_simulation(wake_model='NOJ')
    .apply_losses(
        availability_turbines=0.02,      # Custom 2% instead of 1.5%
        electrical_losses=0.025,         # Custom 2.5% instead of 2.0%
        environmental_degradation=0.04   # Custom 4% instead of 3.0%
    )
    .calculate_production()
)
```

### Example 3: Using Custom CSV Configuration

```python
# Create custom loss configuration file
# custom_losses.csv:
# loss_category,default_value,description,unit
# availability_turbines,0.020,Higher turbine downtime,fraction
# availability_grid,0.010,Lower grid downtime,fraction
# electrical_losses,0.025,Higher electrical losses,fraction
# ...

# Use custom CSV file
result = (
    WindSite.from_wind_data(wind_data)
    .with_turbine(turbine)
    .set_layout(layout)
    .run_simulation(wake_model='NOJ')
    .apply_losses(loss_config_file='path/to/custom_losses.csv')
    .calculate_production()
)
```

### Example 4: Sector Management (Turbine Curtailment)

```python
from latam_hybrid.core import SectorManagementConfig

# Define sector management: turbines stop when wind from prohibited directions
# Example: Turbines 1,3,5,7,9,12 only run when wind is 60-120° or 240-300°
sector_config = SectorManagementConfig(
    turbine_sectors={
        1: [(60, 120), (240, 300)],   # Turbine 1: allowed sectors
        3: [(60, 120), (240, 300)],   # Turbine 3: same sectors
        5: [(60, 120), (240, 300)],   # Turbine 5: same sectors
        7: [(60, 120), (240, 300)],   # Turbine 7: same sectors
        9: [(60, 120), (240, 300)],   # Turbine 9: same sectors
        12: [(60, 120), (240, 300)]   # Turbine 12: same sectors
        # Turbines 2, 4, 6, 8, 10, 11, 13 have NO restrictions
    },
    metadata={'reason': 'Noise restrictions from nearby residents'}
)

# Run simulation with sector management
result = (
    WindSite.from_wind_data(wind_data)
    .with_turbine(turbine)
    .set_layout(layout)
    .set_sector_management(sector_config)  # Add sector management
    .run_simulation(wake_model='NOJ')      # Computes sector losses
    .apply_losses()                         # Apply other losses
    .calculate_production()
)

# Access sector losses
print(f"Wake losses: {result.wake_loss_percent:.2f}%")
print(f"Sector losses: {result.sector_loss_percent:.2f}%")
print(f"Other losses: ~8.8%")
print(f"Total losses: {(1 - result.total_loss_factor) * 100:.2f}%")

# Detailed loss breakdown
for loss_name, loss_data in result.loss_breakdown.items():
    print(f"{loss_name}: {loss_data['percentage']:.2f}%")
```

**How Sector Management Works:**
- Turbines are **STOPPED** (zero production, no wakes) when wind comes from prohibited directions
- Allowed sectors: Turbine runs when wind direction is within specified ranges
- Prohibited sectors: All other wind directions → turbine stops
- Example: `[(60, 120), (240, 300)]` means turbine runs only when wind is 60-120° or 240-300°

**Different Sectors Per Turbine:**
```python
# Each turbine can have different sector restrictions
sector_config = SectorManagementConfig(
    turbine_sectors={
        1: [(60, 120), (240, 300)],    # Turbine 1 sectors
        3: [(50, 130), (230, 310)],    # Turbine 3 different sectors
        5: [(0, 90), (180, 270)]       # Turbine 5 completely different
    }
)
```

## Standalone Losses Calculation

You can also use the losses module independently:

```python
from latam_hybrid.wind.losses import WindFarmLosses, create_default_losses

# Create losses manager
losses = WindFarmLosses()

# Add wake losses (from simulation)
losses.add_loss('wake_losses', 0.08, is_computed=True)

# Add default losses
losses.add_default_losses(
    availability_turbines=0.015,
    availability_grid=0.015,
    electrical_losses=0.02,
    high_hysteresis=0.003,
    environmental_degradation=0.03,
    other_losses=0.005
)

# Calculate results
gross_aep = 1000.0  # GWh
net_aep = losses.calculate_net_aep(gross_aep)
total_loss_pct = losses.calculate_total_loss_percentage()

print(f"Gross AEP: {gross_aep} GWh")
print(f"Net AEP: {net_aep:.2f} GWh")
print(f"Total losses: {total_loss_pct:.2f}%")

# Get detailed breakdown
breakdown = losses.get_loss_breakdown()
for name, data in breakdown.items():
    computed_flag = " (computed)" if data['is_computed'] else ""
    print(f"{name}: {data['percentage']:.2f}%{computed_flag}")
```

## Convenience Function

For quick setup:

```python
from latam_hybrid.wind.losses import create_default_losses

# Create with wake losses and defaults
losses = create_default_losses(
    wake_loss=0.08,
    availability_turbines=0.02  # Override specific default
)

net_aep = losses.calculate_net_aep(1000.0)
```

## Understanding the Multiplicative Formula

The multiplicative formula correctly models independent loss mechanisms:

```python
# Example: 3% and 2% losses
# Additive (WRONG): 3% + 2% = 5% total → Net = 95%
# Multiplicative (CORRECT): (1-0.03) × (1-0.02) = 0.9506 → Net = 95.06%

losses = WindFarmLosses()
losses.add_loss('loss1', 0.03)
losses.add_loss('loss2', 0.02)

total_factor = losses.calculate_total_loss_factor()  # 0.9506
total_pct = losses.calculate_total_loss_percentage()  # 4.94%
```

## Loss Breakdown Analysis

Access detailed loss information:

```python
# Get only computed losses
computed = losses.get_computed_losses()
print("Computed losses:")
for name, loss in computed.items():
    print(f"  {name}: {loss.percentage:.2f}%")

# Get only user-specified losses
user = losses.get_user_losses()
print("\nUser-specified losses:")
for name, loss in user.items():
    print(f"  {name}: {loss.percentage:.2f}%")

# Full export to dictionary
export_data = losses.to_dict()
```

### Complete Loss Breakdown Structure

The `result.loss_breakdown` dictionary contains detailed information for each loss category:

```python
{
    'wake_losses': {
        'percentage': 8.5,              # Loss percentage
        'value': 0.085,                 # Loss as fraction
        'is_computed': True,            # Computed vs user-specified
        'applied_in': 'run_simulation', # Where loss is applied
        'description': 'Wake effects from turbine interactions'
    },
    'availability_turbines': {
        'percentage': 1.5,
        'value': 0.015,
        'is_computed': False,
        'applied_in': 'apply_losses',   # Applied after simulation
        'description': 'Turbine downtime for maintenance and repairs'
    },
    # ... other loss categories
}
```

**Key Fields**:
- `percentage`: Loss as percentage (0-100)
- `value`: Loss as fraction (0-1)
- `is_computed`: True if computed from simulations, False if user-specified
- `applied_in`: Either 'run_simulation' (wake/sector) or 'apply_losses' (others)
- `description`: Human-readable description

**Important Notes**:
- Wake losses appear as **already applied** in the AEP from `run_simulation()`
- Other losses are applied **multiplicatively** on top of the wake-affected AEP
- Sector management losses (future) will also be applied in `run_simulation()`
- No double-counting: each loss is applied exactly once

## Typical Wind Farm Scenario

```python
# Realistic example for 100 MW wind farm
result = (
    WindSite.from_wind_data(wind_data)
    .with_turbine(turbine)
    .set_layout(layout)
    .run_simulation(wake_model='NOJ')
    .apply_losses()
    .calculate_production()
)

# Expected results for typical wind farm:
# Gross AEP: ~350 GWh
# Wake losses: ~8-12%
# Other losses: ~8.8% (defaults)
# Total losses: ~16-20%
# Net AEP: ~280-295 GWh
# Capacity factor: ~32-34%
```

## Integration with Economic Analysis

```python
# Calculate revenue based on net AEP
net_aep_gwh = result.aep_gwh
electricity_price = 50  # USD/MWh

annual_revenue = net_aep_gwh * 1000 * electricity_price  # GWh → MWh
print(f"Annual revenue: ${annual_revenue:,.0f}")

# Loss impact on revenue
gross_revenue = result.gross_aep_gwh * 1000 * electricity_price
revenue_loss = gross_revenue - annual_revenue
print(f"Revenue lost to losses: ${revenue_loss:,.0f}")
```

## Validation and Debugging

```python
# Validate loss values are reasonable
losses = WindFarmLosses()
losses.add_default_losses()

assert 0.08 < losses.calculate_total_loss_percentage() < 0.12, \
    "Default total losses should be 8-12%"

# Check individual components
breakdown = losses.get_loss_breakdown()
for name, data in breakdown.items():
    assert 0 <= data['value'] <= 1, f"{name} has invalid value"
    print(f"✓ {name}: {data['percentage']:.2f}%")
```

## Best Practices

1. **Always apply losses after simulation** - Wake losses are computed first
2. **Use defaults unless you have specific data** - WindPRO defaults are industry-standard
3. **Document custom values** - If overriding defaults, document the source
4. **Check total losses** - Total should typically be 15-25% for wind farms
5. **Compare gross vs net** - Always report both for transparency

## Common Patterns

### Pattern 1: Conservative Estimate (P90)
```python
result = site.run_simulation().apply_losses(
    availability_turbines=0.025,      # Higher availability losses
    environmental_degradation=0.04    # Higher degradation
).calculate_production()
```

### Pattern 2: Best Case (P10)
```python
result = site.run_simulation().apply_losses(
    availability_turbines=0.01,       # Lower availability losses
    environmental_degradation=0.02    # Lower degradation
).calculate_production()
```

### Pattern 3: Export for Reporting
```python
result = site.run_simulation().apply_losses().calculate_production()

# Create detailed loss report
report = {
    'gross_aep_gwh': result.gross_aep_gwh,
    'net_aep_gwh': result.aep_gwh,
    'total_loss_percentage': (1 - result.total_loss_factor) * 100,
    'individual_losses': result.loss_breakdown
}

import json
with open('loss_report.json', 'w') as f:
    json.dump(report, f, indent=2)
```

## API Reference

### WindFarmLosses

**Key Methods**:
- `add_loss(name, value, is_computed, description)` - Add loss category
- `add_default_losses(**kwargs)` - Add WindPRO defaults
- `calculate_total_loss_factor()` - Get multiplicative loss factor (0-1)
- `calculate_total_loss_percentage()` - Get total loss percentage (0-100)
- `calculate_net_aep(gross_aep)` - Calculate net AEP
- `get_loss_breakdown()` - Get detailed breakdown dictionary
- `to_dict()` - Export complete summary

### WindSite.apply_losses()

**Parameters**:
- `loss_config_file` (str, optional) - Path to CSV file with loss configurations
  - Default: `latam_hybrid/Inputdata/losses.csv`
  - If file not found, falls back to built-in defaults

**Loss Override Parameters** (all optional, override CSV/defaults):
- `availability_turbines` - Default: 0.015 (1.5%)
- `availability_grid` - Default: 0.015 (1.5%)
- `electrical_losses` - Default: 0.02 (2.0%)
- `high_hysteresis` - Default: 0.003 (0.3%)
- `environmental_degradation` - Default: 0.03 (3.0%)
- `other_losses` - Default: 0.005 (0.5%)

**Future Parameters**:
- `curtailment_sector` - Not yet implemented (sector management module)

**Priority System**: Manual overrides > CSV values > Built-in defaults

**Returns**: `WindSite` (for method chaining)

## Troubleshooting

### Issue: Total losses seem too high
```python
# Check breakdown
for name, data in result.loss_breakdown.items():
    if data['percentage'] > 5.0:
        print(f"⚠️ High loss: {name} = {data['percentage']:.2f}%")
```

### Issue: Losses not being applied
```python
# Ensure apply_losses() is called before calculate_production()
result = site.run_simulation().apply_losses().calculate_production()

# Check if losses were applied
if result.loss_breakdown is None:
    print("❌ Losses not applied!")
else:
    print("✓ Losses applied")
```

### Issue: Can't override default values
```python
# Make sure to pass values as fractions, not percentages
losses.apply_losses(
    availability_turbines=0.02,  # ✓ Correct (2%)
    # NOT: availability_turbines=2  # ❌ Wrong (200%!)
)
```

### Issue: CSV file not found or not loading
```python
# Check if CSV exists
import os
csv_path = 'latam_hybrid/Inputdata/losses.csv'
if not os.path.exists(csv_path):
    print(f"❌ CSV not found at {csv_path}")
    print("Will use built-in defaults")

# Provide explicit path if needed
result = site.apply_losses(
    loss_config_file='/absolute/path/to/losses.csv'
)

# Verify CSV was loaded
if result._losses is not None:
    print("✓ Losses configuration loaded")
```

### Issue: Sector management losses not appearing
```python
# Sector management is not yet implemented
# Currently defaults to 0.0% and won't appear in loss breakdown
# This is expected behavior - it's a future feature

# Check if it appears in breakdown
if 'sector_management' in result.loss_breakdown:
    print("Sector losses present")
else:
    print("Sector losses = 0% (not implemented yet)")
```
