"""
Core data models for the Latam Hybrid Energy Analysis project.

This module defines immutable dataclasses representing all domain data structures.
All data models follow the principle: frozen after creation to ensure data integrity.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from enum import Enum


# ============================================================================
# Enumerations
# ============================================================================

class WakeModel(str, Enum):
    """Available wake models for wind simulation."""
    NOJ = "NOJ"  # Jensen (N.O. Jensen)
    BASTANKHAH_GAUSSIAN = "Bastankhah_Gaussian"
    TURBO_PARK = "TurboPark"
    FUGA = "Fuga"


class TimeZoneOffset(int, Enum):
    """Common timezone offsets for the project."""
    UTC = 0
    UTC_MINUS_4 = -4  # Default for Latam region
    UTC_MINUS_5 = -5


# ============================================================================
# Input Data Models
# ============================================================================

@dataclass(frozen=True)
class WindData:
    """
    Raw wind time series data from meteorological sources (e.g., Vortex).

    Attributes:
        timeseries: DataFrame with DatetimeIndex and columns for wind components
                   Expected columns: ['ws' (wind speed), 'wd' (wind direction)]
        height: Measurement height in meters
        timezone_offset: UTC offset in hours
        source: Data source identifier (e.g., "Vortex", "Measured")
        metadata: Additional metadata (location, coordinates, etc.)
    """
    timeseries: pd.DataFrame
    height: float
    timezone_offset: int = TimeZoneOffset.UTC_MINUS_4
    source: str = "Unknown"
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate wind data structure."""
        required_cols = ['ws', 'wd']
        if not all(col in self.timeseries.columns for col in required_cols):
            raise ValueError(f"WindData must contain columns: {required_cols}")
        if not isinstance(self.timeseries.index, pd.DatetimeIndex):
            raise ValueError("WindData timeseries must have DatetimeIndex")


@dataclass(frozen=True)
class SolarData:
    """
    Solar irradiance and PV production data from PVGIS or similar sources.

    Attributes:
        timeseries: DataFrame with DatetimeIndex and solar data columns
                   Expected columns: ['G(i)' (irradiance), 'T2m' (temperature), 'P' (power)]
        capacity_kw: Installed PV capacity in kW
        timezone_offset: UTC offset in hours
        shift_minutes: Additional time shift in minutes (PVGIS often needs +30min adjustment)
        source: Data source identifier (e.g., "PVGIS")
        metadata: Additional metadata (location, tilt, azimuth, etc.)
    """
    timeseries: pd.DataFrame
    capacity_kw: float
    timezone_offset: int = TimeZoneOffset.UTC_MINUS_4
    shift_minutes: int = 30
    source: str = "PVGIS"
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate solar data structure."""
        if not isinstance(self.timeseries.index, pd.DatetimeIndex):
            raise ValueError("SolarData timeseries must have DatetimeIndex")
        if self.capacity_kw <= 0:
            raise ValueError("Solar capacity must be positive")


@dataclass(frozen=True)
class GISData:
    """
    Geospatial data including planning areas, elevation, and boundaries.

    Attributes:
        planning_area: GeoDataFrame with planning area boundaries
        elevation: Optional elevation raster or point data
        crs: Coordinate Reference System (e.g., "EPSG:4326")
        metadata: Additional GIS metadata
    """
    planning_area: 'gpd.GeoDataFrame'  # Type hint as string to avoid import
    elevation: Optional[np.ndarray] = None
    crs: str = "EPSG:4326"
    metadata: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class MarketData:
    """
    Electricity market price data.

    Attributes:
        timeseries: DataFrame with DatetimeIndex and price columns
                   Expected columns: ['price'] in currency per kWh
        currency: Currency code (e.g., "USD", "EUR", "CLP")
        exchange_rate: Exchange rate to USD (if applicable)
        timezone_offset: UTC offset in hours
        metadata: Market metadata (zone, market name, etc.)
    """
    timeseries: pd.DataFrame
    currency: str = "USD"
    exchange_rate: float = 1.0
    timezone_offset: int = TimeZoneOffset.UTC_MINUS_4
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate market data structure."""
        if 'price' not in self.timeseries.columns:
            raise ValueError("MarketData must contain 'price' column")
        if not isinstance(self.timeseries.index, pd.DatetimeIndex):
            raise ValueError("MarketData timeseries must have DatetimeIndex")


# ============================================================================
# Configuration Data Models
# ============================================================================

@dataclass(frozen=True)
class TurbineSpec:
    """
    Wind turbine technical specifications.

    Attributes:
        name: Turbine model name (e.g., "Nordex N164")
        hub_height: Hub height in meters
        rotor_diameter: Rotor diameter in meters
        rated_power: Rated power in kW
        power_curve: DataFrame with columns ['ws' (m/s), 'power' (kW)]
        ct_curve: Optional thrust coefficient curve
        metadata: Additional specifications (manufacturer, year, etc.)
    """
    name: str
    hub_height: float
    rotor_diameter: float
    rated_power: float
    power_curve: pd.DataFrame
    ct_curve: Optional[pd.DataFrame] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate turbine specifications."""
        if self.hub_height <= 0 or self.rotor_diameter <= 0:
            raise ValueError("Hub height and rotor diameter must be positive")
        if 'ws' not in self.power_curve.columns or 'power' not in self.power_curve.columns:
            raise ValueError("Power curve must have 'ws' and 'power' columns")


@dataclass(frozen=True)
class LayoutData:
    """
    Wind turbine layout coordinates.

    Attributes:
        coordinates: Array of (x, y) coordinates in meters or (lon, lat) in degrees
        turbine_ids: Optional list of turbine identifiers
        crs: Coordinate Reference System
        metadata: Layout metadata (optimization method, constraints, etc.)
    """
    coordinates: np.ndarray
    turbine_ids: Optional[List[str]] = None
    crs: str = "EPSG:4326"
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate layout data."""
        if self.coordinates.ndim != 2 or self.coordinates.shape[1] != 2:
            raise ValueError("Coordinates must be Nx2 array")
        if self.turbine_ids and len(self.turbine_ids) != len(self.coordinates):
            raise ValueError("Number of turbine IDs must match coordinates")

    @property
    def n_turbines(self) -> int:
        """Return number of turbines in layout."""
        return len(self.coordinates)


# ============================================================================
# Result Data Models
# ============================================================================

@dataclass(frozen=True)
class WindSimulationResult:
    """
    Results from wind farm simulation.

    Attributes:
        power_timeseries: DataFrame with DatetimeIndex and power output (kW)
        capacity_factor: Overall capacity factor (0-1)
        aep_gwh: Annual Energy Production in GWh
        wake_losses: Wake loss percentage (0-100)
        turbine_production: Per-turbine production data
        metadata: Simulation metadata (wake model, version, runtime, etc.)
    """
    power_timeseries: pd.DataFrame
    capacity_factor: float
    aep_gwh: float
    wake_losses: float
    turbine_production: Optional[pd.DataFrame] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate simulation results."""
        if not (0 <= self.capacity_factor <= 1):
            raise ValueError("Capacity factor must be between 0 and 1")
        if self.wake_losses < 0 or self.wake_losses > 100:
            raise ValueError("Wake losses must be between 0 and 100")


@dataclass(frozen=True)
class SolarProductionResult:
    """
    Results from solar PV production analysis.

    Attributes:
        power_timeseries: DataFrame with DatetimeIndex and power output (kW)
        capacity_factor: Overall capacity factor (0-1)
        aep_gwh: Annual Energy Production in GWh
        shading_losses: Shading loss percentage from nearby turbines (0-100)
        system_losses: Total system losses (soiling, degradation, inverter, etc.)
        metadata: Analysis metadata (pvlib version, models used, etc.)
    """
    power_timeseries: pd.DataFrame
    capacity_factor: float
    aep_gwh: float
    shading_losses: float = 0.0
    system_losses: Dict[str, float] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate solar results."""
        if not (0 <= self.capacity_factor <= 1):
            raise ValueError("Capacity factor must be between 0 and 1")


@dataclass(frozen=True)
class EconomicResult:
    """
    Financial analysis results.

    Attributes:
        revenue_timeseries: DataFrame with DatetimeIndex and revenue
        total_revenue: Total revenue over analysis period
        lcoe: Levelized Cost of Energy (currency/kWh)
        npv: Net Present Value
        irr: Internal Rate of Return (0-1)
        payback_period_years: Simple payback period in years
        metadata: Economic assumptions (discount rate, lifetime, costs, etc.)
    """
    revenue_timeseries: pd.DataFrame
    total_revenue: float
    lcoe: float
    npv: float
    irr: Optional[float] = None
    payback_period_years: Optional[float] = None
    metadata: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class HybridResult:
    """
    Combined hybrid analysis results.

    Attributes:
        wind_result: Wind simulation results
        solar_result: Solar production results
        economic_result: Financial analysis results
        combined_power: DataFrame with combined wind + solar power timeseries
        total_aep_gwh: Total annual energy production (wind + solar)
        capacity_factor: Combined capacity factor
        metadata: Hybrid analysis metadata
    """
    wind_result: WindSimulationResult
    solar_result: SolarProductionResult
    economic_result: EconomicResult
    combined_power: pd.DataFrame
    total_aep_gwh: float
    capacity_factor: float
    metadata: Dict = field(default_factory=dict)


# ============================================================================
# Utility Functions
# ============================================================================

def validate_timeseries_alignment(
    *dataframes: pd.DataFrame,
    tolerance_minutes: int = 60
) -> bool:
    """
    Validate that multiple timeseries DataFrames are properly aligned.

    Args:
        *dataframes: Variable number of DataFrames to check
        tolerance_minutes: Maximum allowed time difference between indices

    Returns:
        True if all timeseries are aligned within tolerance

    Raises:
        ValueError: If timeseries are not aligned
    """
    if len(dataframes) < 2:
        return True

    base_index = dataframes[0].index
    for i, df in enumerate(dataframes[1:], start=1):
        if not base_index.equals(df.index):
            # Check if close enough within tolerance
            max_diff = abs(base_index - df.index).max()
            if max_diff > pd.Timedelta(minutes=tolerance_minutes):
                raise ValueError(
                    f"Timeseries {i} not aligned with first timeseries. "
                    f"Max difference: {max_diff}"
                )
    return True
