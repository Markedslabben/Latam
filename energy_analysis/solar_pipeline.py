"""
Solar Energy Analysis Pipeline

Object-oriented wrapper around existing solar energy analysis functions.
Provides stateful pipeline with method chaining while preserving original functionality.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
import os
import sys

# Import existing modules
sys.path.append('.')
from PV_galvian.read_pvgis import read_pvgis
from shading_loss import calculate_annual_shading_loss

from .config import SolarConfig, SiteConfig, ShadingConfig


class SolarEnergyPipeline:
    """
    Solar energy analysis pipeline that maintains state and enables method chaining.
    
    Wraps existing functional code in an object-oriented interface for convenience.
    """
    
    def __init__(self, solar_config: SolarConfig, site_config: SiteConfig, 
                 shading_config: Optional[ShadingConfig] = None, verbose: bool = True):
        self.solar_config = solar_config
        self.site_config = site_config
        self.shading_config = shading_config
        self.verbose = verbose
        
        # State variables
        self._pvgis_data = None
        self._pv_production = None
        self._shading_analysis = None
        
        # Results storage
        self.results = {}
        self.metadata = {}
        
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[SolarPipeline] {message}")
    
    # ============================================================================
    # PVGIS DATA LOADING
    # ============================================================================
    
    def load_pvgis_data(self, csv_path: Optional[str] = None) -> 'SolarEnergyPipeline':
        """
        Load PVGIS solar data from CSV file.
        
        Args:
            csv_path: Path to PVGIS CSV file. If None, uses config default.
            
        Returns:
            Self for method chaining
        """
        csv_path = csv_path or self.solar_config.pvgis_csv_path
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"PVGIS CSV file not found: {csv_path}")
            
        self._log(f"Loading PVGIS data from {csv_path}")
        
        # Use existing function
        self._pvgis_data = read_pvgis(csv_path)
        
        # Apply capacity scaling
        capacity_factor = self.solar_config.installed_capacity_MW * 1e-6  # Convert MW to scaling factor
        self._pvgis_data['power_scaled'] = self._pvgis_data['power'] * capacity_factor
        
        self.metadata['pvgis_loaded'] = True
        self.metadata['pvgis_path'] = csv_path
        self.metadata['installed_capacity_MW'] = self.solar_config.installed_capacity_MW
        self.metadata['n_timesteps'] = len(self._pvgis_data)
        
        self._log(f"PVGIS data loaded: {len(self._pvgis_data)} timesteps")
        return self
    
    @property
    def pvgis_data(self) -> pd.DataFrame:
        """Get loaded PVGIS data."""
        if self._pvgis_data is None:
            raise ValueError("PVGIS data not loaded. Call load_pvgis_data() first.")
        return self._pvgis_data
    
    # ============================================================================
    # SHADING ANALYSIS
    # ============================================================================
    
    def analyze_shading(self, 
                       tower_locations: Optional[list] = None,
                       pv_locations: Optional[list] = None) -> 'SolarEnergyPipeline':
        """
        Analyze shading effects from wind turbine towers.
        
        Args:
            tower_locations: List of (x, y) tower coordinates. If None, uses single tower from config.
            pv_locations: List of (x, y) PV panel coordinates. If None, analyzes grid around towers.
            
        Returns:
            Self for method chaining
        """
        if self.shading_config is None:
            self._log("No shading configuration provided, skipping shading analysis")
            return self
        
        self._log("Analyzing shading effects...")
        
        # Default to single tower from config
        if tower_locations is None:
            tower_locations = [self.shading_config.tower_location]
        
        # If no PV locations specified, create analysis grid
        if pv_locations is None:
            pv_locations = self._create_analysis_grid()
        
        shading_results = []
        
        for i, tower_loc in enumerate(tower_locations):
            for j, pv_loc in enumerate(pv_locations):
                try:
                    # Calculate annual shading loss
                    _, annual_loss = calculate_annual_shading_loss(
                        latitude=self.site_config.latitude,
                        longitude=self.site_config.longitude,
                        altitude=self.site_config.altitude,
                        tower_height=self.shading_config.tower_height,
                        tower_diameter=self.shading_config.tower_diameter_base,
                        tower_diameter_top=self.shading_config.tower_diameter_top,
                        tower_location=tower_loc,
                        pv_location=pv_loc
                    )
                    
                    # Calculate distance and azimuth
                    dx = pv_loc[0] - tower_loc[0]
                    dy = pv_loc[1] - tower_loc[1]
                    distance = np.sqrt(dx**2 + dy**2)
                    azimuth = np.degrees(np.arctan2(dx, dy)) % 360
                    
                    shading_results.append({
                        'tower_id': i,
                        'pv_id': j,
                        'tower_x': tower_loc[0],
                        'tower_y': tower_loc[1],
                        'pv_x': pv_loc[0],
                        'pv_y': pv_loc[1],
                        'distance_m': distance,
                        'azimuth_deg': azimuth,
                        'annual_shading_loss_pct': annual_loss * 100
                    })
                    
                except Exception as e:
                    self._log(f"Shading calculation failed for tower {i}, PV {j}: {e}")
                    continue
        
        self._shading_analysis = pd.DataFrame(shading_results)
        
        self.metadata['shading_analyzed'] = True
        self.metadata['n_tower_locations'] = len(tower_locations)
        self.metadata['n_pv_locations'] = len(pv_locations)
        
        self._log(f"Shading analysis complete: {len(shading_results)} combinations analyzed")
        return self
    
    def _create_analysis_grid(self) -> list:
        """Create grid of PV locations for shading analysis."""
        distances = self.shading_config.analysis_distances
        azimuths = self.shading_config.analysis_azimuths
        
        pv_locations = []
        for distance in distances:
            for azimuth in azimuths:
                angle_rad = np.radians(azimuth)
                x = distance * np.sin(angle_rad)
                y = distance * np.cos(angle_rad)
                pv_locations.append((x, y))
        
        return pv_locations
    
    @property
    def shading_analysis(self) -> pd.DataFrame:
        """Get shading analysis results."""
        if self._shading_analysis is None:
            raise ValueError("Shading analysis not performed. Call analyze_shading() first.")
        return self._shading_analysis
    
    # ============================================================================
    # RESULTS PROCESSING
    # ============================================================================
    
    def process_results(self) -> 'SolarEnergyPipeline':
        """
        Process solar analysis results into convenient formats.
        
        Returns:
            Self for method chaining
        """
        self._log("Processing solar analysis results...")
        
        # Process PV production if available
        if self._pvgis_data is not None:
            total_energy_MWh = self._pvgis_data['power_scaled'].sum() / 1000  # Convert kWh to MWh
            annual_energy_MWh = total_energy_MWh  # Assuming annual data
            
            self.results['total_energy_MWh'] = total_energy_MWh
            self.results['annual_energy_MWh'] = annual_energy_MWh
            self.results['capacity_factor'] = (annual_energy_MWh / 
                                             (self.solar_config.installed_capacity_MW * 8760)) * 100
            
            # Store processed production data
            self.results['production_timeseries'] = self._pvgis_data.copy()
        
        # Process shading analysis if available
        if self._shading_analysis is not None:
            self.results['shading_summary'] = {
                'min_shading_loss_pct': self._shading_analysis['annual_shading_loss_pct'].min(),
                'max_shading_loss_pct': self._shading_analysis['annual_shading_loss_pct'].max(),
                'mean_shading_loss_pct': self._shading_analysis['annual_shading_loss_pct'].mean(),
                'optimal_location': self._get_optimal_pv_location()
            }
            
            self.results['shading_results'] = self._shading_analysis.copy()
        
        self.metadata['results_processed'] = True
        
        if 'annual_energy_MWh' in self.results:
            self._log(f"Results processed. Annual energy: {self.results['annual_energy_MWh']:.2f} MWh")
        
        return self
    
    def _get_optimal_pv_location(self) -> Dict[str, float]:
        """Find PV location with minimum shading loss."""
        if self._shading_analysis is None or len(self._shading_analysis) == 0:
            return {}
        
        min_idx = self._shading_analysis['annual_shading_loss_pct'].idxmin()
        optimal_row = self._shading_analysis.loc[min_idx]
        
        return {
            'pv_x': optimal_row['pv_x'],
            'pv_y': optimal_row['pv_y'],
            'distance_m': optimal_row['distance_m'],
            'azimuth_deg': optimal_row['azimuth_deg'],
            'shading_loss_pct': optimal_row['annual_shading_loss_pct']
        }
    
    # ============================================================================
    # CONVENIENCE METHODS
    # ============================================================================
    
    def run_full_pipeline(self) -> 'SolarEnergyPipeline':
        """
        Run the complete solar analysis pipeline with default settings.
        
        Returns:
            Self for method chaining
        """
        self._log("Running full solar analysis pipeline...")
        
        pipeline = self.load_pvgis_data()
        
        # Add shading analysis if configuration is available
        if self.shading_config is not None:
            pipeline = pipeline.analyze_shading()
        
        return pipeline.process_results()
    
    def run_shading_study(self) -> 'SolarEnergyPipeline':
        """
        Run focused shading analysis study.
        
        Returns:
            Self for method chaining
        """
        if self.shading_config is None:
            raise ValueError("Shading configuration required for shading study")
        
        self._log("Running shading study...")
        
        return (self
                .analyze_shading()
                .process_results())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of analysis results and metadata."""
        summary = {
            'metadata': self.metadata.copy(),
            'config': {
                'solar_config': self.solar_config,
                'site_config': self.site_config,
                'shading_config': self.shading_config
            }
        }
        
        if self.results:
            summary['results_summary'] = {
                'annual_energy_MWh': self.results.get('annual_energy_MWh'),
                'capacity_factor_pct': self.results.get('capacity_factor'),
                'installed_capacity_MW': self.solar_config.installed_capacity_MW
            }
            
            if 'shading_summary' in self.results:
                summary['results_summary']['shading_summary'] = self.results['shading_summary']
        
        return summary 