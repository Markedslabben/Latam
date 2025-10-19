# Path Updates Summary

## What Changed

With `Inputdata/` now inside `latam_hybrid/`, all file paths needed to be updated to use the new location.

---

## Solution: Path Helper Utilities

Created a comprehensive path utilities module to make accessing data files easy and maintainable.

### New Module

**`latam_hybrid/core/paths.py`**
- Helper functions for accessing data files
- Platform-independent path handling
- Automatic validation
- Type-safe Path objects

---

## Quick Usage

### Import Path Helpers

```python
from latam_hybrid.core import (
    get_wind_data_file,
    get_solar_data_file,
    get_turbine_file,
    get_layout_file,
    get_gis_file,
    get_price_file,
    list_data_files
)
```

### Load Data Files

```python
# Wind data
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# Solar data
solar_file = get_solar_data_file()  # Uses default "PVGIS timeseries.csv"

# Turbine
turbine_file = get_turbine_file()  # Uses default "Nordex N164.csv"

# Layout
layout_file = get_layout_file("Turbine_layout_13.csv")

# GIS
gis_file = get_gis_file("Planningarea.gpkg")

# Prices
price_file = get_price_file()  # Uses default price file
```

---

## Files Updated

### 1. ✅ Created Path Utilities
- **`latam_hybrid/core/paths.py`** - Path helper functions
- **`latam_hybrid/core/__init__.py`** - Export path utilities

### 2. ✅ Updated Scripts
- **`scripts/check_leap_years.py`** - Now uses `get_wind_data_file()`
- **`scripts/check_pvgis_leap_years.py`** - Now uses `get_solar_data_file()`
- **`scripts/compare_winddata.py`** - Now uses `get_wind_data_file()`

### 3. ✅ Created Documentation
- **`latam_hybrid/docs/DATA_PATHS_GUIDE.md`** - Complete path usage guide

---

## Path Helper Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `get_package_root()` | Get latam_hybrid directory | `/path/to/latam_hybrid` |
| `get_data_dir()` | Get Inputdata directory | `/path/to/latam_hybrid/Inputdata` |
| `get_data_file(filename, subdir)` | Get any data file | General purpose |
| `get_wind_data_file(filename)` | Get wind data file | Vortex files |
| `get_solar_data_file(filename)` | Get solar data file | PVGIS files |
| `get_turbine_file(filename)` | Get turbine spec file | Nordex N164 |
| `get_layout_file(filename)` | Get layout file | Turbine layouts |
| `get_gis_file(filename)` | Get GIS file | From GISdata/ |
| `get_price_file(filename)` | Get price file | Market prices |
| `list_data_files(subdir, pattern)` | List matching files | Discovery |

---

## Benefits

### ✅ Before (Hardcoded Paths)

```python
# ❌ Platform-specific, breaks if structure changes
wind_file = "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
wind_file = r"C:\Users\klaus\klauspython\Latam\Inputdata\vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
```

**Problems**:
- Platform-specific (Windows vs Linux paths)
- Breaks if data moves
- Hard to maintain
- No validation

### ✅ After (Path Helpers)

```python
# ✅ Platform-independent, self-validating
from latam_hybrid.core import get_wind_data_file
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
```

**Benefits**:
- Works on any platform
- Automatic validation
- Single place to update if structure changes
- Type-safe Path objects
- Clear error messages

---

## Example: Complete Analysis

```python
from latam_hybrid.input import load_wind_data, load_solar_data
from latam_hybrid.core import get_wind_data_file, get_solar_data_file

# Get file paths using helpers
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
solar_file = get_solar_data_file()

# Load data
wind_data = load_wind_data(str(wind_file))
solar_data = load_solar_data(str(solar_file))

# Now use data in analysis...
```

---

## Migration Guide

### Old Code (Don't Use)

```python
# ❌ OLD - Hardcoded paths
wind_file = "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
solar_file = "Inputdata/PVGIS timeseries.csv"
turbine_file = "Inputdata/Nordex N164.csv"
layout_file = "Inputdata/Turbine_layout_13.csv"
gis_file = "Inputdata/GISdata/Planningarea.gpkg"
```

### New Code (Use This)

```python
# ✅ NEW - Path helpers
from latam_hybrid.core import (
    get_wind_data_file,
    get_solar_data_file,
    get_turbine_file,
    get_layout_file,
    get_gis_file
)

wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
solar_file = get_solar_data_file()  # Uses default
turbine_file = get_turbine_file()  # Uses default
layout_file = get_layout_file("Turbine_layout_13.csv")
gis_file = get_gis_file("Planningarea.gpkg")
```

---

## Available Data Files

### Wind Data (Vortex ERA5)
```python
# 10-year dataset
get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# 6-month dataset
get_wind_data_file("vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt")
```

### Solar Data (PVGIS)
```python
get_solar_data_file()  # "PVGIS timeseries.csv"
```

### Turbine Models
```python
get_turbine_file()  # "Nordex N164.csv"
```

### Turbine Layouts
```python
get_layout_file("Turbine_layout_13.csv")
get_layout_file("Turbine_layout_14.csv")
get_layout_file("Turbine_layout_18.csv")
get_layout_file("Turbine layout group 1.csv")
get_layout_file("Turbine layout group 2.csv")
```

### GIS Data
```python
get_gis_file("Planningarea.gpkg")
get_gis_file("Dominikanske republikk.gpkg")
get_gis_file("Export Latam.gpkg")
get_gis_file("Turbine layout 14.shp")  # Shapefiles
```

### Market Prices
```python
get_price_file()  # "Electricity price 2024 grid node.csv"
get_price_file("20250505 Spotmarket Prices_2024.xlsx")
```

---

## File Discovery

List all available files:

```python
from latam_hybrid.core import list_data_files

# All files in Inputdata
all_files = list_data_files()

# All CSV files
csv_files = list_data_files(pattern="*.csv")

# All turbine layouts
layouts = list_data_files(pattern="Turbine_layout_*.csv")

# All GIS files
gis_files = list_data_files(subdir="GISdata", pattern="*.gpkg")

# Print available layouts
print("Available turbine layouts:")
for layout in layouts:
    print(f"  - {layout.name}")
```

---

## Directory Structure

```
latam_hybrid/
├── Inputdata/                               ← Data inside package
│   ├── vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt
│   ├── vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt
│   ├── PVGIS timeseries.csv
│   ├── Nordex N164.csv
│   ├── Turbine_layout_13.csv
│   ├── Turbine_layout_14.csv
│   ├── Turbine_layout_18.csv
│   ├── Turbine layout group 1.csv
│   ├── Turbine layout group 2.csv
│   ├── Electricity price 2024 grid node.csv
│   ├── 20250505 Spotmarket Prices_2024.xlsx
│   └── GISdata/
│       ├── Planningarea.gpkg
│       ├── Dominikanske republikk.gpkg
│       └── Export Latam.gpkg
│
├── core/
│   └── paths.py                             ← Path helper functions
│
└── docs/
    └── DATA_PATHS_GUIDE.md                  ← Complete guide
```

---

## Remaining Updates Needed

### Tests
Some test files may still have hardcoded paths. These will be updated to use path helpers:

```python
# ❌ Old test code
def test_load_wind_data():
    wind_data = load_wind_data("Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# ✅ New test code
def test_load_wind_data():
    from latam_hybrid.core import get_wind_data_file
    wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
    wind_data = load_wind_data(str(wind_file))
```

---

## Summary

✅ **Created**: Path helper utilities module
✅ **Updated**: 3 utility scripts to use new paths
✅ **Created**: Complete documentation guide
✅ **Benefits**: Platform-independent, maintainable, validated paths

**Next Step**: Update any remaining hardcoded paths in tests and examples.

---

## Quick Reference

```python
# Import
from latam_hybrid.core import get_wind_data_file, get_solar_data_file

# Use
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
solar_file = get_solar_data_file()

# Load
from latam_hybrid.input import load_wind_data, load_solar_data
wind_data = load_wind_data(str(wind_file))
solar_data = load_solar_data(str(solar_file))
```

**Documentation**: See `latam_hybrid/docs/DATA_PATHS_GUIDE.md` for complete guide.
