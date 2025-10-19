"""
Solar site analysis with pvlib integration.

Main orchestrator class for solar energy analysis using method chaining pattern.
"""

from typing import Optional, Union, Dict
import pandas as pd
import numpy as np
from pathlib import Path

from ..core import SolarData, SolarProductionResult
from .system import SolarSystem, PVSystemConfig


class SolarSite:
    """
    Solar site analyzer with method chaining API.

    Integrates solar irradiance data and PV system configuration for
    production calculations and analysis.

    Example:
        >>> result = (
        ...     SolarSite.from_solar_data(solar_data)
        ...     .with_system(capacity_kw=10000, tilt=20, azimuth=0)
        ...     .calculate_production()
        ... )
    """

    def __init__(
        self,
        solar_data: SolarData,
        system: Optional[SolarSystem] = None
    ):
        """
        Initialize solar site.

        Args:
            solar_data: Solar irradiance timeseries data
            system: Solar system configuration (optional, can be set later)
        """
        self.solar_data = solar_data
        self.system = system
        self._production_result = None

    @classmethod
    def from_solar_data(cls, solar_data: SolarData) -> 'SolarSite':
        """
        Create SolarSite from solar data.

        Args:
            solar_data: Solar irradiance timeseries

        Returns:
            SolarSite instance

        Example:
            >>> site = SolarSite.from_solar_data(solar_data)
        """
        return cls(solar_data)

    @classmethod
    def from_file(
        cls,
        filepath: Union[str, Path],
        source_type: str = 'auto',
        capacity_kw: float = 1000.0,
        **kwargs
    ) -> 'SolarSite':
        """
        Create SolarSite directly from solar data file.

        Args:
            filepath: Path to solar data file (PVGIS CSV, Excel, etc.)
            source_type: 'pvgis', 'csv', 'excel', or 'auto'
            capacity_kw: System capacity in kW
            **kwargs: Additional arguments for solar data reader

        Returns:
            SolarSite instance

        Example:
            >>> site = SolarSite.from_file(
            ...     "pvgis_data.csv",
            ...     source_type='pvgis',
            ...     capacity_kw=10000
            ... )
        """
        from ..input import read_solar_data

        solar_data = read_solar_data(
            filepath,
            source_type=source_type,
            capacity_kw=capacity_kw,
            **kwargs
        )

        return cls(solar_data)

    def with_system(
        self,
        system: Union[SolarSystem, float] = None,
        capacity_kw: Optional[float] = None,
        tilt: Optional[float] = None,
        azimuth: Optional[float] = None,
        **kwargs
    ) -> 'SolarSite':
        """
        Set solar system configuration (method chaining).

        Args:
            system: SolarSystem instance OR capacity_kw (if float)
            capacity_kw: System capacity (if system not provided)
            tilt: Panel tilt angle
            azimuth: Panel azimuth angle
            **kwargs: Additional system parameters

        Returns:
            Self for method chaining

        Example:
            >>> site = site.with_system(capacity_kw=10000, tilt=20, azimuth=0)
            >>> site = site.with_system(solar_system)
        """
        if isinstance(system, SolarSystem):
            self.system = system
        elif isinstance(system, (int, float)):
            # system is actually capacity_kw
            capacity_kw = float(system)
            # Try to get tilt/azimuth from solar data metadata
            if tilt is None:
                tilt = self.solar_data.metadata.get('tilt', 20)
            if azimuth is None:
                azimuth = self.solar_data.metadata.get('azimuth', 0)

            self.system = SolarSystem.create(
                capacity_kw=capacity_kw,
                tilt=tilt,
                azimuth=azimuth,
                **kwargs
            )
        elif capacity_kw is not None:
            # Create from parameters
            if tilt is None:
                tilt = self.solar_data.metadata.get('tilt', 20)
            if azimuth is None:
                azimuth = self.solar_data.metadata.get('azimuth', 0)

            self.system = SolarSystem.create(
                capacity_kw=capacity_kw,
                tilt=tilt,
                azimuth=azimuth,
                **kwargs
            )
        else:
            raise ValueError(
                "Must provide either SolarSystem instance or capacity_kw"
            )

        return self

    def validate_configuration(self) -> Dict:
        """
        Validate that site is properly configured.

        Returns:
            Dictionary with validation results

        Raises:
            ValueError: If critical configuration is missing
        """
        errors = []
        warnings = []

        if self.solar_data is None:
            errors.append("Solar data not set")

        if self.system is None:
            errors.append("Solar system not set")

        # Check data columns
        if self.solar_data:
            required_cols = ['P']  # At least power column
            missing = [col for col in required_cols
                      if col not in self.solar_data.timeseries.columns]
            if missing:
                warnings.append(f"Missing columns: {missing}")

        # Check system vs data capacity mismatch
        if self.solar_data and self.system:
            data_capacity = self.solar_data.capacity_kw
            system_capacity = self.system.capacity_kw

            if abs(data_capacity - system_capacity) / system_capacity > 0.1:
                warnings.append(
                    f"Solar data capacity ({data_capacity}kW) differs from "
                    f"system capacity ({system_capacity}kW) by "
                    f"{abs(data_capacity - system_capacity)/system_capacity:.1%}"
                )

        result = {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

        if errors:
            raise ValueError(
                f"Site configuration invalid: {'; '.join(errors)}"
            )

        return result

    def calculate_production(
        self,
        apply_shading: bool = False,
        shading_factor: Optional[pd.Series] = None,
        validate: bool = True
    ) -> SolarProductionResult:
        """
        Calculate solar production.

        Args:
            apply_shading: Whether to apply shading losses
            shading_factor: Optional shading factor series (0-1)
            validate: Whether to validate configuration first

        Returns:
            SolarProductionResult with production metrics

        Example:
            >>> result = site.calculate_production()
            >>> print(f"Annual production: {result.annual_production_mwh} MWh")
        """
        if validate:
            self.validate_configuration()

        df = self.solar_data.timeseries.copy()

        # Get power column (already in kW from reader)
        if 'P' in df.columns:
            power_kw = df['P'].values
        else:
            raise ValueError("Solar data must contain 'P' (power) column")

        # Scale to system capacity if needed
        data_capacity = self.solar_data.capacity_kw
        system_capacity = self.system.capacity_kw

        if data_capacity != system_capacity:
            scaling_factor = system_capacity / data_capacity
            power_kw = power_kw * scaling_factor

        # Apply shading losses if requested
        if apply_shading and shading_factor is not None:
            if len(shading_factor) != len(power_kw):
                raise ValueError(
                    f"Shading factor length ({len(shading_factor)}) "
                    f"must match data length ({len(power_kw)})"
                )
            power_kw = power_kw * shading_factor.values

        # Calculate metrics
        annual_production_kwh = power_kw.sum()
        annual_production_mwh = annual_production_kwh / 1000

        # Capacity factor
        hours = len(power_kw)
        max_annual_kwh = system_capacity * hours
        capacity_factor = annual_production_kwh / max_annual_kwh

        # Performance ratio (actual vs theoretical)
        if 'G(i)' in df.columns:
            # Calculate theoretical production from irradiance
            irradiance = df['G(i)'].values
            theoretical_kwh = (
                irradiance *
                system_capacity *
                self.system.efficiency / 1000
            ).sum()
            performance_ratio = annual_production_kwh / theoretical_kwh if theoretical_kwh > 0 else 0
        else:
            performance_ratio = None

        # Peak production
        peak_power_kw = power_kw.max()

        # Create timeseries DataFrame
        production_ts = pd.DataFrame({
            'power_kw': power_kw
        }, index=df.index)

        # Create result
        self._production_result = SolarProductionResult(
            power_timeseries=production_ts,
            capacity_factor=capacity_factor,
            aep_gwh=annual_production_mwh / 1000,  # Convert MWh to GWh
            shading_losses=0.0 if not apply_shading else None,
            system_losses={
                'performance_ratio': performance_ratio,
                'peak_power_kw': peak_power_kw
            } if performance_ratio else {'peak_power_kw': peak_power_kw},
            metadata={
                'system_capacity_kw': system_capacity,
                'tilt': self.system.tilt,
                'azimuth': self.system.azimuth,
                'n_hours': hours,
                'annual_production_mwh': annual_production_mwh
            }
        )

        return self._production_result

    def calculate_shading_losses(
        self,
        turbine_positions: np.ndarray,
        turbine_diameter: float,
        turbine_height: float,
        solar_panel_positions: np.ndarray,
        panel_height: float = 2.0
    ) -> pd.Series:
        """
        Calculate shading losses from wind turbines on solar panels.

        Args:
            turbine_positions: Nx2 array of turbine (x, y) positions
            turbine_diameter: Rotor diameter in meters
            turbine_height: Hub height in meters
            solar_panel_positions: Mx2 array of panel (x, y) positions
            panel_height: Panel mounting height in meters

        Returns:
            Timeseries of shading factors (0-1, 1=no shading)

        Note:
            This is a simplified implementation. For detailed shading analysis,
            use the dedicated shading module.
        """
        # Simplified shading calculation
        # In reality, this requires sun position calculations and shadow geometry
        n_hours = len(self.solar_data.timeseries)

        # Placeholder: assume minimal shading
        # Real implementation would calculate shadows hour by hour
        shading_factor = pd.Series(
            np.ones(n_hours),
            index=self.solar_data.timeseries.index
        )

        return shading_factor

    def get_summary(self) -> Dict:
        """
        Get summary statistics for the solar site.

        Returns:
            Dictionary with site summary
        """
        summary = {
            'solar_data': {
                'n_records': len(self.solar_data.timeseries),
                'capacity_kw': self.solar_data.capacity_kw,
                'source': self.solar_data.source
            }
        }

        if self.system:
            summary['system'] = {
                'capacity_kw': self.system.capacity_kw,
                'tilt': self.system.tilt,
                'azimuth': self.system.azimuth,
                'efficiency': self.system.efficiency,
                'module_area_m2': self.system.module_area_m2
            }

        if self._production_result:
            summary['production'] = {
                'annual_mwh': self._production_result.metadata.get('annual_production_mwh', 0),
                'aep_gwh': self._production_result.aep_gwh,
                'capacity_factor': self._production_result.capacity_factor,
                'peak_power_kw': self._production_result.system_losses.get('peak_power_kw', 0)
            }

        return summary

    def __repr__(self) -> str:
        system_str = (
            f"{self.system.capacity_kw}kW" if self.system
            else "None"
        )

        return (
            f"SolarSite(system={system_str}, "
            f"data_capacity={self.solar_data.capacity_kw}kW)"
        )


# Convenience function
def create_solar_site(
    solar_data: Union[SolarData, str, Path],
    capacity_kw: float,
    tilt: Optional[float] = None,
    azimuth: Optional[float] = None,
    **kwargs
) -> SolarSite:
    """
    Create fully configured SolarSite in one call.

    Args:
        solar_data: SolarData instance or filepath
        capacity_kw: System capacity in kW
        tilt: Panel tilt angle (auto-detected if None)
        azimuth: Panel azimuth (auto-detected if None)
        **kwargs: Additional arguments for data loading or system config

    Returns:
        Configured SolarSite instance

    Example:
        >>> site = create_solar_site(
        ...     solar_data="pvgis_data.csv",
        ...     capacity_kw=10000,
        ...     tilt=20,
        ...     azimuth=0
        ... )
    """
    # Load solar data if needed
    if isinstance(solar_data, (str, Path)):
        site = SolarSite.from_file(solar_data, capacity_kw=capacity_kw, **kwargs)
    else:
        site = SolarSite.from_solar_data(solar_data)

    # Set system
    site.with_system(capacity_kw=capacity_kw, tilt=tilt, azimuth=azimuth)

    return site
