"""
Wind site analysis with pywake integration.

Main orchestrator class for wind energy analysis using method chaining pattern.
"""

from typing import Optional, Union, Dict, List
import pandas as pd
import numpy as np
from pathlib import Path

from ..core import WindData, WindSimulationResult, WakeModel
from .turbine import TurbineModel
from .layout import TurbineLayout


class WindSite:
    """
    Wind site analyzer with method chaining API.

    Integrates wind data, turbine model, and layout for pywake-based
    wind farm simulations and energy production calculations.

    Example:
        >>> result = (
        ...     WindSite.from_wind_data(wind_data)
        ...     .with_turbine(turbine_model)
        ...     .set_layout(layout)
        ...     .run_simulation(wake_model='NOJ')
        ...     .calculate_production()
        ... )
    """

    def __init__(
        self,
        wind_data: WindData,
        turbine: Optional[TurbineModel] = None,
        layout: Optional[TurbineLayout] = None
    ):
        """
        Initialize wind site.

        Args:
            wind_data: Wind timeseries data
            turbine: Turbine model (optional, can be set later)
            layout: Turbine layout (optional, can be set later)
        """
        self.wind_data = wind_data
        self.turbine = turbine
        self.layout = layout
        self._simulation_result = None
        self._production_result = None

    @classmethod
    def from_wind_data(cls, wind_data: WindData) -> 'WindSite':
        """
        Create WindSite from wind data.

        Args:
            wind_data: Wind timeseries data

        Returns:
            WindSite instance

        Example:
            >>> site = WindSite.from_wind_data(wind_data)
        """
        return cls(wind_data)

    @classmethod
    def from_file(
        cls,
        filepath: Union[str, Path],
        source_type: str = 'auto',
        height: float = 100.0,
        **kwargs
    ) -> 'WindSite':
        """
        Create WindSite directly from wind data file.

        Args:
            filepath: Path to wind data file
            source_type: 'vortex', 'csv', 'excel', or 'auto'
            height: Measurement height in meters
            **kwargs: Additional arguments for wind data reader

        Returns:
            WindSite instance

        Example:
            >>> site = WindSite.from_file("vortex.serie.100m.txt", height=100)
        """
        from ..input import read_wind_data

        wind_data = read_wind_data(
            filepath,
            source_type=source_type,
            height=height,
            **kwargs
        )

        return cls(wind_data)

    def with_turbine(
        self,
        turbine: Union[TurbineModel, str, Path]
    ) -> 'WindSite':
        """
        Set turbine model (method chaining).

        Args:
            turbine: TurbineModel instance, filepath, or catalog name

        Returns:
            Self for method chaining

        Example:
            >>> site = site.with_turbine("Nordex N164.csv")
            >>> site = site.with_turbine(turbine_model)
        """
        if isinstance(turbine, TurbineModel):
            self.turbine = turbine
        else:
            # Load from file or catalog
            from .turbine import load_turbine
            self.turbine = load_turbine(turbine)

        return self

    def set_layout(
        self,
        layout: Union[TurbineLayout, str, Path, np.ndarray]
    ) -> 'WindSite':
        """
        Set turbine layout (method chaining).

        Args:
            layout: TurbineLayout instance, filepath, or coordinate array

        Returns:
            Self for method chaining

        Example:
            >>> site = site.set_layout("turbine_layout.csv")
            >>> site = site.set_layout(layout)
        """
        if isinstance(layout, TurbineLayout):
            self.layout = layout
        else:
            # Load from file or array
            from .layout import load_layout
            self.layout = load_layout(layout)

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

        if self.wind_data is None:
            errors.append("Wind data not set")

        if self.turbine is None:
            errors.append("Turbine model not set")

        if self.layout is None:
            errors.append("Turbine layout not set")

        # Check wind data height vs turbine hub height
        if self.wind_data and self.turbine:
            height_diff = abs(self.wind_data.height - self.turbine.hub_height)
            if height_diff > 20:
                warnings.append(
                    f"Wind data height ({self.wind_data.height}m) differs from "
                    f"turbine hub height ({self.turbine.hub_height}m) by {height_diff}m. "
                    f"Consider applying wind profile correction."
                )

        # Check minimum spacing
        if self.layout and self.turbine:
            spacing_result = self.layout.validate_minimum_spacing(
                min_spacing=2.0,
                rotor_diameter=self.turbine.rotor_diameter
            )
            if not spacing_result['is_valid']:
                warnings.append(
                    f"Layout has {spacing_result['n_violations']} spacing violations "
                    f"(minimum 2D recommended)"
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

    def run_simulation(
        self,
        wake_model: Union[str, WakeModel] = WakeModel.NOJ,
        wind_direction_bins: int = 12,
        validate: bool = True
    ) -> 'WindSite':
        """
        Run wake simulation using pywake.

        Args:
            wake_model: Wake model to use ('NOJ', 'Bastankhah_Gaussian', etc.)
            wind_direction_bins: Number of direction bins for simulation
            validate: Whether to validate configuration first

        Returns:
            Self for method chaining

        Example:
            >>> site = site.run_simulation(wake_model='NOJ')
        """
        if validate:
            self.validate_configuration()

        # Convert string to WakeModel enum if needed
        if isinstance(wake_model, str):
            wake_model = WakeModel[wake_model.upper().replace(' ', '_')]

        try:
            from py_wake import WindFarmModel
            from py_wake.site import UniformWeibullSite
            from py_wake.deficit_models import NOJDeficit, BastankhahGaussianDeficit
        except ImportError:
            raise ImportError(
                "pywake is required for simulations. "
                "Install with: conda install -c conda-forge py_wake"
            )

        # Get pywake turbine
        pywake_turbine = self.turbine.to_pywake()

        # Get layout coordinates
        x, y = self.layout.to_pywake_format()

        # Create wind frequency table
        wind_freq = self._create_wind_frequency_table(
            n_direction_bins=wind_direction_bins
        )

        # Create pywake site (using Weibull distribution)
        # Note: This is simplified - could be enhanced with measured wind data
        site_params = self._estimate_weibull_parameters()

        pywake_site = UniformWeibullSite(
            p_wd=wind_freq['frequency'].values,
            a=wind_freq['weibull_A'].values,
            k=wind_freq['weibull_k'].values,
            ti=0.1  # Turbulence intensity (could be parameter)
        )

        # Select wake model
        wake_deficit_models = {
            WakeModel.NOJ: NOJDeficit(),
            WakeModel.BASTANKHAH_GAUSSIAN: BastankhahGaussianDeficit()
        }

        deficit_model = wake_deficit_models.get(
            wake_model,
            NOJDeficit()  # Default
        )

        # Create wind farm model
        wfm = WindFarmModel(
            site=pywake_site,
            wind_turbines=pywake_turbine,
            wake_deficitModel=deficit_model
        )

        # Run simulation
        sim_res = wfm(x, y)

        # Extract results
        aep_per_turbine = sim_res.aep().values  # GWh per turbine
        total_aep = aep_per_turbine.sum()

        # Create result dataclass
        self._simulation_result = WindSimulationResult(
            aep_gwh=total_aep,
            capacity_factor=self._calculate_capacity_factor(total_aep),
            wake_loss_percent=self._calculate_wake_loss(sim_res),
            turbine_production_gwh=aep_per_turbine.tolist(),
            wake_model=wake_model,
            metadata={
                'n_turbines': self.layout.n_turbines,
                'total_capacity_mw': self.turbine.rated_power * self.layout.n_turbines / 1000,
                'wind_direction_bins': wind_direction_bins,
                'simulation_type': 'pywake'
            }
        )

        return self

    def calculate_production(
        self,
        include_timeseries: bool = False
    ) -> WindSimulationResult:
        """
        Get production results.

        Args:
            include_timeseries: Whether to include hourly production timeseries

        Returns:
            WindSimulationResult with AEP, capacity factor, wake losses

        Example:
            >>> result = site.calculate_production()
            >>> print(f"AEP: {result.aep_gwh} GWh")
        """
        if self._simulation_result is None:
            raise ValueError(
                "No simulation results available. Run run_simulation() first."
            )

        return self._simulation_result

    def _create_wind_frequency_table(
        self,
        n_direction_bins: int = 12
    ) -> pd.DataFrame:
        """
        Create wind frequency table from wind data.

        Args:
            n_direction_bins: Number of direction bins

        Returns:
            DataFrame with direction bins and frequencies
        """
        df = self.wind_data.timeseries.copy()

        # Create direction bins
        bin_width = 360 / n_direction_bins
        df['wd_bin'] = (df['wd'] / bin_width).astype(int) % n_direction_bins

        # Calculate frequency per bin
        freq_table = df.groupby('wd_bin').size() / len(df)

        # Estimate Weibull parameters per bin
        weibull_params = df.groupby('wd_bin')['ws'].apply(
            self._estimate_weibull_from_series
        )

        result = pd.DataFrame({
            'direction_bin': range(n_direction_bins),
            'frequency': [freq_table.get(i, 0) for i in range(n_direction_bins)],
            'weibull_A': [weibull_params.get(i, (8.0, 2.0))[0] for i in range(n_direction_bins)],
            'weibull_k': [weibull_params.get(i, (8.0, 2.0))[1] for i in range(n_direction_bins)]
        })

        return result

    @staticmethod
    def _estimate_weibull_from_series(ws_series: pd.Series) -> tuple:
        """
        Estimate Weibull A and k parameters from wind speed series.

        Args:
            ws_series: Wind speed series

        Returns:
            Tuple of (A, k) parameters
        """
        from scipy import stats

        # Remove zeros and NaN
        ws_clean = ws_series[ws_series > 0].dropna()

        if len(ws_clean) < 10:
            return (8.0, 2.0)  # Default values

        # Fit Weibull distribution
        # scipy uses (c=k, scale=A) parameterization
        k, loc, A = stats.weibull_min.fit(ws_clean, floc=0)

        return (A, k)

    def _estimate_weibull_parameters(self) -> Dict:
        """
        Estimate overall Weibull parameters for site.

        Returns:
            Dictionary with A and k parameters
        """
        ws = self.wind_data.timeseries['ws']
        A, k = self._estimate_weibull_from_series(ws)

        return {'A': A, 'k': k}

    def _calculate_capacity_factor(self, aep_gwh: float) -> float:
        """
        Calculate capacity factor from AEP.

        Args:
            aep_gwh: Annual energy production in GWh

        Returns:
            Capacity factor (0-1)
        """
        total_capacity_mw = (
            self.turbine.rated_power * self.layout.n_turbines / 1000
        )

        max_annual_gwh = total_capacity_mw * 8760 / 1000  # GWh

        capacity_factor = aep_gwh / max_annual_gwh

        return capacity_factor

    def _calculate_wake_loss(self, sim_res) -> float:
        """
        Calculate wake loss percentage from pywake simulation.

        Args:
            sim_res: pywake simulation result

        Returns:
            Wake loss percentage
        """
        # Get AEP with and without wakes
        aep_with_wake = sim_res.aep().sum()

        # For wake-free, we'd need to run separate simulation
        # For now, estimate from capacity factor
        # This is a simplification - could be improved
        return 10.0  # Placeholder - needs actual calculation

    def get_summary(self) -> Dict:
        """
        Get summary statistics for the wind site.

        Returns:
            Dictionary with site summary
        """
        summary = {
            'wind_data': {
                'n_records': len(self.wind_data.timeseries),
                'height_m': self.wind_data.height,
                'mean_wind_speed': self.wind_data.timeseries['ws'].mean(),
                'source': self.wind_data.source
            }
        }

        if self.turbine:
            summary['turbine'] = {
                'name': self.turbine.name,
                'hub_height_m': self.turbine.hub_height,
                'rotor_diameter_m': self.turbine.rotor_diameter,
                'rated_power_kw': self.turbine.rated_power
            }

        if self.layout:
            summary['layout'] = {
                'n_turbines': self.layout.n_turbines,
                'bounds': self.layout.bounds,
                'center': self.layout.center
            }

        if self._simulation_result:
            summary['production'] = {
                'aep_gwh': self._simulation_result.aep_gwh,
                'capacity_factor': self._simulation_result.capacity_factor,
                'wake_loss_percent': self._simulation_result.wake_loss_percent
            }

        return summary

    def __repr__(self) -> str:
        turbine_str = f"'{self.turbine.name}'" if self.turbine else "None"
        layout_str = f"{self.layout.n_turbines} turbines" if self.layout else "None"

        return (
            f"WindSite(turbine={turbine_str}, "
            f"layout={layout_str}, "
            f"wind_data_height={self.wind_data.height}m)"
        )


# Convenience function
def create_wind_site(
    wind_data: Union[WindData, str, Path],
    turbine: Union[TurbineModel, str, Path],
    layout: Union[TurbineLayout, str, Path, np.ndarray],
    **kwargs
) -> WindSite:
    """
    Create fully configured WindSite in one call.

    Args:
        wind_data: WindData instance or filepath
        turbine: TurbineModel instance or filepath
        layout: TurbineLayout instance, filepath, or coordinate array
        **kwargs: Additional arguments for wind data loading

    Returns:
        Configured WindSite instance

    Example:
        >>> site = create_wind_site(
        ...     wind_data="vortex.serie.100m.txt",
        ...     turbine="Nordex N164.csv",
        ...     layout="turbine_layout.csv"
        ... )
    """
    # Load wind data if needed
    if isinstance(wind_data, (str, Path)):
        site = WindSite.from_file(wind_data, **kwargs)
    else:
        site = WindSite.from_wind_data(wind_data)

    # Set turbine and layout
    site.with_turbine(turbine).set_layout(layout)

    return site
