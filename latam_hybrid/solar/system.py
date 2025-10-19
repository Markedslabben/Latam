"""
Solar PV system configuration.

Handles PV system parameters and integrates with pvlib for solar calculations.
"""

from dataclasses import dataclass
from typing import Optional, Dict
import numpy as np


@dataclass(frozen=True)
class PVSystemConfig:
    """
    PV system configuration parameters.

    Attributes:
        capacity_kw: System capacity in kW (DC)
        tilt: Panel tilt angle in degrees (0=horizontal, 90=vertical)
        azimuth: Panel azimuth in degrees (0=North, 90=East, 180=South, 270=West)
        efficiency: System efficiency (0-1), default 0.20
        temperature_coefficient: Power temperature coefficient (%/°C), default -0.4
        nominal_operating_cell_temp: NOCT in °C, default 45
        module_type: 'standard', 'premium', or 'thin_film'
        inverter_efficiency: Inverter efficiency (0-1), default 0.96
        dc_ac_ratio: DC/AC ratio, default 1.2
        losses: System losses (soiling, mismatch, etc.) (0-1), default 0.14
        metadata: Additional metadata
    """
    capacity_kw: float
    tilt: float
    azimuth: float
    efficiency: float = 0.20
    temperature_coefficient: float = -0.4
    nominal_operating_cell_temp: float = 45.0
    module_type: str = 'standard'
    inverter_efficiency: float = 0.96
    dc_ac_ratio: float = 1.2
    losses: float = 0.14
    metadata: Dict = None

    def __post_init__(self):
        """Validate PV system parameters."""
        if self.capacity_kw <= 0:
            raise ValueError("Capacity must be positive")
        if not (0 <= self.tilt <= 90):
            raise ValueError("Tilt must be between 0 and 90 degrees")
        if not (0 <= self.azimuth < 360):
            raise ValueError("Azimuth must be between 0 and 360 degrees")
        if not (0 < self.efficiency <= 1):
            raise ValueError("Efficiency must be between 0 and 1")
        if not (0 < self.inverter_efficiency <= 1):
            raise ValueError("Inverter efficiency must be between 0 and 1")


class SolarSystem:
    """
    Solar PV system model.

    Handles PV system configuration and integrates with pvlib for
    solar irradiance and production calculations.

    Example:
        >>> system = SolarSystem(
        ...     capacity_kw=10000,
        ...     tilt=20,
        ...     azimuth=0  # North-facing (Southern hemisphere)
        ... )
    """

    def __init__(self, config: PVSystemConfig):
        """
        Initialize solar system.

        Args:
            config: PVSystemConfig with system parameters
        """
        self.config = config
        self._pvlib_system = None

    @classmethod
    def create(
        cls,
        capacity_kw: float,
        tilt: float,
        azimuth: float,
        efficiency: float = 0.20,
        **kwargs
    ) -> 'SolarSystem':
        """
        Create solar system with basic parameters.

        Args:
            capacity_kw: System capacity in kW
            tilt: Panel tilt angle in degrees
            azimuth: Panel azimuth in degrees
            efficiency: System efficiency (0-1)
            **kwargs: Additional PVSystemConfig parameters

        Returns:
            SolarSystem instance

        Example:
            >>> system = SolarSystem.create(
            ...     capacity_kw=10000,
            ...     tilt=20,
            ...     azimuth=0,
            ...     efficiency=0.22
            ... )
        """
        config = PVSystemConfig(
            capacity_kw=capacity_kw,
            tilt=tilt,
            azimuth=azimuth,
            efficiency=efficiency,
            **kwargs
        )
        return cls(config)

    @classmethod
    def from_pvgis_data(
        cls,
        capacity_kw: float,
        pvgis_metadata: Dict
    ) -> 'SolarSystem':
        """
        Create system from PVGIS metadata.

        Args:
            capacity_kw: System capacity in kW
            pvgis_metadata: PVGIS metadata dict with 'tilt' and 'azimuth'

        Returns:
            SolarSystem instance
        """
        tilt = pvgis_metadata.get('tilt', 20)
        azimuth = pvgis_metadata.get('azimuth', 0)

        return cls.create(capacity_kw, tilt, azimuth)

    def to_pvlib(self):
        """
        Convert to pvlib PVSystem object.

        Returns:
            pvlib.pvsystem.PVSystem instance

        Raises:
            ImportError: If pvlib not installed
        """
        if self._pvlib_system is not None:
            return self._pvlib_system

        try:
            from pvlib import pvsystem
        except ImportError:
            raise ImportError(
                "pvlib is required for solar calculations. "
                "Install with: conda install -c conda-forge pvlib-python"
            )

        # Create pvlib PVSystem
        # Note: This is simplified - could be enhanced with detailed module/inverter models
        self._pvlib_system = pvsystem.PVSystem(
            surface_tilt=self.config.tilt,
            surface_azimuth=self.config.azimuth,
            module_parameters={
                'pdc0': self.config.capacity_kw * 1000,  # Convert to W
                'gamma_pdc': self.config.temperature_coefficient
            },
            inverter_parameters={
                'pdc0': self.config.capacity_kw * 1000 / self.config.dc_ac_ratio,
                'eta_inv_nom': self.config.inverter_efficiency
            }
        )

        return self._pvlib_system

    def calculate_effective_irradiance(
        self,
        ghi: float,
        dni: float,
        dhi: float,
        solar_zenith: float,
        solar_azimuth: float
    ) -> float:
        """
        Calculate effective irradiance on tilted panel.

        Args:
            ghi: Global horizontal irradiance (W/m²)
            dni: Direct normal irradiance (W/m²)
            dhi: Diffuse horizontal irradiance (W/m²)
            solar_zenith: Solar zenith angle (degrees)
            solar_azimuth: Solar azimuth angle (degrees)

        Returns:
            Plane-of-array irradiance (W/m²)
        """
        try:
            from pvlib import irradiance
        except ImportError:
            raise ImportError("pvlib is required")

        # Calculate POA irradiance
        poa = irradiance.get_total_irradiance(
            surface_tilt=self.config.tilt,
            surface_azimuth=self.config.azimuth,
            solar_zenith=solar_zenith,
            solar_azimuth=solar_azimuth,
            dni=dni,
            ghi=ghi,
            dhi=dhi
        )

        return poa['poa_global']

    def calculate_power_from_irradiance(
        self,
        irradiance: float,
        temperature: float = 25.0
    ) -> float:
        """
        Calculate DC power output from irradiance.

        Args:
            irradiance: Plane-of-array irradiance (W/m²)
            temperature: Cell temperature (°C)

        Returns:
            DC power output (kW)
        """
        # Standard test conditions
        stc_irradiance = 1000  # W/m²
        stc_temperature = 25  # °C

        # Temperature-corrected power
        temp_diff = temperature - stc_temperature
        temp_factor = 1 + (self.config.temperature_coefficient / 100) * temp_diff

        # Power calculation
        power_dc = (
            self.config.capacity_kw *
            (irradiance / stc_irradiance) *
            temp_factor *
            (1 - self.config.losses)
        )

        return max(0, power_dc)

    def calculate_ac_power(self, dc_power: float) -> float:
        """
        Convert DC power to AC power through inverter.

        Args:
            dc_power: DC power (kW)

        Returns:
            AC power output (kW)
        """
        # Inverter clipping
        max_ac = self.config.capacity_kw / self.config.dc_ac_ratio

        # Apply inverter efficiency
        ac_power = dc_power * self.config.inverter_efficiency

        # Clip at inverter capacity
        return min(ac_power, max_ac)

    @property
    def capacity_kw(self) -> float:
        """System capacity in kW."""
        return self.config.capacity_kw

    @property
    def tilt(self) -> float:
        """Panel tilt angle in degrees."""
        return self.config.tilt

    @property
    def azimuth(self) -> float:
        """Panel azimuth in degrees."""
        return self.config.azimuth

    @property
    def efficiency(self) -> float:
        """System efficiency."""
        return self.config.efficiency

    @property
    def module_area_m2(self) -> float:
        """Estimated module area in m²."""
        # Approximate: 1 kW ~ 6 m² at 20% efficiency
        return self.config.capacity_kw * 1000 / (self.config.efficiency * 1000)

    def __repr__(self) -> str:
        return (
            f"SolarSystem(capacity={self.capacity_kw}kW, "
            f"tilt={self.tilt}°, azimuth={self.azimuth}°, "
            f"efficiency={self.efficiency:.1%})"
        )


# Convenience function
def create_solar_system(
    capacity_kw: float,
    tilt: float,
    azimuth: float,
    **kwargs
) -> SolarSystem:
    """
    Create solar system with basic parameters.

    Args:
        capacity_kw: System capacity in kW
        tilt: Panel tilt angle in degrees
        azimuth: Panel azimuth in degrees
        **kwargs: Additional system parameters

    Returns:
        SolarSystem instance

    Example:
        >>> system = create_solar_system(10000, tilt=20, azimuth=0)
    """
    return SolarSystem.create(capacity_kw, tilt, azimuth, **kwargs)
