# Input Data Directory Structure

## Overview

All your actual input data files remain **unchanged** and are located in the `Inputdata/` directory. The new framework **reads from these same data files** - nothing was moved or changed.

---

## Primary Data Location: Inputdata/

```
Inputdata/
├── Wind Data (Vortex ERA5 time series)
│   ├── vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt      (376 KB - 6 months)
│   └── vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt     (8.3 MB - 10 years)
│
├── Solar Data (PVGIS)
│   └── PVGIS timeseries.csv                               (390 KB)
│
├── Turbine Models
│   └── Nordex N164.csv                                    (791 bytes)
│
├── Turbine Layouts
│   ├── Turbine layout group 1.csv                         (116 bytes)
│   ├── Turbine layout group 2.csv                         (116 bytes)
│   ├── Turbine_layout_13.csv                              (379 bytes)
│   ├── turbine_layout_14.csv                              (596 bytes)
│   └── turbine_layout_18.csv                              (760 bytes)
│
├── Market Data (Electricity Prices)
│   ├── 20250505 Spotmarket Prices_2024.xlsx               (4.6 MB)
│   └── Electricity price 2024 grid node.csv               (121 KB)
│
├── GISdata/                                               (GIS files)
│   ├── Dominikanske republikk.gpkg                        (468 KB - country boundaries)
│   ├── Export Latam.gpkg                                  (396 KB - Latam region)
│   ├── Planningarea.gpkg                                  (104 KB - project area)
│   │
│   ├── Turbine layout 14 shapefiles:
│   │   ├── Turbine layout 14.shp                          (shapefile geometry)
│   │   ├── Turbine layout 14.dbf                          (attributes)
│   │   ├── Turbine layout 14.prj                          (projection)
│   │   ├── Turbine layout 14.shx                          (index)
│   │   ├── Turbine layout 14.cpg                          (encoding)
│   │   └── Turbine layout 14.qmd                          (QGIS metadata)
│   │
│   ├── Turbine layout2 shapefiles:
│   │   ├── Turbine layout2.shp
│   │   ├── Turbine layout2.dbf
│   │   ├── Turbine layout2.prj
│   │   ├── Turbine layout2.shx
│   │   ├── Turbine layout2.cpg
│   │   └── Turbine layout2.qmd
│   │
│   └── planningarea shapefiles:
│       ├── planningarea.shp
│       ├── planningarea.dbf
│       ├── planningarea.prj
│       ├── planningarea.shx
│       ├── planningarea.cpg
│       └── planningarea.qmd
│
└── Legacy helper script:
    └── create_xrsite_from_vortex.py                       (Vortex data loader)
```

---

## Empty Placeholder Directory: data/

This directory structure was created as a template but is currently **empty**:

```
data/
├── gis/          (empty - placeholder)
├── market/       (empty - placeholder)
├── solar/        (empty - placeholder)
├── turbines/     (empty - placeholder)
└── wind/         (empty - placeholder)
```

**Purpose**: Optional organized structure for future data organization. Not currently used.

---

## Output Directory: output/

```
output/
└── turbine_coordinates.csv                                (763 bytes - generated output)
```

---

## How the New Framework Uses This Data

### Wind Data Loading

**Old way** (legacy scripts):
```python
# Scattered manual loading in various scripts
wind_data = pd.read_csv("Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt", ...)
```

**New framework** (automatic):
```python
from latam_hybrid.input import load_wind_data

# Automatic format detection and parsing
wind_data = load_wind_data("Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
```

### Solar Data Loading

**Old way**:
```python
# Manual PVGIS parsing
solar_data = pd.read_csv("Inputdata/PVGIS timeseries.csv", ...)
```

**New framework**:
```python
from latam_hybrid.input import load_solar_data

# Automatic time zone and format handling
solar_data = load_solar_data("Inputdata/PVGIS timeseries.csv")
```

### Turbine Models

**Old way**:
```python
# Manual turbine power curve loading
turbine_df = pd.read_csv("Inputdata/Nordex N164.csv")
```

**New framework**:
```python
from latam_hybrid.wind import load_turbine

# Creates TurbineModel object with validation
turbine = load_turbine("Inputdata/Nordex N164.csv")
```

### Turbine Layouts

**Old way**:
```python
# Manual coordinate parsing
layout_df = pd.read_csv("Inputdata/Turbine_layout_13.csv")
x = layout_df['x'].values
y = layout_df['y'].values
```

**New framework**:
```python
from latam_hybrid.wind import load_layout

# Creates TurbineLayout object with validation
layout = load_layout("Inputdata/Turbine_layout_13.csv")
```

### GIS Data

**Old way**:
```python
# Manual shapefile/geopackage loading
import geopandas as gpd
planning_area = gpd.read_file("Inputdata/GISdata/Planningarea.gpkg")
```

**New framework**:
```python
from latam_hybrid.input import load_gis_data

# Automatic format detection (shapefile, geopackage, geojson)
planning_area = load_gis_data("Inputdata/GISdata/Planningarea.gpkg")
```

### Market Data

**Old way**:
```python
# Manual price data parsing
prices = pd.read_csv("Inputdata/Electricity price 2024 grid node.csv", ...)
```

**New framework**:
```python
from latam_hybrid.input import load_market_data

# Automatic time parsing and validation
prices = load_market_data("Inputdata/Electricity price 2024 grid node.csv")
```

---

## Data Files Summary

### By Type

| Data Type | Files | Total Size | Location |
|-----------|-------|------------|----------|
| **Wind (Vortex ERA5)** | 2 files | 8.7 MB | Inputdata/ |
| **Solar (PVGIS)** | 1 file | 390 KB | Inputdata/ |
| **Turbine Models** | 1 file | 791 bytes | Inputdata/ |
| **Turbine Layouts** | 5 files | ~2 KB | Inputdata/ |
| **Market Prices** | 2 files | 4.7 MB | Inputdata/ |
| **GIS Data** | 21 files | ~1 MB | Inputdata/GISdata/ |
| **TOTAL** | **32 files** | **~15 MB** | Inputdata/ |

### By Format

| Format | Count | Examples |
|--------|-------|----------|
| **CSV** | 7 | Turbine layouts, PVGIS, prices |
| **TXT** | 2 | Vortex wind time series |
| **XLSX** | 1 | Spotmarket prices |
| **GeoPackage (.gpkg)** | 3 | Planning area, country boundaries |
| **Shapefile (.shp + support)** | 18 | Turbine layouts (3 sets × 6 files) |
| **Python** | 1 | Vortex data loader helper |

---

## Important Notes

### ✅ Data Remains Untouched

- **NO data files were moved or changed** during the refactoring
- All original data files remain in `Inputdata/` directory
- The new framework **reads from the same locations** as legacy code
- Your data is **safe and unchanged**

### ✅ New Framework Compatibility

The new framework's data loaders are designed to:
- Read from existing `Inputdata/` directory
- Handle all existing data formats (Vortex, PVGIS, CSV, shapefiles, geopackages)
- Validate data automatically
- Provide better error messages when data issues occur

### ✅ Optional Data Organization

If you want to organize data differently in the future:
- The `data/` placeholder directories are available
- You can move data files to organized subdirectories
- Update file paths in your scripts accordingly
- No requirement to reorganize - current structure works fine

---

## Example: Complete Analysis Using Your Data

```python
from latam_hybrid import quick_feasibility_study

# All data paths point to existing Inputdata/ directory
result = quick_feasibility_study(
    project_name="Latam Hybrid Project",
    wind_capacity_mw=50,
    solar_capacity_mw=10,

    # These would use your actual data files:
    # wind_data_file="Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt",
    # solar_data_file="Inputdata/PVGIS timeseries.csv",
    # turbine_file="Inputdata/Nordex N164.csv",
    # layout_file="Inputdata/Turbine_layout_13.csv",
    # price_file="Inputdata/Electricity price 2024 grid node.csv",

    # For now using simplified inputs:
    annual_wind_production_gwh=150,
    annual_solar_production_gwh=30,
    electricity_price=55
)
```

---

## Recommended: Keep Current Structure

**Recommendation**: Keep all data in `Inputdata/` directory as-is.

**Why**:
- Works with both legacy scripts and new framework
- No need to update file paths in existing work
- Clear separation: Code in `latam_hybrid/`, Data in `Inputdata/`
- Easy to backup and version control (data separate from code)

**Future Option**: If you want to reorganize later, you can move data files to the `data/` subdirectories, but this is **optional and not required**.

---

## Summary

✅ **All your input data is in**: `Inputdata/` directory (unchanged)
✅ **New framework reads from**: Same `Inputdata/` directory
✅ **Nothing was moved or changed**: Data remains exactly where it was
✅ **New framework advantage**: Better data loading with validation and error handling
