"""
Latam Hybrid Energy Analysis Framework

A comprehensive framework for analyzing hybrid wind-solar energy systems,
with focus on the Latam region. Provides clean separation between data ingestion,
calculations, and results output.

Main modules:
- core: Data models, time alignment, and validation utilities
- input: Data loaders for wind, solar, GIS, and market data
- wind: Wind energy analysis with pywake integration
- solar: Solar energy analysis with pvlib integration
- gis: Geospatial analysis and visualization
- economics: Financial analysis and metrics
- analysis: Hybrid analysis orchestration
- output: Results export and reporting

Example usage:
    >>> from latam_hybrid import HybridAnalysis
    >>> analysis = (
    ...     HybridAnalysis()
    ...     .add_wind_site(wind_site)
    ...     .add_solar_array(solar_array)
    ...     .calculate_economics()
    ... )
    >>> analysis.export_results("results/")
"""

__version__ = "0.1.0"
__author__ = "Klaus"

# Core exports (available for all modules)
from .core import (
    # Data models
    WindData,
    SolarData,
    GISData,
    MarketData,
    TurbineSpec,
    LayoutData,
    WindSimulationResult,
    SolarProductionResult,
    EconomicResult,
    HybridResult,
    # Enumerations
    WakeModel,
    TimeZoneOffset,
    # Time alignment
    TimeAlignmentService,
    TimeAlignmentConfig,
    align_pvgis_time,
    align_vortex_time,
    # Validation
    ValidationResult,
    DataValidator,
)

# Hybrid analysis orchestration
from .hybrid import (
    HybridAnalysis,
    analyze_wind_solar_hybrid,
    analyze_wind_only,
    analyze_solar_only,
    quick_feasibility_study,
    compare_scenarios,
)

__all__ = [
    # Version info
    '__version__',
    '__author__',
    # Core data models
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
    # Enumerations
    'WakeModel',
    'TimeZoneOffset',
    # Services
    'TimeAlignmentService',
    'TimeAlignmentConfig',
    'align_pvgis_time',
    'align_vortex_time',
    'ValidationResult',
    'DataValidator',
    # Hybrid analysis
    'HybridAnalysis',
    'analyze_wind_solar_hybrid',
    'analyze_wind_only',
    'analyze_solar_only',
    'quick_feasibility_study',
    'compare_scenarios',
]
