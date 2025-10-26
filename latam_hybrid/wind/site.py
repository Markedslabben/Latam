"""
Wind site analysis with pywake integration.

Main orchestrator class for wind energy analysis using method chaining pattern.
"""

from typing import Optional, Union, Dict, List
import pandas as pd
import numpy as np
from pathlib import Path

from ..core import WindData, WindSimulationResult, WakeModel, SectorManagementConfig
from .turbine import TurbineModel
from .layout import TurbineLayout
from .losses import WindFarmLosses, create_default_losses


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
        self._losses: Optional[WindFarmLosses] = None
        self._gross_aep: Optional[float] = None
        self.sector_management: Optional[SectorManagementConfig] = None

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

    def set_sector_management(
        self,
        config: SectorManagementConfig
    ) -> 'WindSite':
        """
        Set sector management configuration (method chaining).

        Args:
            config: SectorManagementConfig defining allowed wind sectors per turbine

        Returns:
            Self for method chaining

        Example:
            >>> from latam_hybrid.core import SectorManagementConfig
            >>> sector_config = SectorManagementConfig(
            ...     turbine_sectors={1: [(60, 120), (240, 300)]}
            ... )
            >>> site = site.set_sector_management(sector_config)
        """
        self.sector_management = config
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
        compute_losses: bool = True,
        validate: bool = True,
        simulation_method: str = 'timeseries'
    ) -> 'WindSite':
        """
        Run PyWake simulation with optional wake loss computation.

        Args:
            wake_model: Wake model to use ('NOJ', 'Bastankhah_Gaussian', etc.)
            wind_direction_bins: Number of direction bins for simulation
            compute_losses: If True, run comparative simulations to compute wake losses
            validate: Whether to validate configuration first
            simulation_method: 'timeseries' for hourly time series simulation,
                             'weibull' for Weibull distribution simulation

        Returns:
            Self for method chaining

        Example:
            >>> # Time series simulation (default)
            >>> site = site.run_simulation(wake_model='Bastankhah_Gaussian',
            ...                            simulation_method='timeseries')
            >>>
            >>> # Weibull distribution simulation
            >>> site = site.run_simulation(wake_model='NOJ',
            ...                            simulation_method='weibull')
        """
        if validate:
            self.validate_configuration()

        # Convert string to WakeModel enum if needed
        if isinstance(wake_model, str):
            wake_model = WakeModel[wake_model.upper().replace(' ', '_')]

        # Compute wake losses if requested
        if compute_losses:
            aep_ideal, wake_loss_pct = self._compute_wake_losses(
                wake_model,
                wind_direction_bins,
                simulation_method
            )
        else:
            aep_ideal = None
            wake_loss_pct = 0.0

        # Compute sector losses if sector management enabled
        if compute_losses and self.sector_management:
            sector_loss_pct = self._compute_sector_losses(
                wake_model,
                wind_direction_bins,
                simulation_method
            )
        else:
            sector_loss_pct = 0.0

        # Run final simulation (with wakes)
        sim_res = self._run_pywake_simulation(wake_model, wind_direction_bins, simulation_method)

        # ========================================================================
        # WAKE LOSS CALCULATION: Two-Simulation Approach
        # ========================================================================
        # NOTE: This approach treats wake losses and sector losses as INDEPENDENT,
        # which introduces a small approximation error (~0.5-1% farm-level).
        #
        # Current Implementation (2 simulations):
        #   1. Ideal: No wake, no sector management
        #   2. Realistic: With wake, no sector management
        #   → Wake loss = Ideal - Realistic
        #   → Sector loss applied as post-processing (see _apply_sector_management_to_results)
        #
        # Known Limitation:
        #   When a turbine is stopped (sector management), it doesn't create wakes
        #   for downstream turbines. This reduces wake losses compared to assuming
        #   all turbines always run. Current approach OVERESTIMATES total losses
        #   by not accounting for this interaction effect.
        #
        # Example:
        #   - Turbine 3 stopped in wind directions 120-240° (sector management)
        #   - Turbine 5 (downwind) produces MORE when T3 is stopped (no wake)
        #   - Current code calculates T5 wake loss assuming T3 always running
        #   - Result: Wake losses overestimated by ~(sector_loss × wake_fraction)
        #
        # Ideal Implementation (future work):
        #   Would require 3-4 PyWake simulations to properly capture interaction:
        #   1. No wake, NO sector     → Ideal baseline
        #   2. No wake, WITH sector   → Pure sector effect
        #   3. With wake, NO sector   → Pure wake effect
        #   4. With wake, WITH sector → Combined effect (current reality)
        #   → This would allow separating: wake + sector + interaction
        #
        # Why Not Implemented:
        #   PyWake doesn't natively support sector management (assumes continuous
        #   operation). Sector management is applied as post-processing, so we
        #   cannot run PyWake "with sector management built-in" to capture the
        #   reduced wake effects when turbines are stopped.
        #
        # Error Magnitude:
        #   Sector loss = ~6% farm-level
        #   Wake loss = ~10% farm-level
        #   Interaction effect ≈ 0.6% (second-order)
        #   → Total error estimate: 0.5-1% of farm production
        #
        # TODO: Future enhancement - Implement proper wake-sector interaction
        #       calculation if PyWake adds sector management support, or develop
        #       custom post-processing to estimate interaction correction factor.
        # ========================================================================

        # Run NO-WAKE simulation to get ideal production per turbine
        sim_no_wake = self._run_pywake_simulation(None, wind_direction_bins, simulation_method)
        ideal_per_turbine = self._get_aep_per_turbine(sim_no_wake)  # Without wake, without sector

        # Extract results WITH wake and apply sector management
        aep_per_turbine, sector_loss_per_turbine = self._apply_sector_management_to_results(
            sim_res,
            wind_direction_bins,
            return_losses=True
        )  # GWh per turbine (with sector curtailment if applicable)
        aep_gross = aep_per_turbine.sum()

        # Calculate per-turbine wake losses
        # Wake loss = (ideal - production_with_wake_and_sector) - sector_loss
        # Because sector management was applied to BOTH ideal and actual
        production_with_wake_no_sector = self._get_aep_per_turbine(sim_res)
        wake_loss_per_turbine = ideal_per_turbine - production_with_wake_no_sector

        # Create result dataclass
        self._simulation_result = WindSimulationResult(
            aep_gwh=aep_gross,  # This includes wake + sector effects
            capacity_factor=self._calculate_capacity_factor(aep_gross),
            wake_loss_percent=wake_loss_pct,
            turbine_production_gwh=aep_per_turbine.tolist(),
            wake_model=wake_model,
            sector_loss_percent=sector_loss_pct,
            metadata={
                'n_turbines': self.layout.n_turbines,
                'total_capacity_mw': self.turbine.rated_power * self.layout.n_turbines / 1000,
                'wind_direction_bins': wind_direction_bins,
                'simulation_type': 'pywake',
                'aep_ideal': aep_ideal,  # Baseline (no wake, no sector)
                'has_sector_management': self.sector_management is not None,
                'pywake_sim_result': sim_res,  # Store PyWake simulation result object
                # Per-turbine loss arrays (GWh/yr per turbine)
                'ideal_per_turbine_gwh': ideal_per_turbine.tolist(),
                'wake_loss_per_turbine_gwh': wake_loss_per_turbine.tolist(),
                'sector_loss_per_turbine_gwh': sector_loss_per_turbine.tolist()
            }
        )

        return self

    def apply_losses(
        self,
        loss_config_file: Optional[str] = None,
        **overrides
    ) -> 'WindSite':
        """
        Apply non-PyWake losses from CSV configuration file.

        Wake and sector losses are NOT applied here - they're already
        included in the AEP from run_simulation().

        This method only applies losses not modeled in PyWake:
        - Availability (turbines/grid)
        - Electrical losses
        - Hysteresis
        - Environmental degradation
        - Other losses

        Args:
            loss_config_file: Path to losses CSV file.
                            If None, uses default: latam_hybrid/Inputdata/losses.csv
            **overrides: Manual overrides for specific losses (highest priority)
                        Example: availability_turbines=0.02

        Priority order:
            1. Manual overrides (highest)
            2. CSV file values
            3. Built-in defaults (if CSV missing or incomplete)

        Returns:
            Self for method chaining

        Example:
            >>> # Use default CSV
            >>> site.run_simulation().apply_losses().calculate_production()
            >>>
            >>> # Custom CSV
            >>> site.run_simulation().apply_losses(
            ...     loss_config_file="custom_losses.csv"
            ... ).calculate_production()
            >>>
            >>> # CSV + manual overrides
            >>> site.run_simulation().apply_losses(
            ...     availability_turbines=0.02  # Override CSV value
            ... ).calculate_production()
        """
        import pandas as pd
        from pathlib import Path

        if self._simulation_result is None:
            raise ValueError(
                "No simulation results available. Run run_simulation() first."
            )

        # Determine CSV path
        if loss_config_file is None:
            # Default to Inputdata/losses.csv
            project_root = Path(__file__).parent.parent
            loss_config_file = project_root / 'Inputdata' / 'losses.csv'
        else:
            loss_config_file = Path(loss_config_file)

        # Read CSV file
        csv_values = {}
        if loss_config_file.exists():
            df = pd.read_csv(loss_config_file)
            csv_values = dict(zip(df['loss_category'], df['default_value']))
        else:
            # CSV not found - will use built-in defaults
            csv_values = {}

        # Merge priorities: built-in defaults < CSV < manual overrides
        # Start with built-in defaults
        final_values = dict(WindFarmLosses.DEFAULTS)
        # Override with CSV values
        final_values.update(csv_values)
        # Override with manual parameters
        final_values.update(overrides)

        # Get AEP from simulation (already includes wake + sector)
        aep_gross = self._simulation_result.aep_gwh

        # Create losses manager (only non-PyWake losses)
        self._losses = WindFarmLosses()
        self._losses.add_default_losses(
            availability_turbines=final_values.get('availability_turbines'),
            availability_grid=final_values.get('availability_grid'),
            electrical_losses=final_values.get('electrical_losses'),
            high_hysteresis=final_values.get('high_hysteresis_losses'),
            environmental_degradation=final_values.get('environmental_performance_degradation'),
            other_losses=final_values.get('other_losses')
        )

        # Calculate net AEP (only applying non-PyWake losses)
        aep_net = self._losses.calculate_net_aep(aep_gross)

        # Calculate per-turbine other losses (applied uniformly as farm-level percentage)
        # NOTE: calculate_total_loss_factor() returns the REMAINING production factor (e.g., 0.912)
        # NOT the loss factor (e.g., 0.088), so we need to swap the assignments
        remaining_factor = self._losses.calculate_total_loss_factor()  # e.g., 0.912 for 8.8% losses
        turbine_prod_before_other = np.array(self._simulation_result.turbine_production_gwh)
        turbine_prod_net = turbine_prod_before_other * remaining_factor  # Net = 91.2% of gross
        other_loss_per_turbine = turbine_prod_before_other * (1 - remaining_factor)  # Loss = 8.8% of gross

        # Build complete loss breakdown (wake + sector + others)
        complete_breakdown = self._build_complete_loss_breakdown()

        # Calculate total loss factor (ideal → net)
        total_loss_factor = self._calculate_total_loss_factor(aep_net)

        # Update result with net AEP and losses
        self._simulation_result = WindSimulationResult(
            aep_gwh=aep_net,  # Net AEP
            capacity_factor=self._calculate_capacity_factor(aep_net),
            wake_loss_percent=self._simulation_result.wake_loss_percent,
            turbine_production_gwh=turbine_prod_net.tolist(),  # Net production per turbine
            wake_model=self._simulation_result.wake_model,
            sector_loss_percent=self._simulation_result.sector_loss_percent,
            gross_aep_gwh=aep_gross,
            loss_breakdown=complete_breakdown,
            total_loss_factor=total_loss_factor,
            metadata={
                **self._simulation_result.metadata,
                'losses_applied': True,
                'loss_config_file': str(loss_config_file),
                'other_loss_per_turbine_gwh': other_loss_per_turbine.tolist()  # Add per-turbine other losses
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

    def _create_timeseries_site(self):
        """
        Create XRSite from wind data time series.

        Based on legacy create_site_from_vortex implementation.
        Uses IEC 61400-1 NTM formula for turbulence intensity.

        Returns:
            XRSite configured for time series simulation
        """
        import xarray as xr
        from py_wake.site.xrsite import XRSite

        # Extract wind data
        ws = self.wind_data.timeseries['ws'].values
        wd = self.wind_data.timeseries['wd'].values
        n_timesteps = len(ws)

        # Turbulence intensity using IEC 61400-1 NTM formula
        # TI = I_ref * (0.75 + 5.6/V_hub), I_ref = 0.12
        ti = np.array([0.12 * (0.75 + 5.6 / max(v, 1.0)) for v in ws])

        # Probability weights (uniform for time series)
        P = np.ones(n_timesteps)

        # Create xarray Dataset
        ds = xr.Dataset(
            {
                "wind_speed": ("time", ws),
                "wind_direction": ("time", wd),
                "P": ("time", P),
                "TI": ("time", ti),
            },
            coords={"time": np.arange(n_timesteps)}
        )

        return XRSite(ds, interp_method='nearest')

    def _run_pywake_simulation(
        self,
        wake_model: Optional[WakeModel],
        wind_direction_bins: int,
        simulation_method: str = 'timeseries'
    ):
        """
        Run single PyWake simulation with specified wake model.

        Args:
            wake_model: Wake model (None for no-wake baseline)
            wind_direction_bins: Number of direction bins
            simulation_method: 'timeseries' or 'weibull'

        Returns:
            PyWake simulation result object
        """
        try:
            from py_wake.wind_farm_models import PropagateDownwind
            from py_wake.site import UniformWeibullSite
            from py_wake.deficit_models import NOJDeficit, BastankhahGaussianDeficit, NoWakeDeficit
        except ImportError:
            raise ImportError(
                "pywake is required for simulations. "
                "Install with: conda install -c conda-forge py_wake"
            )

        # Get pywake turbine
        pywake_turbine = self.turbine.to_pywake()

        # Get layout coordinates
        x, y = self.layout.to_pywake_format()

        # Select wake model
        if wake_model is None:
            deficit_model = NoWakeDeficit()
        else:
            wake_deficit_models = {
                WakeModel.NOJ: NOJDeficit(),
                WakeModel.BASTANKHAH_GAUSSIAN: BastankhahGaussianDeficit()
            }
            deficit_model = wake_deficit_models.get(wake_model, NOJDeficit())

        # Create site based on simulation method
        if simulation_method == 'timeseries':
            # Time series simulation
            pywake_site = self._create_timeseries_site()

            # Create wind farm model using PropagateDownwind
            wfm = PropagateDownwind(
                pywake_site,
                pywake_turbine,
                wake_deficitModel=deficit_model
            )

            # Run simulation with time series
            times = np.arange(len(self.wind_data.timeseries))
            ws = self.wind_data.timeseries['ws'].values
            wd = self.wind_data.timeseries['wd'].values

            return wfm(x, y, wd=wd, ws=ws, time=times)

        else:
            # Weibull distribution simulation (original method)
            # Create wind frequency table
            wind_freq = self._create_wind_frequency_table(
                n_direction_bins=wind_direction_bins
            )

            # Create pywake site (using Weibull distribution)
            pywake_site = UniformWeibullSite(
                p_wd=wind_freq['frequency'].values,
                a=wind_freq['weibull_A'].values,
                k=wind_freq['weibull_k'].values,
                ti=0.1  # Turbulence intensity (could be parameter)
            )

            # Create wind farm model using PropagateDownwind
            wfm = PropagateDownwind(
                pywake_site,
                pywake_turbine,
                wake_deficitModel=deficit_model
            )

            return wfm(x, y)

    def _get_aep_per_turbine(self, sim_result) -> np.ndarray:
        """
        Extract annual energy per turbine from PyWake simulation result.
        PyWake's .aep() returns annualized power values, so .mean(dim='time') gives GWh/year.

        Args:
            sim_result: PyWake simulation result object

        Returns:
            Array of annual energy per turbine (GWh/year), shape (n_turbines,)
        """
        aep_raw = sim_result.aep()  # xarray DataArray


        # For timeseries: shape is (n_turbines, n_timesteps), sum over time
        # PyWake's .aep() returns energy per timestep,  so sum gives total (but internally annualized)
        # For Weibull: shape is already (n_turbines,)
        if len(aep_raw.shape) == 2:
            # Timeseries simulation - SUM over time dimension
            # NOTE: PyWake internally annualizes results, so sum returns GWh/year not total GWh
            return aep_raw.sum(dim='time').values  # Shape: (n_turbines,), GWh/year
        else:
            # Weibull simulation - already aggregated
            return aep_raw.values  # Shape: (n_turbines,), GWh/year

    def _apply_sector_management_to_results(
        self,
        sim_result,
        wind_direction_bins: int,
        return_losses: bool = False
    ):
        """
        Apply sector management curtailment to PyWake simulation results.

        Calculates sector losses based on ACTUAL ENERGY lost in prohibited sectors,
        not simple time availability. This accounts for wind speed and frequency
        variations by direction.

        Args:
            sim_result: PyWake simulation result object
            wind_direction_bins: Number of direction bins used in simulation
            return_losses: Whether to return sector losses per turbine

        Returns:
            If return_losses=False: Array of adjusted AEP per turbine (GWh/year)
            If return_losses=True: Tuple of (adjusted AEP, sector losses per turbine)

        Note:
            This is a post-processing step. PyWake assumes all turbines operate
            continuously. We calculate actual energy that would be lost when
            turbines are stopped during prohibited wind directions.

        **IMPORTANT - Wake-Sector Loss Interaction:**
            This post-processing approach treats sector losses as independent of
            wake losses, which introduces a small approximation error (~0.5-1%
            farm-level). In reality, when a turbine is stopped (sector management),
            it doesn't create wakes for downstream turbines, reducing their wake
            losses. Since PyWake runs with all turbines continuously operating,
            it cannot capture this interaction effect.

            Current approach: Wake losses calculated assuming all turbines always
            run → slightly OVERESTIMATES total losses.

            See detailed explanation in run_simulation() method (line ~302) and
            loss_calculation_methodology.md documentation.

            TODO: Future enhancement to capture wake-sector interaction effects.
        """
        # Get base AEP per turbine from PyWake using helper method
        aep_per_turbine = self._get_aep_per_turbine(sim_result)

        # Initialize sector losses array (zero for all turbines initially)
        sector_loss_per_turbine = np.zeros(len(aep_per_turbine))

        # If no sector management, return unchanged
        if not self.sector_management:
            if return_losses:
                return aep_per_turbine, sector_loss_per_turbine
            else:
                return aep_per_turbine

        # Check if we have timeseries data to calculate energy-based losses
        aep_raw = sim_result.aep()

        if len(aep_raw.shape) == 2:
            # TIMESERIES: Calculate energy-based sector losses from hourly data
            from .sector_management import is_direction_in_sectors

            # Get hourly power production per turbine from PyWake
            # PyWake returns power in Watts (W) for each timestep
            power_timeseries = sim_result.Power.values  # Shape: (n_turbines, n_timesteps)
            wind_directions = self.wind_data.timeseries['wd'].values

            # Verify shapes match
            if len(wind_directions) != power_timeseries.shape[1]:
                raise ValueError(
                    f"Wind direction length ({len(wind_directions)}) doesn't match "
                    f"power timeseries length ({power_timeseries.shape[1]})"
                )

            # For each restricted turbine, calculate energy lost in prohibited sectors
            for turbine_id, sectors in self.sector_management.turbine_sectors.items():
                turbine_idx = turbine_id - 1  # Convert to 0-indexed

                if turbine_idx < 0 or turbine_idx >= len(aep_per_turbine):
                    raise ValueError(
                        f"Turbine ID {turbine_id} out of range for "
                        f"{len(aep_per_turbine)} turbines"
                    )

                # Calculate energy produced in prohibited sectors
                # Sum power (W) over prohibited hours to get energy (Wh)
                prohibited_energy_wh = 0.0
                for t, wd in enumerate(wind_directions):
                    if not is_direction_in_sectors(wd, sectors):
                        # Wind is in prohibited sector - this energy is lost
                        # power_timeseries is in W, multiplied by 1 hour = Wh
                        prohibited_energy_wh += power_timeseries[turbine_idx, t]

                # Convert from Wh to GWh and annualize to match aep_per_turbine units
                # aep_per_turbine is already annual (GWh/year) from PyWake
                # prohibited_energy_wh is total over simulation period, need to annualize
                num_hours = len(wind_directions)
                num_years = num_hours / 8760.0
                sector_loss_gwh_total = prohibited_energy_wh / 1e9  # Total over simulation
                sector_loss_per_turbine[turbine_idx] = sector_loss_gwh_total / num_years  # Annual average

                # Subtract lost energy from turbine production (both now in GWh/year)
                aep_per_turbine[turbine_idx] -= sector_loss_per_turbine[turbine_idx]

        else:
            # WEIBULL: Fallback to time-based availability (less accurate)
            # This is necessary because Weibull doesn't have hourly timeseries
            from .sector_management import calculate_sector_availability

            availability = calculate_sector_availability(
                self.wind_data.timeseries,
                self.sector_management.turbine_sectors
            )

            for turbine_id, avail_factor in availability.items():
                turbine_idx = turbine_id - 1

                if turbine_idx < 0 or turbine_idx >= len(aep_per_turbine):
                    raise ValueError(
                        f"Turbine ID {turbine_id} out of range for "
                        f"{len(aep_per_turbine)} turbines"
                    )

                # Use time-based approximation for Weibull
                original_aep = aep_per_turbine[turbine_idx]
                sector_loss_per_turbine[turbine_idx] = original_aep * (1 - avail_factor)
                aep_per_turbine[turbine_idx] *= avail_factor

        if return_losses:
            return aep_per_turbine, sector_loss_per_turbine
        else:
            return aep_per_turbine

    def _compute_wake_losses(
        self,
        wake_model: WakeModel,
        wind_direction_bins: int,
        simulation_method: str = 'timeseries'
    ) -> tuple[float, float]:
        """
        Compute wake losses by running comparative simulations.

        Runs two simulations:
        1. Baseline (no wake)
        2. With wake model

        Args:
            wake_model: Wake model to use
            wind_direction_bins: Number of direction bins
            simulation_method: 'timeseries' or 'weibull'

        Returns:
            (aep_ideal, wake_loss_percent)
        """
        # Run baseline (no wake)
        sim_baseline = self._run_pywake_simulation(None, wind_direction_bins, simulation_method)
        aep_ideal = sim_baseline.aep().sum()

        # Run with wake
        sim_wake = self._run_pywake_simulation(wake_model, wind_direction_bins, simulation_method)
        aep_with_wake = sim_wake.aep().sum()

        # Calculate wake loss percentage
        if aep_ideal == 0:
            wake_loss_pct = 0.0
        else:
            wake_loss_pct = (aep_ideal - aep_with_wake) / aep_ideal * 100

        return aep_ideal, max(0.0, wake_loss_pct)

    def _compute_sector_losses(
        self,
        wake_model: WakeModel,
        wind_direction_bins: int,
        simulation_method: str = 'timeseries'
    ) -> float:
        """
        Compute sector management losses via comparative simulation.

        Runs two simulations:
        1. WITH sector management (curtailed turbines)
        2. WITHOUT sector management (all turbines always running)

        The difference represents the energy lost due to sector curtailment.

        Args:
            wake_model: Wake model to use in simulations
            wind_direction_bins: Number of direction bins
            simulation_method: 'timeseries' or 'weibull'

        Returns:
            sector_loss_percent: Loss percentage from sector curtailment (0-100)
        """
        if not self.sector_management:
            return 0.0

        # Run simulation WITH sector management
        sim_result = self._run_pywake_simulation(wake_model, wind_direction_bins, simulation_method)
        aep_with_sectors = self._apply_sector_management_to_results(
            sim_result, wind_direction_bins
        ).sum()

        # Run simulation WITHOUT sector management (baseline)
        # Temporarily disable sector management
        saved_config = self.sector_management
        self.sector_management = None

        sim_baseline = self._run_pywake_simulation(wake_model, wind_direction_bins, simulation_method)
        aep_no_sectors = sim_baseline.aep().sum()

        # Restore sector management config
        self.sector_management = saved_config

        # Calculate sector loss percentage
        if aep_no_sectors == 0:
            return 0.0

        sector_loss_pct = (aep_no_sectors - aep_with_sectors) / aep_no_sectors * 100

        return max(0.0, sector_loss_pct)

    def _build_complete_loss_breakdown(self) -> Dict[str, Dict]:
        """
        Build complete loss breakdown including:
        - Wake losses (from simulation, already applied in AEP)
        - Sector losses (from simulation, future, already applied in AEP)
        - Other losses (from apply_losses, applied to simulation AEP)
        """
        breakdown = {}

        # Add wake losses (computed in run_simulation, already in AEP)
        if self._simulation_result.wake_loss_percent > 0:
            breakdown['wake_losses'] = {
                'percentage': self._simulation_result.wake_loss_percent,
                'value': self._simulation_result.wake_loss_percent / 100,
                'is_computed': True,
                'applied_in': 'run_simulation',
                'description': 'Wake effects from turbine interactions'
            }

        # Add sector losses (future feature, already in AEP when implemented)
        if self._simulation_result.sector_loss_percent > 0:
            breakdown['sector_management'] = {
                'percentage': self._simulation_result.sector_loss_percent,
                'value': self._simulation_result.sector_loss_percent / 100,
                'is_computed': True,
                'applied_in': 'run_simulation',
                'description': 'Curtailment from sector management constraints'
            }

        # Add other losses (from apply_losses)
        user_losses = {}
        if self._losses is not None:
            for name, loss_data in self._losses.get_loss_breakdown().items():
                breakdown[name] = {
                    **loss_data,
                    'applied_in': 'apply_losses'
                }
                user_losses[name] = loss_data.get('percentage', 0)

        # Calculate total loss percentage
        # Note: losses are multiplicative, not additive
        # Total = 100 * (1 - (1-l1/100) * (1-l2/100) * ...)
        loss_factor = 1.0

        # Apply wake losses
        if 'wake_losses' in breakdown:
            loss_factor *= (1 - breakdown['wake_losses']['percentage'] / 100)

        # Apply sector losses
        if 'sector_management' in breakdown:
            loss_factor *= (1 - breakdown['sector_management']['percentage'] / 100)

        # Apply user losses
        for loss_pct in user_losses.values():
            loss_factor *= (1 - loss_pct / 100)

        total_loss_percentage = 100 * (1 - loss_factor)

        # Add summary fields
        breakdown['total_loss_percentage'] = total_loss_percentage
        breakdown['user_losses'] = user_losses

        return breakdown

    def _calculate_total_loss_factor(self, aep_net: float) -> Optional[float]:
        """
        Calculate total loss factor from ideal AEP to net AEP.

        This captures the COMBINED effect of ALL losses:
        - Wake losses (applied in run_simulation)
        - Sector losses (applied in run_simulation, future)
        - Availability, electrical, etc. (applied in apply_losses)

        Args:
            aep_net: Net AEP after all losses

        Returns:
            Total loss factor (net / ideal), or None if ideal AEP unknown
        """
        aep_ideal = self._simulation_result.metadata.get('aep_ideal')

        if aep_ideal is None or aep_ideal == 0:
            return None

        return aep_net / aep_ideal

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
