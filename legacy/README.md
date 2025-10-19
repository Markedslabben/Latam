# Legacy Code Archive

This directory contains the original scattered Python scripts and modules that were replaced by the new `latam_hybrid` framework.

**Archive Date**: October 18, 2025

---

## What's Archived Here

### old_scripts/ - Legacy Root-Level Scripts (23 files)

Scattered Python scripts that were previously in the root directory:

**Shading Analysis**:
- `calculate_annual_loss.py` - Annual shading loss calculations
- `shading_loss.py` - Shading loss computations
- `shading_analysis.py` - Shading analysis workflow
- `site_shading_analysis.py` - Site-specific shading

**Wind Analysis**:
- `wind_energy_estimate.py` - Wind energy calculations
- `windfarm_layout.py` - Layout management
- `windfarmsim.py` - Wind farm simulation

**Plotting & Visualization**:
- `plot_example.py` - Example plots
- `plot_shading_results.py` - Shading result plots
- `gis_visualization.py` - GIS visualization

**Utility Scripts**:
- `calculate_example.py` - Example calculations
- `draft.py` - Draft testing script
- `testfunction.py` - Test functions
- `create_notebook.py` - Notebook creation
- `list_layers.py` - GIS layer listing
- `pv_battery_lp.py` - Battery optimization

**Test Scripts**:
- `test_create_nordex_n164_turbine.py`
- `test_create_xrsite_from_vortex.py`
- `test_geopandas.py`

**Examples & Experiments**:
- `example_new_workflow.py` - Workflow example
- `test_fixed_issues.py` - Issue testing
- `wind_analysis_with_klaus_plots.py` - Wind analysis with plotting
- `working_wind_example.py` - Working example

### old_modules/ - Legacy Module Directories

Scattered module directories that were previously in the root:

**PV_galvian/**:
- `pv_production_calculator.py` - Solar production calculations
- `read_pvgis.py` - PVGIS data reader

**turbine_galvian/**:
- `create_turbine.py` - Turbine model creation
- `read_windturbine.py` - Turbine data reader

**site_galvian/**:
- `site_galvian.py` - Site analysis

**simulation/**:
- `production_years.py` - Multi-year production
- `results.py` - Results handling
- `run_simulation_weibull.py` - Weibull simulation

### old_outputs/ - Legacy Output Files

Old CSV output files that were previously in the root:
- Various `.csv` result files from legacy scripts

---

## Why These Were Archived

### Problems with Legacy Structure

❌ **No Organization**: Files scattered in root directory
❌ **No Clear Boundaries**: Mixed concerns (data + calculation + plotting)
❌ **No Reusability**: Functions buried in scripts
❌ **No Testing**: 0% test coverage
❌ **No Documentation**: Minimal inline comments only
❌ **Hard to Maintain**: Changes require editing multiple files
❌ **No Type Safety**: No type hints
❌ **Difficult to Use**: No clear API or entry points

### Replaced By

✅ **Organized Package**: `latam_hybrid/` with clear module boundaries
✅ **Professional API**: Method chaining and fluent interfaces
✅ **High Test Coverage**: 77% coverage with 364 tests
✅ **Type Safety**: Full type hints throughout
✅ **Comprehensive Docs**: README, migration guide, API reference
✅ **Easy to Maintain**: Modular design makes changes simple
✅ **Reusable**: Import and use anywhere

---

## Mapping: Old → New

### Shading Calculations

**Old**: `shading_loss.py`, `calculate_annual_loss.py`
**New**: `latam_hybrid/solar/shading.py`

```python
# Old way
from shading_loss import calculate_annual_shading_loss
annual_results, annual_loss = calculate_annual_shading_loss(...)

# New way
from latam_hybrid.solar import ShadingCalculator
calculator = ShadingCalculator(...)
annual_loss = calculator.calculate_annual_loss(...)
```

### Wind Analysis

**Old**: `wind_energy_estimate.py`, `windfarmsim.py`
**New**: `latam_hybrid/wind/site.py`, `latam_hybrid/wind/turbine.py`

```python
# Old way - scattered across multiple files

# New way
from latam_hybrid.wind import load_turbine, load_layout, create_wind_site
turbine = load_turbine("turbine.csv")
layout = load_layout("layout.csv")
wind_site = create_wind_site("wind_data.nc")
result = wind_site.set_turbine(turbine).set_layout(layout).run_simulation()
```

### Solar Production

**Old**: `PV_galvian/pv_production_calculator.py`
**New**: `latam_hybrid/solar/site.py`, `latam_hybrid/solar/system.py`

```python
# Old way - manual calculations in scripts

# New way
from latam_hybrid.solar import create_solar_system, create_solar_site
solar_system = create_solar_system("PV System", capacity_mw=10)
solar_site = create_solar_site("solar_data.csv")
result = solar_site.set_system(solar_system).calculate_production()
```

### Data Loading

**Old**: `turbine_galvian/read_windturbine.py`, `PV_galvian/read_pvgis.py`
**New**: `latam_hybrid/input/` module

```python
# Old way - scattered readers

# New way
from latam_hybrid.input import (
    load_wind_data,
    load_solar_data,
    load_turbine,
    load_layout
)
```

### Complete Analysis

**Old**: Manual orchestration across 5+ scripts
**New**: `latam_hybrid/hybrid/workflows.py`

```python
# Old way - run multiple scripts manually

# New way - single function
from latam_hybrid import quick_feasibility_study
result = quick_feasibility_study(
    project_name="Project",
    wind_capacity_mw=50,
    solar_capacity_mw=10,
    annual_wind_production_gwh=150,
    annual_solar_production_gwh=30,
    electricity_price=55
)
```

---

## Migration Guide

For detailed migration instructions, see:
- `docs/migration_guide.md` - Complete migration guide
- `README.md` - New framework overview
- `claudedocs/BEFORE_AFTER_COMPARISON.md` - Detailed comparison

---

## Should You Delete This?

**NO - Keep for Reference**

Reasons to keep legacy code:
1. **Historical Reference**: See how things used to work
2. **Algorithm Verification**: Compare old vs new calculations
3. **Code Salvaging**: May contain useful logic not yet migrated
4. **Documentation**: Shows evolution of the project

**When to Delete**:
- After verifying new framework produces identical results
- After migrating all useful algorithms
- After 6-12 months of successful new framework usage

---

## Statistics

| Metric | Legacy | New Framework |
|--------|--------|---------------|
| **Files** | 23 scripts + 4 modules | 26 organized modules |
| **Lines** | ~5,000 scattered | 2,916 organized |
| **Test Coverage** | 0% | 77% |
| **Documentation** | Minimal | Comprehensive |
| **Maintainability** | Low | High |
| **Reusability** | Difficult | Easy |

---

## Archive Structure

```
legacy/
├── README.md                  (this file)
├── old_scripts/               (23 root-level Python scripts)
├── old_modules/               (4 legacy module directories)
│   ├── PV_galvian/
│   ├── turbine_galvian/
│   ├── site_galvian/
│   └── simulation/
└── old_outputs/               (old CSV result files)
```

---

**Archived**: October 18, 2025
**Replaced By**: `latam_hybrid` framework (version 0.1.0)
**Status**: Preserved for reference, not for active development
