"""
Core module for Latam Hybrid Energy Analysis.

This module provides the foundational data models, time alignment services,
and validation utilities used throughout the project.
"""

# Data models
from .data_models import (
    # Enumerations
    WakeModel,
    TimeZoneOffset,
    # Input data models
    WindData,
    SolarData,
    GISData,
    MarketData,
    # Configuration models
    TurbineSpec,
    LayoutData,
    # Result models
    WindSimulationResult,
    SolarProductionResult,
    EconomicResult,
    HybridResult,
    # Utilities
    validate_timeseries_alignment,
)

# Time alignment
from .time_alignment import (
    TimeAlignmentConfig,
    TimeAlignmentService,
    align_pvgis_time,
    align_vortex_time,
)

# Validation
from .validation import (
    ValidationResult,
    DataValidator,
)

# Path utilities
from .paths import (
    get_package_root,
    get_data_dir,
    get_data_file,
    get_wind_data_file,
    get_solar_data_file,
    get_turbine_file,
    get_layout_file,
    get_gis_file,
    get_price_file,
    list_data_files,
    PACKAGE_ROOT,
    DATA_DIR,
    GIS_DATA_DIR,
)

__all__ = [
    # Enumerations
    'WakeModel',
    'TimeZoneOffset',
    # Data models
    'WindData',
    'SolarData',
    'GISData',
    'MarketData',
    'TurbineSpec',
    'LayoutData',
    'WindSimulationResult',
    'SolarProductionResult',
    'EconomicResult',
    'HybridResult',
    # Time alignment
    'TimeAlignmentConfig',
    'TimeAlignmentService',
    'align_pvgis_time',
    'align_vortex_time',
    # Validation
    'ValidationResult',
    'DataValidator',
    # Path utilities
    'get_package_root',
    'get_data_dir',
    'get_data_file',
    'get_wind_data_file',
    'get_solar_data_file',
    'get_turbine_file',
    'get_layout_file',
    'get_gis_file',
    'get_price_file',
    'list_data_files',
    'PACKAGE_ROOT',
    'DATA_DIR',
    'GIS_DATA_DIR',
    # Utilities
    'validate_timeseries_alignment',
]
