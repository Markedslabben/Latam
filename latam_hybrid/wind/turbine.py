"""
Wind turbine model classes.

Wraps turbine specifications and integrates with pywake WindTurbine objects.
"""

from pathlib import Path
from typing import Optional, Union, Dict
import pandas as pd
import numpy as np

from ..core import TurbineSpec, DataValidator


class TurbineModel:
    """
    Wind turbine model with pywake integration.

    This class wraps turbine specifications and creates pywake WindTurbine objects.
    Supports loading from CSV files (like your Nordex N164.csv) or programmatic creation.
    """

    def __init__(self, spec: TurbineSpec):
        """
        Initialize turbine model from specification.

        Args:
            spec: TurbineSpec with power curve and technical parameters
        """
        self.spec = spec
        self._pywake_turbine = None

    @classmethod
    def from_csv(
        cls,
        filepath: Union[str, Path],
        name: Optional[str] = None,
        hub_height: float = 100.0,
        rotor_diameter: float = 150.0,
        rated_power: Optional[float] = None,
        ws_column: str = 'ws',
        power_column: str = 'power',
        ct_column: Optional[str] = 'ct'
    ) -> 'TurbineModel':
        """
        Load turbine from CSV file (like Nordex N164.csv or ANY turbine).

        Args:
            filepath: Path to turbine CSV file
            name: Turbine name (auto-detected from filename if None)
            hub_height: Hub height in meters
            rotor_diameter: Rotor diameter in meters
            rated_power: Rated power in kW (auto-detected from curve if None)
            ws_column: Wind speed column name
            power_column: Power column name
            ct_column: Thrust coefficient column name (optional)

        Returns:
            TurbineModel instance

        Example:
            >>> turbine = TurbineModel.from_csv(
            ...     "Nordex N164.csv",
            ...     hub_height=120,
            ...     rotor_diameter=164
            ... )
        """
        from ..input import FileLoader

        filepath = Path(filepath)

        # Auto-detect name from filename if not provided
        if name is None:
            name = filepath.stem  # e.g., "Nordex N164" from "Nordex N164.csv"

        # Load power curve
        df = FileLoader.load_csv(filepath)

        # Rename columns to standard names
        column_map = {ws_column: 'ws', power_column: 'power'}
        if ct_column and ct_column in df.columns:
            column_map[ct_column] = 'ct'

        df = df.rename(columns=column_map)

        # Validate required columns
        if 'ws' not in df.columns or 'power' not in df.columns:
            raise ValueError(
                f"CSV must contain '{ws_column}' and '{power_column}' columns. "
                f"Available: {df.columns.tolist()}"
            )

        # Extract power curve
        power_curve = df[['ws', 'power']].copy()

        # Auto-detect rated power if not provided
        if rated_power is None:
            rated_power = power_curve['power'].max()

        # Extract CT curve if available
        ct_curve = None
        if 'ct' in df.columns:
            ct_curve = df[['ws', 'ct']].copy()

        # Create TurbineSpec
        spec = TurbineSpec(
            name=name,
            hub_height=hub_height,
            rotor_diameter=rotor_diameter,
            rated_power=rated_power,
            power_curve=power_curve,
            ct_curve=ct_curve,
            metadata={'filepath': str(filepath)}
        )

        return cls(spec)

    @classmethod
    def from_pywake_catalog(
        cls,
        turbine_name: str,
        hub_height: Optional[float] = None
    ) -> 'TurbineModel':
        """
        Load turbine from pywake's built-in catalog.

        Args:
            turbine_name: Name in pywake catalog (e.g., 'Vestas V80 2MW')
            hub_height: Hub height override (uses default if None)

        Returns:
            TurbineModel instance

        Example:
            >>> turbine = TurbineModel.from_pywake_catalog('Vestas V80 2MW')
        """
        try:
            from py_wake.wind_turbines import WindTurbine
            from py_wake.wind_turbines._wind_turbines import get_wt
        except ImportError:
            raise ImportError(
                "pywake is required for catalog loading. "
                "Install with: conda install -c conda-forge py_wake"
            )

        # Get turbine from catalog
        wt = get_wt(turbine_name)

        # Extract power curve from pywake turbine
        ws_array = np.arange(0, 30, 0.5)
        power_array = wt.power(ws_array)

        power_curve = pd.DataFrame({
            'ws': ws_array,
            'power': power_array
        })

        # Use provided hub height or default
        if hub_height is None:
            hub_height = wt.hub_height()

        # Create TurbineSpec
        spec = TurbineSpec(
            name=turbine_name,
            hub_height=hub_height,
            rotor_diameter=wt.diameter(),
            rated_power=power_array.max(),
            power_curve=power_curve,
            ct_curve=None,
            metadata={'source': 'pywake_catalog'}
        )

        instance = cls(spec)
        instance._pywake_turbine = wt  # Store original pywake object

        return instance

    def to_pywake(self) -> 'WindTurbine':
        """
        Convert to pywake WindTurbine object.

        Returns:
            pywake WindTurbine instance

        Example:
            >>> turbine_model = TurbineModel.from_csv("Nordex N164.csv")
            >>> pywake_turbine = turbine_model.to_pywake()
        """
        if self._pywake_turbine is not None:
            return self._pywake_turbine

        try:
            from py_wake.wind_turbines import WindTurbine
            from py_wake.wind_turbines.power_ct_functions import PowerCtTabular
        except ImportError:
            raise ImportError(
                "pywake is required. "
                "Install with: conda install -c conda-forge py_wake"
            )

        # Extract power curve arrays
        ws = self.spec.power_curve['ws'].values
        power = self.spec.power_curve['power'].values

        # Extract CT curve if available, otherwise use default
        if self.spec.ct_curve is not None:
            ct = self.spec.ct_curve['ct'].values
        else:
            # Use pywake's default CT curve estimation
            ct = None

        # Create pywake power/CT function
        if ct is not None:
            power_ct_func = PowerCtTabular(
                ws=ws,
                power=power,
                power_unit='kW',
                ct=ct
            )
        else:
            power_ct_func = PowerCtTabular(
                ws=ws,
                power=power,
                power_unit='kW'
            )

        # Create pywake WindTurbine
        wt = WindTurbine(
            name=self.spec.name,
            diameter=self.spec.rotor_diameter,
            hub_height=self.spec.hub_height,
            powerCtFunction=power_ct_func
        )

        self._pywake_turbine = wt
        return wt

    def power_at_wind_speed(self, wind_speed: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Get power output at given wind speed(s).

        Args:
            wind_speed: Wind speed(s) in m/s

        Returns:
            Power output(s) in kW

        Example:
            >>> power = turbine.power_at_wind_speed(10.0)  # Single value
            >>> powers = turbine.power_at_wind_speed([8, 10, 12])  # Array
        """
        # Interpolate from power curve
        power = np.interp(
            wind_speed,
            self.spec.power_curve['ws'].values,
            self.spec.power_curve['power'].values,
            left=0.0,
            right=0.0  # Zero power outside curve range
        )

        return power

    @property
    def name(self) -> str:
        """Turbine name."""
        return self.spec.name

    @property
    def hub_height(self) -> float:
        """Hub height in meters."""
        return self.spec.hub_height

    @property
    def rotor_diameter(self) -> float:
        """Rotor diameter in meters."""
        return self.spec.rotor_diameter

    @property
    def rated_power(self) -> float:
        """Rated power in kW."""
        return self.spec.rated_power

    @property
    def swept_area(self) -> float:
        """Rotor swept area in m²."""
        return np.pi * (self.rotor_diameter / 2) ** 2

    def __repr__(self) -> str:
        return (
            f"TurbineModel(name='{self.name}', "
            f"hub_height={self.hub_height}m, "
            f"rotor_diameter={self.rotor_diameter}m, "
            f"rated_power={self.rated_power}kW)"
        )


# Convenience function
def load_turbine(
    source: Union[str, Path],
    **kwargs
) -> TurbineModel:
    """
    Load turbine from file or catalog.

    Args:
        source: File path or catalog name
        **kwargs: Additional arguments for loading

    Returns:
        TurbineModel instance

    Example:
        >>> # From file
        >>> turbine = load_turbine("Nordex N164.csv", hub_height=120)
        >>>
        >>> # From pywake catalog
        >>> turbine = load_turbine("Vestas V80 2MW")
    """
    source_path = Path(source)

    # Check if it's a file
    if source_path.exists():
        return TurbineModel.from_csv(source, **kwargs)
    else:
        # Try pywake catalog
        return TurbineModel.from_pywake_catalog(source, **kwargs)
