# Latam Hybrid Energy Analysis Framework

A comprehensive Python framework for analyzing hybrid wind-solar energy systems, with a focus on projects in the Latin American region.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Coverage](https://img.shields.io/badge/coverage-77%25-yellowgreen.svg)](docs/testing.md)

## Overview

**Latam Hybrid** provides a clean, modular architecture for:
- Wind farm analysis with wake modeling (pywake integration)
- Solar PV production analysis (pvlib integration)
- Turbine-to-panel shading calculations
- Geospatial analysis and visualization
- Financial analysis (LCOE, NPV, IRR)
- Multi-format results export and reporting
- Complete end-to-end hybrid project workflows

### Key Features

- **Clean Architecture**: Separation between data loading, calculations, and output
- **Method Chaining**: Fluent API for building analysis pipelines
- **Generic Design**: Works with any wind/solar project worldwide
- **Comprehensive Testing**: 77% test coverage, 364 tests
- **Type Hints**: Full type annotations for better IDE support
- **Frozen Dataclasses**: Immutable data structures for reliability

## Installation

### Prerequisites

- Python 3.10 or higher
- Conda (recommended for managing dependencies)

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/latam-hybrid.git
cd latam-hybrid

# Create conda environment
conda env create -f environment.yaml
conda activate latam

# Install the package
pip install -e .
```

### With Development Tools

```bash
# Install with development dependencies
pip install -e ".[dev]"
```

### Optional Dependencies

```bash
# Visualization tools
pip install -e ".[visualization]"

# Documentation tools
pip install -e ".[docs]"

# pywake (must be installed via conda)
conda install -c conda-forge py_wake
```

## Quick Start

### Simple Feasibility Study

```python
from latam_hybrid import quick_feasibility_study

# Run quick feasibility analysis
result = quick_feasibility_study(
    project_name="Chile Hybrid 1",
    wind_capacity_mw=50,
    solar_capacity_mw=10,
    annual_wind_production_gwh=150,
    annual_solar_production_gwh=30,
    electricity_price=55,  # USD/MWh
    location="Antofagasta, Chile"
)

# Check results
print(f"Total AEP: {result.production.total_aep_gwh:.1f} GWh")
print(f"LCOE: {result.economics.lcoe:.2f} USD/MWh")
print(f"NPV: {result.economics.npv/1e6:.1f} MUSD")
print(f"IRR: {result.economics.irr:.1%}")
```

### Scenario Comparison

```python
from latam_hybrid import compare_scenarios

# Define base scenario
base = {
    'project_name': 'Base',
    'wind_capacity_mw': 50,
    'solar_capacity_mw': 10,
    'annual_wind_production_gwh': 150,
    'annual_solar_production_gwh': 30,
    'electricity_price': 50
}

# Define alternatives
scenarios = {
    'High Price': {'electricity_price': 60},
    'Low Price': {'electricity_price': 40},
    'More Wind': {'wind_capacity_mw': 75, 'annual_wind_production_gwh': 225}
}

# Compare
comparison = compare_scenarios(base, scenarios, output_dir="output/")
print(comparison)
```

### Complete Hybrid Analysis

```python
from latam_hybrid import HybridAnalysis
from latam_hybrid.wind import load_turbine, load_layout, create_wind_site
from latam_hybrid.solar import create_solar_system, create_solar_site
from latam_hybrid.economics import create_hybrid_economics

# Load components
turbine = load_turbine("path/to/turbine.csv")
layout = load_layout("path/to/layout.csv")
wind_site = create_wind_site("path/to/wind_data.nc")
solar_system = create_solar_system("PV System", capacity_mw=10)
solar_site = create_solar_site("path/to/solar_data.csv")

# Configure economics
economics = create_hybrid_economics(
    wind_capacity_mw=50,
    solar_capacity_mw=10,
    electricity_price=55
)

# Run analysis
analysis = (
    HybridAnalysis(project_name="Chile Hybrid 1", location="Antofagasta")
    .configure_wind(turbine, layout, wind_site, wake_model="NOJ")
    .configure_solar(solar_system, solar_site)
    .configure_economics(economics)
    .run()
)

# Export results
analysis.export_results("output/", formats=['json', 'excel', 'markdown'])
analysis.save_report("output/report.md", format='markdown')
```

## Project Structure

```
latam-hybrid/
├── latam_hybrid/           # Main package
│   ├── core/              # Core data models and utilities
│   ├── input/             # Data loaders
│   ├── wind/              # Wind analysis
│   ├── solar/             # Solar analysis
│   ├── gis/               # Geospatial operations
│   ├── economics/         # Financial calculations
│   ├── output/            # Results and reporting
│   └── hybrid/            # Orchestration and workflows
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                  # Documentation
├── examples/              # Usage examples
└── legacy/               # Archived legacy code
```

## Core Modules

### Data Models (`latam_hybrid.core`)
- Frozen dataclasses for wind, solar, GIS, and market data
- Time alignment services for heterogeneous data sources
- Comprehensive data validation

### Wind Analysis (`latam_hybrid.wind`)
- Turbine model management
- Layout optimization
- Wake modeling (pywake integration)
- Production calculations

### Solar Analysis (`latam_hybrid.solar`)
- PV system configuration
- Solar site analysis (pvlib integration)
- Turbine shading calculations
- System loss modeling

### GIS Operations (`latam_hybrid.gis`)
- Planning area management
- Spatial utilities (distance, bearing, setbacks)
- Visualization (optional matplotlib)

### Economics (`latam_hybrid.economics`)
- LCOE calculation with discounted cash flows
- NPV, IRR, payback period
- Revenue modeling (flat, ToD, seasonal, merchant)
- Sensitivity analysis and Monte Carlo

### Output (`latam_hybrid.output`)
- Result aggregation
- Multi-format export (JSON, CSV, Excel)
- Report generation (text, markdown)
- Executive summaries

### Hybrid Orchestration (`latam_hybrid.hybrid`)
- `HybridAnalysis` class with fluent API
- Pre-built workflows
- Scenario comparison tools

## Documentation

- **[Getting Started Guide](docs/getting_started.md)** - Detailed installation and setup
- **[API Reference](docs/api_reference.md)** - Complete API documentation
- **[Examples](docs/examples/)** - Usage examples and tutorials
- **[Architecture](docs/architecture.md)** - System design and patterns
- **[Testing Guide](docs/testing.md)** - Test strategy and coverage
- **[Migration Guide](docs/migration_guide.md)** - Migrating from legacy code

## Examples

See the `examples/` directory for complete working examples:

- `01_quick_feasibility.py` - Simple feasibility analysis
- `02_wind_only_analysis.py` - Wind-only project
- `03_solar_only_analysis.py` - Solar-only project
- `04_complete_hybrid.py` - Full hybrid analysis
- `05_scenario_comparison.py` - Comparing multiple scenarios
- `06_sensitivity_analysis.py` - Sensitivity and risk analysis

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=latam_hybrid --cov-report=html

# Run specific module
pytest tests/unit/test_economics.py -v

# Run integration tests only
pytest tests/integration/ -v
```

**Current Coverage**: 77% (364 tests, 349 passing)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run code formatting
black latam_hybrid/
ruff check latam_hybrid/

# Run type checking
mypy latam_hybrid/
```

## Design Principles

1. **Separation of Concerns**: Clear boundaries between data, calculations, and output
2. **Immutability**: Frozen dataclasses prevent accidental mutation
3. **Composition**: Build complex analyses from simple components
4. **Type Safety**: Comprehensive type hints for better IDE support
5. **Testability**: Pure functions and dependency injection

## Requirements

### Core Dependencies
- pandas >= 2.2.0
- numpy >= 1.26.0
- pvlib >= 0.10.0
- geopandas >= 0.14.0
- xarray >= 2024.0.0

### Optional Dependencies
- py_wake (wind wake modeling)
- matplotlib >= 3.8.0 (visualization)
- openpyxl >= 3.1.0 (Excel export)
- folium >= 0.15.0 (interactive maps)

## Roadmap

- [x] Phase 1-9: Core framework implementation
- [x] Phase 10: Documentation and migration
- [ ] Advanced optimization algorithms
- [ ] Battery storage integration
- [ ] Real-time monitoring integration
- [ ] Cloud deployment support
- [ ] Web-based dashboard

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **Klaus** - Initial work and framework design

## Acknowledgments

- **pywake** - Wind wake modeling
- **pvlib** - Solar PV modeling
- **geopandas** - Geospatial operations
- The renewable energy open-source community

## Support

For questions, issues, or feature requests, please:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Review the [examples](examples/)

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{latam_hybrid,
  title = {Latam Hybrid Energy Analysis Framework},
  author = {Klaus},
  year = {2025},
  url = {https://github.com/yourusername/latam-hybrid}
}
```

---

**Status**: Production Ready ✅
**Version**: 0.1.0
**Last Updated**: January 2025
