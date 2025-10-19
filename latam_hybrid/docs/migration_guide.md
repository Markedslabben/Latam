# Migration Guide: Legacy → New Framework

This guide helps you migrate from the legacy codebase to the new **Latam Hybrid Energy Analysis Framework**.

## Overview of Changes

### Architecture Changes

**Before (Legacy)**:
- Monolithic scripts
- Scattered functions across multiple files
- Mixed concerns (data loading + calculation + output)
- No clear module boundaries
- Difficult to test and maintain

**After (New Framework)**:
- Clean modular architecture
- Clear separation: Input → Processing → Output
- Domain-driven design (wind, solar, GIS, economics)
- Method chaining / fluent API
- Comprehensive test coverage (77%)

## Quick Migration Examples

### Example 1: Simple Shading Calculation

**Legacy Code** (`shading_loss.py`):
```python
from shading_loss import calculate_annual_shading_loss

annual_results, annual_loss = calculate_annual_shading_loss(
    latitude=40.0,
    longitude=-80.0,
    altitude=100,
    tower_height=80,
    tower_diameter=4,
    tower_location=(0, 0),
    pv_location=(20, 30),
    year=2024
)
```

**New Framework**:
```python
from latam_hybrid.solar import ShadingCalculator

calculator = ShadingCalculator(
    turbine_height=80,
    turbine_diameter=4,
    latitude=40.0,
    longitude=-80.0
)

annual_loss = calculator.calculate_annual_loss(
    turbine_positions=[(0, 0)],
    pv_positions=[(20, 30)],
    year=2024
)
```

### Example 2: Wind Production Calculation

**Legacy Code**:
```python
# Scattered across multiple scripts
import pandas as pd
from wind_energy_estimate import calculate_production

# Load data manually
wind_data = pd.read_csv("wind_data.csv")
turbine_data = pd.read_csv("turbine.csv")

# Manual calculations
production = calculate_production(wind_data, turbine_data)
```

**New Framework**:
```python
from latam_hybrid.wind import load_turbine, load_layout, create_wind_site

# Method chaining for clean workflow
turbine = load_turbine("turbine.csv")
layout = load_layout("layout.csv")
wind_site = create_wind_site("wind_data.nc")

# Run simulation
result = wind_site.set_turbine(turbine).set_layout(layout).run_simulation()

print(f"AEP: {result.aep_gwh} GWh")
print(f"Capacity Factor: {result.capacity_factor:.2%}")
```

### Example 3: Complete Hybrid Analysis

**Legacy Code**:
```python
# Multiple scripts needed:
# - wind_farm_sim.py
# - pv_production_calculator.py
# - calculate_annual_loss.py
# - economics_calculator.py
# - manual result aggregation

# Scattered across many files...
wind_result = run_wind_simulation(...)
solar_result = run_solar_simulation(...)
shading_loss = calculate_shading(...)
economics = calculate_economics(...)

# Manual aggregation
total_production = wind_result + solar_result * (1 - shading_loss)
```

**New Framework**:
```python
from latam_hybrid import quick_feasibility_study

# Single function call for complete analysis
result = quick_feasibility_study(
    project_name="My Hybrid Project",
    wind_capacity_mw=50,
    solar_capacity_mw=10,
    annual_wind_production_gwh=150,
    annual_solar_production_gwh=30,
    electricity_price=55
)

# Structured results
print(f"Total AEP: {result.production.total_aep_gwh} GWh")
print(f"LCOE: {result.economics.lcoe} USD/MWh")
print(f"NPV: {result.economics.npv/1e6:.1f} MUSD")
print(f"IRR: {result.economics.irr:.1%}")

# Auto-export results
from latam_hybrid.output import export_all
export_all(result, "output/", formats=['json', 'excel', 'markdown'])
```

## Module-by-Module Migration

### Data Loading

**Legacy**: Manual pandas operations scattered everywhere
```python
import pandas as pd

wind_data = pd.read_csv("wind.csv", parse_dates=['time'])
solar_data = pd.read_csv("solar.csv", parse_dates=['time'])
# Manual time alignment, validation, etc.
```

**New Framework**: Unified loaders with validation
```python
from latam_hybrid.input import load_wind_data, load_solar_data

wind_data = load_wind_data("wind.csv", validate=True)
solar_data = load_solar_data("solar.csv", validate=True)
# Automatic time alignment, validation, error checking
```

### Wind Analysis

**Legacy**: Direct pywake calls, manual setup
```python
from py_wake import NOJ
from py_wake.examples.data.hornsrev1 import V80

site = ...  # Manual site setup
windTurbines = V80()
wfm = NOJ(site, windTurbines)
sim_res = wfm(x=[0, 500], y=[0, 0])
```

**New Framework**: Clean abstraction layer
```python
from latam_hybrid.wind import TurbineModel, TurbineLayout, WindSite

turbine = TurbineModel.from_file("turbine.csv")
layout = TurbineLayout.from_coordinates(x=[0, 500], y=[0, 0])
site = WindSite(wind_data, turbulence_intensity=0.1)

result = site.set_turbine(turbine).set_layout(layout).run_simulation(wake_model="NOJ")
```

### Solar Analysis

**Legacy**: Manual pvlib calculations
```python
import pvlib

location = pvlib.location.Location(lat, lon)
times = pd.date_range(...)
solar_position = location.get_solarposition(times)
# Many manual steps...
```

**New Framework**: Simplified API
```python
from latam_hybrid.solar import SolarSite, SolarSystem

solar_system = SolarSystem(
    name="My PV System",
    capacity_mw=10,
    module_type="Standard",
    inverter_type="Standard"
)

solar_site = SolarSite(solar_data, latitude=lat, longitude=lon)
result = solar_site.set_system(solar_system).calculate_production()
```

### Economics

**Legacy**: Manual spreadsheet-style calculations
```python
# Manual LCOE calculation
capex = wind_capex + solar_capex
opex = wind_opex + solar_opex
production = wind_production + solar_production

years = range(25)
cash_flows = [-capex] + [(production * price - opex) for _ in years]
npv = sum(cf / (1 + discount_rate)**year for year, cf in enumerate(cash_flows))
```

**New Framework**: Professional financial functions
```python
from latam_hybrid.economics import create_hybrid_economics, calculate_all_metrics

economics = create_hybrid_economics(
    wind_capacity_mw=50,
    solar_capacity_mw=10,
    electricity_price=55
)

metrics = calculate_all_metrics(
    annual_production_mwh=180_000,
    installed_capacity_mw=60,
    economic_params=economics
)

print(f"LCOE: {metrics.lcoe}")
print(f"NPV: {metrics.npv}")
print(f"IRR: {metrics.irr}")
```

### Results Export

**Legacy**: Manual CSV writing
```python
results_df = pd.DataFrame({
    'wind_production': wind_production,
    'solar_production': solar_production,
    'total_production': total_production
})
results_df.to_csv("results.csv")

# Manual report writing
with open("report.txt", "w") as f:
    f.write(f"Wind Production: {wind_production}\n")
    f.write(f"Solar Production: {solar_production}\n")
    # ...
```

**New Framework**: Structured export with multiple formats
```python
from latam_hybrid.output import export_all, save_report

# Export to all formats at once
export_all(result, "output/", formats=['json', 'csv', 'excel', 'markdown'])

# Professional reports
save_report(result, "output/report.md", format='markdown')
```

## Key Concepts to Learn

### 1. Frozen Dataclasses

**Purpose**: Immutable data structures prevent accidental modification

```python
from latam_hybrid.core import WindData

# Create once, cannot modify
wind_data = WindData(
    u=u_component,
    v=v_component,
    timestamps=times
)

# This will raise an error:
# wind_data.u = new_data  # ❌ FrozenInstanceError
```

### 2. Method Chaining

**Purpose**: Fluent API for readable workflows

```python
result = (
    site
    .set_turbine(turbine)
    .set_layout(layout)
    .run_simulation(wake_model="NOJ")
)
```

### 3. Separation of Concerns

**Input → Processing → Output**

```python
# Input: Load data
wind_data = load_wind_data("wind.csv")

# Processing: Calculate
result = calculate_wind_production(wind_data, turbine, layout)

# Output: Export
export_to_excel(result, "output.xlsx")
```

### 4. Type Hints

**Purpose**: Better IDE support and error detection

```python
def calculate_lcoe(
    annual_production_mwh: float,
    capex: float,
    opex: float,
    discount_rate: float = 0.08
) -> float:
    """Calculate LCOE with clear types."""
    ...
```

## Common Migration Patterns

### Pattern 1: Script → Function

**Before**: Script with global variables
```python
# calculate_production.py
turbine_capacity = 5000  # kW
num_turbines = 10
wind_speed = pd.read_csv("wind.csv")

production = calculate(wind_speed, turbine_capacity, num_turbines)
print(production)
```

**After**: Proper function with parameters
```python
from latam_hybrid.wind import calculate_production

def run_analysis(turbine_file, layout_file, wind_file):
    turbine = load_turbine(turbine_file)
    layout = load_layout(layout_file)
    wind_data = load_wind_data(wind_file)

    return calculate_production(wind_data, turbine, layout)
```

### Pattern 2: Manual Loops → Vectorized Operations

**Before**: Manual iteration
```python
results = []
for timestamp in timestamps:
    result = calculate_for_time(timestamp)
    results.append(result)
```

**After**: Vectorized pandas/numpy
```python
results = calculate_vectorized(timestamps)  # Much faster
```

### Pattern 3: Implicit → Explicit

**Before**: Magic numbers and assumptions
```python
discount_rate = 0.08  # Where did this come from?
project_lifetime = 25  # Why 25?
```

**After**: Explicit configuration
```python
from latam_hybrid.economics import FinancingParameters

financing = FinancingParameters(
    project_lifetime=25,  # Standard for renewables
    discount_rate=0.08,   # Typical WACC for solar/wind
    inflation_rate=0.02   # Long-term average
)
```

## Testing Your Migration

### 1. Compare Outputs

```python
# Run both legacy and new code
legacy_result = legacy_calculate_production(...)
new_result = new_framework_calculate_production(...)

# Compare
assert abs(legacy_result - new_result.aep_gwh * 1000) < 1.0  # Within 1 MWh
```

### 2. Validate Edge Cases

```python
import pytest

def test_zero_wind():
    """Test with no wind."""
    result = calculate_production(zero_wind_data, turbine, layout)
    assert result.aep_gwh == 0

def test_extreme_wind():
    """Test with above-rated wind."""
    result = calculate_production(extreme_wind_data, turbine, layout)
    assert result.aep_gwh <= rated_capacity * 8760
```

### 3. Performance Testing

```python
import time

start = time.time()
result = run_new_framework_analysis()
duration = time.time() - start

print(f"Analysis completed in {duration:.2f} seconds")
assert duration < 60  # Should complete in under 1 minute
```

## Troubleshooting

### Issue 1: Import Errors

**Error**: `ModuleNotFoundError: No module named 'latam_hybrid'`

**Solution**:
```bash
cd /path/to/latam-hybrid
pip install -e .
```

### Issue 2: Data Format Mismatch

**Error**: `ValueError: Expected DatetimeIndex, got Int64Index`

**Solution**: Use built-in loaders with automatic parsing
```python
# Instead of:
data = pd.read_csv("data.csv")

# Use:
from latam_hybrid.input import load_wind_data
data = load_wind_data("data.csv")  # Handles parsing automatically
```

### Issue 3: Different Results

**Possible Causes**:
1. Time zone differences
2. Different wake models
3. Different loss assumptions
4. Rounding differences

**Solution**: Check assumptions
```python
# Compare intermediate steps
print(f"Legacy wind speed: {legacy_ws}")
print(f"New wind speed: {new_result.wind_speed}")

# Check wake losses
print(f"Legacy wake losses: {legacy_wake_loss}")
print(f"New wake losses: {new_result.wake_losses}")
```

## Gradual Migration Strategy

### Phase 1: Start with New Projects

Use the new framework for all new analyses while keeping legacy code for existing projects.

### Phase 2: Migrate High-Value Scripts

Identify frequently-used scripts and migrate them first:
1. Feasibility studies
2. Scenario comparisons
3. Standard reports

### Phase 3: Refactor Legacy Projects

Gradually migrate existing projects when they need updates.

### Phase 4: Archive Legacy Code

Once all projects are migrated, move legacy code to `legacy/` directory.

## Benefits Summary

| Aspect | Legacy | New Framework |
|--------|--------|---------------|
| Lines of Code | ~5000 lines scattered | ~3000 lines organized |
| Test Coverage | 0% | 77% |
| Documentation | Minimal | Comprehensive |
| Modularity | Low | High |
| Reusability | Difficult | Easy |
| Maintainability | Hard | Easy |
| Type Safety | None | Full type hints |
| Error Handling | Basic | Comprehensive |
| Performance | Variable | Optimized |

## Getting Help

1. **Documentation**: Check `docs/` for detailed guides
2. **Examples**: Review `examples/` for working code
3. **Tests**: Look at `tests/` to see how features work
4. **API Reference**: See `docs/api_reference.md`

## Next Steps

1. ✅ Read this migration guide
2. ✅ Install new framework
3. ✅ Try quick_feasibility_study with your data
4. ✅ Compare outputs with legacy code
5. ✅ Migrate one script at a time
6. ✅ Write tests for migrated code
7. ✅ Archive legacy code when confident

---

**Questions?** Open an issue on GitHub or check the documentation.

**Found a bug during migration?** Please report it so we can help others!
