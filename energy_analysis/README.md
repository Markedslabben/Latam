# Energy Analysis Package

A modern, object-oriented wrapper around existing wind and solar energy analysis functions. This package solves the common pain points of functional workflows while preserving all existing functionality.

## 🎯 Problem Solved

**Before (Functional Approach):**
- ❌ Constant `importlib.reload()` needed when developing
- ❌ Manual function sequencing and parameter passing
- ❌ Scattered configuration across multiple files
- ❌ No state management between analysis steps
- ❌ Difficult to use in Jupyter notebooks

**After (Object-Oriented Approach):**
- ✅ No module reloading needed - state maintained in objects
- ✅ Method chaining for clean, readable workflows
- ✅ Automatic data flow between analysis steps
- ✅ Centralized configuration management
- ✅ Jupyter-friendly interactive analysis
- ✅ Backward compatible with existing functions

## 🚀 Quick Start

### Simple One-Liner Analysis
```python
from energy_analysis import HybridEnergyAnalysis

# Complete analysis with defaults
analysis = HybridEnergyAnalysis.quick_analysis()
analysis.print_summary()
```

### Method Chaining Workflow
```python
from energy_analysis import HybridEnergyAnalysis

# Create analysis instance
analysis = HybridEnergyAnalysis.from_defaults()

# Wind analysis with method chaining
wind_results = (analysis.wind
               .load_turbine()
               .create_site()
               .load_layout()
               .setup_wind_farm_model()
               .run_simulation()
               .process_results())

# Solar analysis with method chaining
solar_results = (analysis.solar
                .load_pvgis_data()
                .analyze_shading()
                .process_results())

# Combine and export
analysis.combine_results()
analysis.export_results()
```

## 📁 Package Structure

```
energy_analysis/
├── __init__.py          # Main package exports
├── config.py            # Configuration management
├── wind_pipeline.py     # Wind energy analysis pipeline
├── solar_pipeline.py    # Solar energy analysis pipeline
├── hybrid_analysis.py   # Combined wind+solar analysis
└── README.md           # This file
```

## 🔧 Core Classes

### `AnalysisConfig`
Centralized configuration management for all analysis parameters.

```python
config = AnalysisConfig()
config.site.latitude = 19.71814
config.site.longitude = -71.35602
config.wind.start_year = 2020
config.wind.wake_model = "BastankhahGaussianDeficit"
config.solar.installed_capacity_MW = 150.0
```

### `WindEnergyPipeline`
Object-oriented wrapper for wind energy analysis.

```python
wind = WindEnergyPipeline(wind_config, site_config)
results = (wind
          .load_turbine()
          .create_site()
          .load_layout()
          .setup_wind_farm_model()
          .run_simulation()
          .process_results())
```

### `SolarEnergyPipeline`
Object-oriented wrapper for solar energy analysis.

```python
solar = SolarEnergyPipeline(solar_config, site_config, shading_config)
results = (solar
          .load_pvgis_data()
          .analyze_shading()
          .process_results())
```

### `HybridEnergyAnalysis`
Main class combining wind and solar analysis.

```python
analysis = HybridEnergyAnalysis(config)
analysis.run_full_analysis()
analysis.print_summary()
analysis.export_results()
```

## 📊 Features

### State Management
- Objects maintain state between method calls
- No need to reload modules during development
- Results automatically passed between pipeline steps

### Method Chaining
- Fluent interface for readable workflows
- Each method returns `self` for chaining
- Optional step-by-step execution

### Configuration Management
- Centralized parameter control via `AnalysisConfig`
- Hierarchical configuration structure
- Easy customization and validation

### Error Handling
- Comprehensive input validation
- Clear error messages with suggestions
- Graceful handling of missing files

### Result Organization
- Structured storage of all analysis results
- Automatic metadata tracking
- Easy export to multiple formats

### Jupyter Integration
- Perfect for interactive analysis
- Rich display of results and summaries
- Easy plotting and visualization

## 🔄 Migration from Functional Code

Your existing functional code still works! The new system wraps your functions without changing them.

### Old Workflow
```python
import importlib
importlib.reload(turbine_galvian.create_turbine)
importlib.reload(site_galvian.create_site)

turbine = create_nordex_n164_turbine("Inputdata/Nordex N164.csv")
site = create_site_from_vortex("Inputdata/vortex.serie...", start="2014-01-01")
layout = pd.read_csv("Inputdata/turbine_layout_13.csv")
x = layout["x_coord"].values
y = layout["y_coord"].values
wfm = PropagateDownwind(site, turbine, wake_deficitModel=NoWakeDeficit())
sim_res = wfm(x, y, wd=wd, ws=ws, time=times)
# ... manual result processing
```

### New Workflow
```python
analysis = HybridEnergyAnalysis.from_defaults()
analysis.run_full_analysis()
analysis.print_summary()
```

## 📋 Requirements

The package uses your existing dependencies:
- pandas
- numpy
- xarray
- py-wake
- pvlib (for solar analysis)
- geopandas (for GIS functionality)
- matplotlib (for plotting)

## 🎓 Examples

### Complete Examples
- `example_new_workflow.py` - Comprehensive workflow demonstration
- `demo_hybrid_analysis.ipynb` - Jupyter notebook tutorial

### Quick Examples

#### Wind-Only Analysis
```python
from energy_analysis import HybridEnergyAnalysis

analysis = HybridEnergyAnalysis.from_defaults()
analysis.run_wind_analysis()
wind_summary = analysis.wind.get_summary()
print(f"Annual wind energy: {wind_summary['results_summary']['annual_energy_GWh']:.2f} GWh")
```

#### Solar-Only Analysis
```python
from energy_analysis import HybridEnergyAnalysis

analysis = HybridEnergyAnalysis.from_defaults()
analysis.run_solar_analysis()
solar_summary = analysis.solar.get_summary()
print(f"Annual solar energy: {solar_summary['results_summary']['annual_energy_MWh']:.2f} MWh")
```

#### Custom Wake Model Comparison
```python
from energy_analysis import AnalysisConfig, HybridEnergyAnalysis

# No wake analysis
config_no_wake = AnalysisConfig()
config_no_wake.wind.wake_model = "NoWakeDeficit"
analysis_no_wake = HybridEnergyAnalysis(config_no_wake)
analysis_no_wake.run_wind_analysis()

# With wake analysis
config_wake = AnalysisConfig()
config_wake.wind.wake_model = "BastankhahGaussianDeficit"
analysis_wake = HybridEnergyAnalysis(config_wake)
analysis_wake.run_wind_analysis()

# Compare results
no_wake_energy = analysis_no_wake.wind.results['annual_energy_GWh']
wake_energy = analysis_wake.wind.results['annual_energy_GWh']
wake_loss = (no_wake_energy - wake_energy) / no_wake_energy * 100

print(f"Wake loss: {wake_loss:.1f}%")
```

## 🤝 Backward Compatibility

All your existing functions continue to work exactly as before:

```python
# These still work!
from turbine_galvian.create_turbine import create_nordex_n164_turbine
from site_galvian.create_site import create_site_from_vortex
from PV_galvian.read_pvgis import read_pvgis

turbine = create_nordex_n164_turbine("Inputdata/Nordex N164.csv")
site = create_site_from_vortex("Inputdata/vortex.serie...")
pv_data = read_pvgis("Inputdata/PVGIS timeseries.csv")
```

The new system simply provides a more convenient interface on top of your existing code.

## 🎯 Benefits Summary

1. **Development Efficiency**: No more module reloading during development
2. **Code Readability**: Method chaining creates self-documenting workflows
3. **Error Reduction**: Automatic data flow prevents manual errors
4. **Configuration Management**: Centralized, validated parameter control
5. **Interactive Analysis**: Perfect for Jupyter notebook exploration
6. **Result Organization**: Structured storage and easy export
7. **Maintainability**: Object-oriented design for easier extension
8. **Backward Compatibility**: Existing code continues to work

## 🚀 Getting Started

1. **Try the quick example:**
   ```bash
   python example_new_workflow.py
   ```

2. **Open the demo notebook:**
   ```bash
   jupyter notebook demo_hybrid_analysis.ipynb
   ```

3. **Start with your own analysis:**
   ```python
   from energy_analysis import HybridEnergyAnalysis
   analysis = HybridEnergyAnalysis.from_defaults()
   validation = analysis.validate_setup()
   # Check validation results and run analysis
   ```

The new system will guide you through any missing files or configuration issues! 