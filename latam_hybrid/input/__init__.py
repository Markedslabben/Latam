"""
Input data layer for Latam Hybrid Energy Analysis.

This module provides unified data loading for all input data types:
- Wind data (Vortex, CSV, Excel)
- Solar data (PVGIS, CSV, Excel)
- GIS data (Shapefiles, GeoJSON)
- Market data (Electricity prices)

All readers return standardized data models from the core module.
"""

# Generic loaders
from .loaders import FileLoader

# Wind data readers
from .wind_data_reader import (
    VortexWindReader,
    GenericWindReader,
    read_wind_data,
)

# Solar data readers
from .solar_data_reader import (
    PVGISReader,
    GenericSolarReader,
    read_solar_data,
)

# Market data readers
from .market_data_reader import (
    ElectricityPriceReader,
    read_electricity_prices,
)

# GIS data readers
from .gis_data_reader import (
    GISReader,
    read_gis_data,
)

__all__ = [
    # Generic loaders
    'FileLoader',
    # Wind readers
    'VortexWindReader',
    'GenericWindReader',
    'read_wind_data',
    # Solar readers
    'PVGISReader',
    'GenericSolarReader',
    'read_solar_data',
    # Market readers
    'ElectricityPriceReader',
    'read_electricity_prices',
    # GIS readers
    'GISReader',
    'read_gis_data',
]
