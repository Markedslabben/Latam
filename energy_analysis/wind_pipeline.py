"""
Wind Energy Analysis Pipeline

Object-oriented wrapper around existing wind energy analysis functions.
Provides stateful pipeline with method chaining while preserving original functionality.
"""

import pandas as pd
import numpy as np
import xarray as xr
from typing import Optional, Tuple, Dict, Any
import os
import sys

# Import existing modules
sys.path.append('.')
from turbine_galvian.create_turbine import create_nordex_n164_turbine, create_turbine_from_csv
from site_galvian.create_site import (
    create_site_from_vortex, 
    create_wind_distribution, 
    create_weibull_site,
    read_electricity_price
)
from py_wake.wind_farm_models import PropagateDownwind
from py_wake.deficit_models import NOJDeficit, BastankhahGaussianDeficit, NoWakeDeficit

from .config import WindConfig, SiteConfig


class WindEnergyPipeline:
    """
    Wind energy analysis pipeline that maintains state and enables method chaining.
    
    Wraps existing functional code in an object-oriented interface for convenience.
    """
    
    def __init__(self, wind_config: WindConfig, site_config: SiteConfig, verbose: bool = True):
        self.wind_config = wind_config
        self.site_config = site_config
        self.verbose = verbose
        
        # State variables
        self._turbine = None
        self._site = None
        self._layout = None
        self._wind_farm_model = None
        self._simulation_results = None
        self._weibull_site = None
        self._wind_distribution = None
        self._electricity_prices = None
        
        # Results storage
        self.results = {}
        self.metadata = {}
        
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[WindPipeline] {message}")
    
    # ============================================================================
    # TURBINE LOADING
    # ============================================================================
    
    def load_turbine(self, csv_path: Optional[str] = None) -> 'WindEnergyPipeline':
        """
        Load wind turbine model from CSV file.
        
        Args:
            csv_path: Path to turbine CSV file. If None, uses config default.
            
        Returns:
            Self for method chaining
        """
        csv_path = csv_path or self.wind_config.turbine_csv_path
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Turbine CSV file not found: {csv_path}")
            
        self._log(f"Loading turbine from {csv_path}")
        
        # Use existing function
        self._turbine = create_nordex_n164_turbine(csv_path)
        
        self.metadata['turbine_loaded'] = True
        self.metadata['turbine_path'] = csv_path
        self.metadata['turbine_name'] = self.wind_config.turbine_name
        
        self._log(f"Turbine loaded: {self.wind_config.turbine_name}")
        return self
    
    def load_custom_turbine(self, csv_path: str, name: str, diameter: float, hub_height: float) -> 'WindEnergyPipeline':
        """
        Load custom turbine model.
        
        Args:
            csv_path: Path to turbine CSV file
            name: Turbine name
            diameter: Rotor diameter in meters
            hub_height: Hub height in meters
            
        Returns:
            Self for method chaining
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Turbine CSV file not found: {csv_path}")
            
        self._log(f"Loading custom turbine: {name}")
        
        # Use existing function
        self._turbine = create_turbine_from_csv(csv_path, name, diameter, hub_height)
        
        self.metadata['turbine_loaded'] = True
        self.metadata['turbine_path'] = csv_path
        self.metadata['turbine_name'] = name
        
        return self
    
    @property
    def turbine(self):
        """Get loaded turbine model."""
        if self._turbine is None:
            raise ValueError("Turbine not loaded. Call load_turbine() first.")
        return self._turbine
    
    # ============================================================================
    # SITE CREATION
    # ============================================================================
    
    def create_site(self, vortex_path: Optional[str] = None, 
                   start: Optional[str] = None, 
                   end: Optional[str] = None) -> 'WindEnergyPipeline':
        """
        Create wind site from Vortex data file.
        
        Args:
            vortex_path: Path to Vortex data file. If None, uses config default.
            start: Start date string. If None, uses config years.
            end: End date string. If None, uses config years.
            
        Returns:
            Self for method chaining
        """
        vortex_path = vortex_path or self.wind_config.vortex_data_path
        start = start or f"{self.wind_config.start_year}-01-01 00:00"
        end = end or f"{self.wind_config.end_year}-12-31 23:59"
        
        if not os.path.exists(vortex_path):
            raise FileNotFoundError(f"Vortex data file not found: {vortex_path}")
            
        self._log(f"Creating site from {vortex_path}")
        self._log(f"Time period: {start} to {end}")
        
        # Use existing function
        self._site = create_site_from_vortex(
            vortex_path, 
            start=start, 
            end=end, 
            include_leap_year=self.wind_config.include_leap_year
        )
        
        self.metadata['site_created'] = True
        self.metadata['vortex_path'] = vortex_path
        self.metadata['time_period'] = (start, end)
        
        self._log("Site created successfully")
        return self
    
    @property
    def site(self):
        """Get created wind site."""
        if self._site is None:
            raise ValueError("Site not created. Call create_site() first.")
        return self._site
    
    # ============================================================================
    # LAYOUT LOADING
    # ============================================================================
    
    def load_layout(self, layout_path: Optional[str] = None) -> 'WindEnergyPipeline':
        """
        Load turbine layout from CSV file.
        
        Args:
            layout_path: Path to layout CSV file. If None, uses config default.
            
        Returns:
            Self for method chaining
        """
        layout_path = layout_path or self.wind_config.layout_csv_path
        
        if not os.path.exists(layout_path):
            raise FileNotFoundError(f"Layout CSV file not found: {layout_path}")
            
        self._log(f"Loading layout from {layout_path}")
        
        self._layout = pd.read_csv(layout_path)
        
        # Validate required columns
        required_cols = ['x_coord', 'y_coord']
        missing_cols = [col for col in required_cols if col not in self._layout.columns]
        if missing_cols:
            raise ValueError(f"Layout CSV missing required columns: {missing_cols}")
        
        self.metadata['layout_loaded'] = True
        self.metadata['layout_path'] = layout_path
        self.metadata['n_turbines'] = len(self._layout)
        
        self._log(f"Layout loaded: {len(self._layout)} turbines")
        return self
    
    @property
    def layout(self) -> pd.DataFrame:
        """Get loaded turbine layout."""
        if self._layout is None:
            raise ValueError("Layout not loaded. Call load_layout() first.")
        return self._layout
    
    @property
    def turbine_coordinates(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get turbine coordinates as (x, y) arrays."""
        layout = self.layout
        return layout['x_coord'].values, layout['y_coord'].values
    
    # ============================================================================
    # WIND FARM MODEL SETUP
    # ============================================================================
    
    def setup_wind_farm_model(self, wake_model: Optional[str] = None) -> 'WindEnergyPipeline':
        """
        Set up wind farm model with specified wake model.
        
        Args:
            wake_model: Wake model name. If None, uses config default.
                       Options: "NoWakeDeficit", "BastankhahGaussianDeficit", "NOJDeficit"
            
        Returns:
            Self for method chaining
        """
        wake_model = wake_model or self.wind_config.wake_model
        
        # Ensure prerequisites are met
        if self._turbine is None:
            raise ValueError("Turbine not loaded. Call load_turbine() first.")
        if self._site is None:
            raise ValueError("Site not created. Call create_site() first.")
        
        self._log(f"Setting up wind farm model with {wake_model}")
        
        # Select wake deficit model
        wake_models = {
            "NoWakeDeficit": NoWakeDeficit(),
            "BastankhahGaussianDeficit": BastankhahGaussianDeficit(),
            "NOJDeficit": NOJDeficit()
        }
        
        if wake_model not in wake_models:
            raise ValueError(f"Unknown wake model: {wake_model}. Options: {list(wake_models.keys())}")
        
        deficit_model = wake_models[wake_model]
        
        # Create wind farm model
        self._wind_farm_model = PropagateDownwind(
            self._site, 
            self._turbine, 
            wake_deficitModel=deficit_model
        )
        
        self.metadata['wind_farm_model_setup'] = True
        self.metadata['wake_model'] = wake_model
        
        self._log("Wind farm model setup complete")
        return self
    
    @property
    def wind_farm_model(self):
        """Get wind farm model."""
        if self._wind_farm_model is None:
            raise ValueError("Wind farm model not setup. Call setup_wind_farm_model() first.")
        return self._wind_farm_model
    
    # ============================================================================
    # SIMULATION EXECUTION
    # ============================================================================
    
    def run_simulation(self) -> 'WindEnergyPipeline':
        """
        Run wind farm simulation.
        
        Returns:
            Self for method chaining
        """
        # Ensure prerequisites are met
        if self._wind_farm_model is None:
            raise ValueError("Wind farm model not setup. Call setup_wind_farm_model() first.")
        if self._layout is None:
            raise ValueError("Layout not loaded. Call load_layout() first.")
        
        self._log("Running wind farm simulation...")
        
        x, y = self.turbine_coordinates
        
        # Extract time series data
        times = self._site.ds['time'].values
        wd = self._site.ds['wind_direction'].values
        ws = self._site.ds['wind_speed'].values
        
        # Run simulation
        self._simulation_results = self._wind_farm_model(x, y, wd=wd, ws=ws, time=times)
        
        self.metadata['simulation_complete'] = True
        self.metadata['n_timesteps'] = len(times)
        
        self._log(f"Simulation complete: {len(times)} timesteps, {len(x)} turbines")
        return self
    
    @property
    def simulation_results(self):
        """Get simulation results."""
        if self._simulation_results is None:
            raise ValueError("Simulation not run. Call run_simulation() first.")
        return self._simulation_results
    
    # ============================================================================
    # RESULTS PROCESSING
    # ============================================================================
    
    def process_results(self) -> 'WindEnergyPipeline':
        """
        Process simulation results into convenient formats.
        
        Returns:
            Self for method chaining
        """
        if self._simulation_results is None:
            raise ValueError("Simulation not run. Call run_simulation() first.")
        
        self._log("Processing simulation results...")
        
        # Convert to DataFrame
        sim_res_df = self._simulation_results.to_dataframe()
        
        # Ensure 'time' is a column
        if 'time' not in sim_res_df.columns and 'time' in sim_res_df.index.names:
            sim_res_df = sim_res_df.reset_index()
        
        # Add datetime column
        start_time = pd.to_datetime(f'{self.wind_config.start_year}-01-01 00:00')
        if 'time' in sim_res_df.columns:
            sim_res_df['datetime'] = [start_time + pd.Timedelta(hours=int(i)) for i in sim_res_df['time']]
        
        # Store processed results
        self.results['simulation_df'] = sim_res_df
        self.results['power_matrix'] = self._simulation_results.Power.values
        self.results['total_power_timeseries'] = self._simulation_results.Power.sum(axis=1).values
        
        # Calculate summary statistics
        total_energy_GWh = self.results['total_power_timeseries'].sum() / 1e9  # Convert W*h to GWh
        n_years = sim_res_df['datetime'].dt.year.nunique() if 'datetime' in sim_res_df.columns else 1
        annual_energy_GWh = total_energy_GWh / n_years
        
        self.results['total_energy_GWh'] = total_energy_GWh
        self.results['annual_energy_GWh'] = annual_energy_GWh
        
        self.metadata['results_processed'] = True
        
        self._log(f"Results processed. Annual energy: {annual_energy_GWh:.2f} GWh")
        return self
    
    # ============================================================================
    # CONVENIENCE METHODS
    # ============================================================================
    
    def run_full_pipeline(self) -> 'WindEnergyPipeline':
        """
        Run the complete wind analysis pipeline with default settings.
        
        Returns:
            Self for method chaining
        """
        self._log("Running full wind analysis pipeline...")
        
        return (self
                .load_turbine()
                .create_site()
                .load_layout()
                .setup_wind_farm_model()
                .run_simulation()
                .process_results())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of analysis results and metadata."""
        summary = {
            'metadata': self.metadata.copy(),
            'config': {
                'wind_config': self.wind_config,
                'site_config': self.site_config
            }
        }
        
        if self.results:
            # Fix capacity factor calculation
            annual_energy_GWh = self.results.get('annual_energy_GWh', 0)
            n_turbines = self.metadata.get('n_turbines', 1)
            
            # Calculate capacity factor properly
            # Assuming turbine rated power from turbine object
            if hasattr(self._turbine, 'power') and hasattr(self._turbine.power, 'max'):
                turbine_rated_power_MW = self._turbine.power.max() / 1e6  # Convert W to MW
            else:
                # Fallback estimate based on typical values
                turbine_rated_power_MW = 6.0  # MW, typical for large turbines
            
            total_rated_capacity_MW = n_turbines * turbine_rated_power_MW
            hours_per_year = 8760
            max_annual_energy_GWh = total_rated_capacity_MW * hours_per_year / 1000  # Convert MWh to GWh
            
            capacity_factor = annual_energy_GWh / max_annual_energy_GWh if max_annual_energy_GWh > 0 else 0
            
            summary['results_summary'] = {
                'annual_energy_GWh': annual_energy_GWh,
                'total_energy_GWh': self.results.get('total_energy_GWh'),
                'capacity_factor': capacity_factor,
                'n_turbines': n_turbines,
                'n_timesteps': self.metadata.get('n_timesteps'),
                'turbine_rated_power_MW': turbine_rated_power_MW,
                'total_rated_capacity_MW': total_rated_capacity_MW
            }
            
            # Store capacity factor in results for easy access
            self.results['capacity_factor'] = capacity_factor
        
        return summary
    
    # ============================================================================
    # PLOTTING METHODS (Klaus's Original Functions)
    # ============================================================================
    
    def plot_production_profiles(self, **kwargs):
        """
        Klaus's plot_production_profiles() - Yearly, seasonal, diurnal profiles.
        Wrapper for simulation.results.plot_production_profiles()
        """
        from simulation.results import plot_production_profiles
        
        if 'simulation_df' not in self.results:
            raise ValueError("Results not processed. Call process_results() first.")
        
        sim_res_df = self.results['simulation_df'].copy()
        
        # Ensure datetime column exists and is named correctly
        if 'datetime' not in sim_res_df.columns and 'datetime_x' in sim_res_df.columns:
            sim_res_df['datetime'] = sim_res_df['datetime_x']
        
        return plot_production_profiles(sim_res_df, **kwargs)
    
    def plot_energy_rose(self, **kwargs):
        """
        Klaus's plot_energy_rose() - Polar plot of power by wind direction.
        Wrapper for simulation.results.plot_energy_rose()
        """
        from simulation.results import plot_energy_rose
        
        if 'simulation_df' not in self.results:
            raise ValueError("Results not processed. Call process_results() first.")
        
        sim_res_df = self.results['simulation_df'].copy()
        
        # Sum power across all turbines for each timestep
        if 'Power' not in sim_res_df.columns:
            # If Power is not summed, we need to sum across turbines
            power_cols = [col for col in sim_res_df.columns if 'Power' in col or 'power' in col.lower()]
            if power_cols:
                sim_res_df['Power'] = sim_res_df[power_cols].sum(axis=1)
            else:
                raise ValueError("No power columns found in simulation results")
        
        return plot_energy_rose(sim_res_df, **kwargs)
    
    def plot_turbine_production(self, sim_res_no_wake=None, **kwargs):
        """
        Klaus's plot_turbine_production() - Stacked bar comparison with/without wake.
        Wrapper for simulation.results.plot_turbine_production()
        
        This function runs two simulations: one with wake and one without wake.
        """
        from simulation.results import plot_turbine_production
        from py_wake.deficit_models import NoWakeDeficit
        from py_wake.wind_farm_models import PropagateDownwind
        
        # If no_wake simulation not provided, run it
        if sim_res_no_wake is None:
            self._log("Running no-wake simulation for comparison...")
            no_wake_wfm = PropagateDownwind(self._site, self._turbine, wake_deficitModel=NoWakeDeficit())
            x, y = self.turbine_coordinates
            
            # Extract time series data (use same as main simulation)
            times = self._site.ds['time'].values
            wd = self._site.ds['wind_direction'].values  
            ws = self._site.ds['wind_speed'].values
            
            sim_res_no_wake = no_wake_wfm(x, y, wd=wd, ws=ws, time=times)
        
        return plot_turbine_production(sim_res_no_wake, self._simulation_results, **kwargs)
    
    def plot_wind_direction_vs_mean_power(self, **kwargs):
        """
        Klaus's plot_wind_direction_vs_mean_power() - Histogram of wind direction vs power.
        Wrapper for simulation.results.plot_wind_direction_vs_mean_power()
        """
        from simulation.results import plot_wind_direction_vs_mean_power
        
        if 'simulation_df' not in self.results:
            raise ValueError("Results not processed. Call process_results() first.")
        
        sim_res_df = self.results['simulation_df'].copy()
        
        # Sum power across all turbines for each timestep
        if 'Power' not in sim_res_df.columns:
            power_cols = [col for col in sim_res_df.columns if 'Power' in col or 'power' in col.lower()]
            if power_cols:
                sim_res_df['Power'] = sim_res_df[power_cols].sum(axis=1)
        
        return plot_wind_direction_vs_mean_power(sim_res_df, **kwargs)
    
    def plot_wake_maps(self, wd_ws_list=None, **kwargs):
        """
        Klaus's plot_wake_maps() - Wake visualization maps.
        Wrapper for simulation.results.plot_wake_maps()
        
        Args:
            wd_ws_list: List of (wind_direction, wind_speed) tuples.
                       If None, uses default values.
        """
        from simulation.results import plot_wake_maps
        
        if wd_ws_list is None:
            # Default wind conditions for the site
            wd_ws_list = [(60, 10)]  # Klaus mentioned to use single wd/ws
        
        # Klaus's function expects file paths, not objects
        # Use the same file paths from config
        plot_wake_maps(
            turbine_coords_file=self.wind_config.layout_csv_path,
            turbine_file=self.wind_config.turbine_csv_path,
            site_file=self.wind_config.vortex_path,
            n_sectors=self.wind_config.n_sectors,
            wd_ws_list=wd_ws_list,
            **kwargs
        )
    
    def plot_wind_speed_histogram(self, **kwargs):
        """
        Klaus's plot_wind_speed_histogram() - Wind speed distribution.
        Wrapper for simulation.results.plot_wind_speed_histogram()
        """
        from simulation.results import plot_wind_speed_histogram
        
        if 'simulation_df' not in self.results:
            raise ValueError("Results not processed. Call process_results() first.")
        
        sim_res_df = self.results['simulation_df'].copy()
        
        return plot_wind_speed_histogram(sim_res_df, **kwargs)
    
    def plot_wind_rose_from_site(self, **kwargs):
        """
        Klaus's plot_wind_rose_from_site() - Wind rose from site data.
        Wrapper for site_galvian.create_site.plot_wind_rose()
        """
        from site_galvian.create_site import plot_wind_rose
        
        # Extract wind data from site
        wd = self._site.ds['wind_direction'].values
        ws = self._site.ds['wind_speed'].values
        
        # Create frequency data that Klaus's function expects
        import pandas as pd
        wind_data = pd.DataFrame({
            'wind_direction': wd,
            'wind_speed': ws
        })
        
        return plot_wind_rose(wind_data, **kwargs)

    def plot_layers(self, **kwargs):
        """
        Klaus's plot_layers() - GIS layers plotting.
        Wrapper for windfarm_layout.plot_layers()
        """
        from windfarm_layout import plot_layers
        
        return plot_layers(**kwargs) 