# Data Paths Guide

## Overview

With Inputdata now inside the `latam_hybrid/` package, we provide convenient path utilities to access data files without hardcoding paths.

---

## Quick Start

### Import Path Utilities

```python
from latam_hybrid.core import (
    get_data_dir,
    get_wind_data_file,
    get_solar_data_file,
    get_turbine_file,
    get_layout_file,
    get_gis_file,
    get_price_file
)
```

### Load Data Files

```python
# Wind data
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# Solar data
solar_file = get_solar_data_file()  # Defaults to "PVGIS timeseries.csv"

# Turbine specification
turbine_file = get_turbine_file()  # Defaults to "Nordex N164.csv"

# Turbine layout
layout_file = get_layout_file("Turbine_layout_13.csv")

# GIS files
gis_file = get_gis_file("Planningarea.gpkg")

# Price data
price_file = get_price_file()  # Defaults to "Electricity price 2024 grid node.csv"
```

---

## Complete API Reference

### get_package_root()
Returns the root directory of the latam_hybrid package.

```python
from latam_hybrid.core import get_package_root

root = get_package_root()
print(root)  # /path/to/latam_hybrid
```

### get_data_dir()
Returns the Inputdata directory within the package.

```python
from latam_hybrid.core import get_data_dir

data_dir = get_data_dir()
print(data_dir)  # /path/to/latam_hybrid/Inputdata
```

### get_data_file(filename, subdir=None)
Get absolute path to any data file.

```python
from latam_hybrid.core import get_data_file

# Top-level data file
wind_file = get_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# File in subdirectory
gis_file = get_data_file("Planningarea.gpkg", subdir="GISdata")
```

### get_wind_data_file(filename)
Get path to wind data file.

```python
from latam_hybrid.core import get_wind_data_file

# 10-year dataset
wind_10y = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# 6-month dataset
wind_6m = get_wind_data_file("vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt")
```

### get_solar_data_file(filename="PVGIS timeseries.csv")
Get path to solar data file.

```python
from latam_hybrid.core import get_solar_data_file

# Use default filename
solar_file = get_solar_data_file()

# Or specify custom filename
solar_custom = get_solar_data_file("my_pvgis_data.csv")
```

### get_turbine_file(filename="Nordex N164.csv")
Get path to turbine specification file.

```python
from latam_hybrid.core import get_turbine_file

# Use default Nordex N164
turbine = get_turbine_file()

# Or specify different turbine
turbine_custom = get_turbine_file("Vestas_V164.csv")
```

### get_layout_file(filename)
Get path to turbine layout file.

```python
from latam_hybrid.core import get_layout_file

layout = get_layout_file("Turbine_layout_13.csv")
```

### get_gis_file(filename)
Get path to GIS file in GISdata subdirectory.

```python
from latam_hybrid.core import get_gis_file

# GeoPackage
planning_area = get_gis_file("Planningarea.gpkg")

# Shapefile (will find .shp and associated files)
layout_shp = get_gis_file("Turbine layout 14.shp")
```

### get_price_file(filename="Electricity price 2024 grid node.csv")
Get path to electricity price file.

```python
from latam_hybrid.core import get_price_file

# Use default filename
prices = get_price_file()

# Or specify custom price file
prices_custom = get_price_file("2024_spotmarket_prices.xlsx")
```

### list_data_files(subdir=None, pattern="*")
List all files matching pattern in Inputdata directory.

```python
from latam_hybrid.core import list_data_files

# List all files
all_files = list_data_files()

# List all CSV files
csv_files = list_data_files(pattern="*.csv")

# List all turbine layouts
layouts = list_data_files(pattern="Turbine_layout_*.csv")

# List all GIS files
gis_files = list_data_files(subdir="GISdata", pattern="*.gpkg")
```

---

## Constants

Pre-calculated path constants for convenience:

```python
from latam_hybrid.core import PACKAGE_ROOT, DATA_DIR, GIS_DATA_DIR

print(f"Package root: {PACKAGE_ROOT}")
print(f"Data directory: {DATA_DIR}")
print(f"GIS data directory: {GIS_DATA_DIR}")
```

---

## Usage Examples

### Example 1: Load Wind Data

```python
from latam_hybrid.input import load_wind_data
from latam_hybrid.core import get_wind_data_file

# Get file path
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# Load data
wind_data = load_wind_data(str(wind_file))
```

### Example 2: Load All Data for Analysis

```python
from latam_hybrid.input import (
    load_wind_data,
    load_solar_data,
    load_turbine,
    load_layout,
    load_gis_data,
    load_market_data
)
from latam_hybrid.core import (
    get_wind_data_file,
    get_solar_data_file,
    get_turbine_file,
    get_layout_file,
    get_gis_file,
    get_price_file
)

# Get all file paths
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
solar_file = get_solar_data_file()
turbine_file = get_turbine_file()
layout_file = get_layout_file("Turbine_layout_13.csv")
gis_file = get_gis_file("Planningarea.gpkg")
price_file = get_price_file()

# Load all data
wind_data = load_wind_data(str(wind_file))
solar_data = load_solar_data(str(solar_file))
turbine = load_turbine(str(turbine_file))
layout = load_layout(str(layout_file))
planning_area = load_gis_data(str(gis_file))
prices = load_market_data(str(price_file))
```

### Example 3: List Available Layouts

```python
from latam_hybrid.core import list_data_files

# Find all turbine layouts
layouts = list_data_files(pattern="Turbine_layout_*.csv")

print("Available turbine layouts:")
for layout in layouts:
    print(f"  - {layout.name}")
```

### Example 4: Dynamic File Discovery

```python
from latam_hybrid.core import list_data_files, get_data_file

# Find the 10-year wind dataset automatically
wind_files = list_data_files(pattern="vortex.serie.*.10y*.txt")

if wind_files:
    wind_file = wind_files[0]
    print(f"Using wind data: {wind_file}")
else:
    raise FileNotFoundError("No 10-year wind dataset found")
```

---

## Migration from Old Paths

### Before (Hardcoded Paths)

```python
# ❌ OLD WAY - Don't use this anymore
wind_file = "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
solar_file = "Inputdata/PVGIS timeseries.csv"
turbine_file = "Inputdata/Nordex N164.csv"
```

### After (Path Helpers)

```python
# ✅ NEW WAY - Use path helpers
from latam_hybrid.core import (
    get_wind_data_file,
    get_solar_data_file,
    get_turbine_file
)

wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
solar_file = get_solar_data_file()
turbine_file = get_turbine_file()
```

---

## Benefits

### ✅ Platform Independent
Works on Windows, macOS, Linux without path separator issues.

### ✅ Package Relative
Paths are relative to package installation, not current working directory.

### ✅ Validation
Raises clear errors if files don't exist.

### ✅ Type Safe
Returns Path objects for better IDE support.

### ✅ Maintainable
If data structure changes, update once in paths.py.

---

## Error Handling

```python
from latam_hybrid.core import get_data_file

try:
    wind_file = get_wind_data_file("nonexistent_file.txt")
except FileNotFoundError as e:
    print(f"File not found: {e}")
    # Handle error appropriately
```

---

## Directory Structure

```
latam_hybrid/
└── Inputdata/
    ├── vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt
    ├── vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt
    ├── PVGIS timeseries.csv
    ├── Nordex N164.csv
    ├── Turbine_layout_13.csv
    ├── Turbine_layout_14.csv
    ├── Turbine_layout_18.csv
    ├── Turbine layout group 1.csv
    ├── Turbine layout group 2.csv
    ├── Electricity price 2024 grid node.csv
    ├── 20250505 Spotmarket Prices_2024.xlsx
    └── GISdata/
        ├── Planningarea.gpkg
        ├── Dominikanske republikk.gpkg
        ├── Export Latam.gpkg
        └── *.shp, *.dbf, *.prj (shapefiles)
```

---

## Best Practices

### 1. Always Use Path Helpers

```python
# ✅ Good
from latam_hybrid.core import get_wind_data_file
wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# ❌ Bad
wind_file = "latam_hybrid/Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
```

### 2. Convert to String When Needed

```python
from latam_hybrid.core import get_wind_data_file
from latam_hybrid.input import load_wind_data

wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

# Convert Path to string for pandas/loaders
wind_data = load_wind_data(str(wind_file))
```

### 3. Use Default Arguments

```python
# ✅ Good - uses default
solar_file = get_solar_data_file()
turbine_file = get_turbine_file()

# ❌ Unnecessary - only specify if different
solar_file = get_solar_data_file("PVGIS timeseries.csv")
```

### 4. List Files for Discovery

```python
# ✅ Good - discover available files
layouts = list_data_files(pattern="Turbine_layout_*.csv")
for layout in layouts:
    print(layout.name)

# ❌ Bad - hardcode all layouts
layout_13 = get_layout_file("Turbine_layout_13.csv")
layout_14 = get_layout_file("Turbine_layout_14.csv")
# ...
```

---

## Summary

**Path helpers make your code:**
- ✅ Platform independent
- ✅ Maintainable
- ✅ Self-documenting
- ✅ Error-resistant

**Always prefer path helpers over hardcoded paths!**
