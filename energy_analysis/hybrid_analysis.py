"""
Hybrid Energy Analysis

Main class that combines wind and solar energy analysis pipelines.
Provides unified interface for comprehensive renewable energy analysis.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
import os
from datetime import datetime

from .config import AnalysisConfig
from .wind_pipeline import WindEnergyPipeline
from .solar_pipeline import SolarEnergyPipeline


class HybridEnergyAnalysis:
    """
    Hybrid energy analysis combining wind and solar energy pipelines.
    
    Provides unified interface for comprehensive renewable energy analysis
    including economic evaluation and combined optimization.
    """
    
    def __init__(self, config: AnalysisConfig, verbose: bool = True):
        self.config = config
        self.verbose = verbose
        
        # Initialize sub-pipelines
        self.wind = WindEnergyPipeline(
            wind_config=config.wind,
            site_config=config.site,
            verbose=verbose
        )
        
        self.solar = SolarEnergyPipeline(
            solar_config=config.solar,
            site_config=config.site,
            shading_config=config.shading,
            verbose=verbose
        )
        
        # Combined results storage
        self.combined_results = {}
        self.economic_results = {}
        self.metadata = {
            'analysis_started': datetime.now().isoformat(),
            'config_summary': config.summary()
        }
        
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[HybridAnalysis] {message}")
    
    # ============================================================================
    # SETUP AND VALIDATION
    # ============================================================================
    
    def validate_setup(self) -> Dict[str, Any]:
        """
        Validate configuration and check for missing files.
        
        Returns:
            Dictionary with validation results
        """
        self._log("Validating analysis setup...")
        
        validation_results = {
            'valid': True,
            'missing_files': [],
            'warnings': [],
            'config_issues': []
        }
        
        # Check for missing input files
        missing_files = self.config.validate_paths()
        if missing_files:
            validation_results['missing_files'] = missing_files
            validation_results['valid'] = False
            self._log(f"Missing files: {missing_files}")
        
        # Create output directories
        try:
            self.config.create_output_dirs()
            self._log("Output directories created/verified")
        except Exception as e:
            validation_results['warnings'].append(f"Could not create output directories: {e}")
        
        # Validate time periods match
        if (self.config.wind.start_year != self.config.wind.end_year and 
            len(missing_files) == 0):  # Only check if files exist
            validation_results['warnings'].append(
                f"Multi-year analysis: {self.config.wind.start_year}-{self.config.wind.end_year}"
            )
        
        self.metadata['validation_results'] = validation_results
        
        if validation_results['valid']:
            self._log("Setup validation passed")
        else:
            self._log("Setup validation failed - check missing files")
        
        return validation_results
    
    # ============================================================================
    # PIPELINE EXECUTION
    # ============================================================================
    
    def run_wind_analysis(self) -> 'HybridEnergyAnalysis':
        """
        Run complete wind energy analysis.
        
        Returns:
            Self for method chaining
        """
        self._log("Running wind energy analysis...")
        
        try:
            self.wind.run_full_pipeline()
            self.metadata['wind_analysis_complete'] = True
            self._log("Wind analysis completed successfully")
        except Exception as e:
            self._log(f"Wind analysis failed: {e}")
            self.metadata['wind_analysis_error'] = str(e)
            raise
        
        return self
    
    def run_solar_analysis(self) -> 'HybridEnergyAnalysis':
        """
        Run complete solar energy analysis.
        
        Returns:
            Self for method chaining
        """
        self._log("Running solar energy analysis...")
        
        try:
            self.solar.run_full_pipeline()
            self.metadata['solar_analysis_complete'] = True
            self._log("Solar analysis completed successfully")
        except Exception as e:
            self._log(f"Solar analysis failed: {e}")
            self.metadata['solar_analysis_error'] = str(e)
            raise
        
        return self
    
    def run_full_analysis(self) -> 'HybridEnergyAnalysis':
        """
        Run complete hybrid energy analysis including both wind and solar.
        
        Returns:
            Self for method chaining
        """
        self._log("Running full hybrid energy analysis...")
        
        # Validate setup first
        validation = self.validate_setup()
        if not validation['valid']:
            raise ValueError(f"Setup validation failed: {validation['missing_files']}")
        
        # Run both analyses
        self.run_wind_analysis()
        self.run_solar_analysis()
        
        # Combine results
        self.combine_results()
        
        # Run economic analysis if price data available
        try:
            self.calculate_economics()
        except Exception as e:
            self._log(f"Economic analysis failed: {e}")
            self.metadata['economic_analysis_error'] = str(e)
        
        self.metadata['full_analysis_complete'] = True
        self._log("Full hybrid analysis completed")
        
        return self
    
    # ============================================================================
    # RESULTS COMBINATION
    # ============================================================================
    
    def combine_results(self) -> 'HybridEnergyAnalysis':
        """
        Combine wind and solar analysis results.
        
        Returns:
            Self for method chaining
        """
        self._log("Combining wind and solar results...")
        
        # Initialize combined results
        self.combined_results = {
            'summary': {},
            'timeseries': {},
            'totals': {}
        }
        
        # Combine energy production summaries
        wind_summary = self.wind.get_summary().get('results_summary', {})
        solar_summary = self.solar.get_summary().get('results_summary', {})
        
        self.combined_results['summary'] = {
            'wind': wind_summary,
            'solar': solar_summary
        }
        
        # Calculate combined totals
        wind_annual_GWh = wind_summary.get('annual_energy_GWh', 0)
        solar_annual_MWh = solar_summary.get('annual_energy_MWh', 0)
        solar_annual_GWh = solar_annual_MWh / 1000  # Convert MWh to GWh
        
        total_annual_GWh = wind_annual_GWh + solar_annual_GWh
        
        self.combined_results['totals'] = {
            'wind_annual_GWh': wind_annual_GWh,
            'solar_annual_GWh': solar_annual_GWh,
            'total_annual_GWh': total_annual_GWh,
            'wind_capacity_MW': self.config.wind.rated_power_MW * wind_summary.get('n_turbines', 0),
            'solar_capacity_MW': self.config.solar.installed_capacity_MW,
            'total_capacity_MW': (self.config.wind.rated_power_MW * wind_summary.get('n_turbines', 0) + 
                                self.config.solar.installed_capacity_MW)
        }
        
        # Calculate combined capacity factor
        if self.combined_results['totals']['total_capacity_MW'] > 0:
            self.combined_results['totals']['combined_capacity_factor_pct'] = (
                total_annual_GWh * 1000 / 
                (self.combined_results['totals']['total_capacity_MW'] * 8760) * 100
            )
        
        # Try to combine time series if both are available
        try:
            self._combine_timeseries()
        except Exception as e:
            self._log(f"Could not combine time series: {e}")
        
        self.metadata['results_combined'] = True
        self._log(f"Results combined. Total annual energy: {total_annual_GWh:.2f} GWh")
        
        return self
    
    def _combine_timeseries(self):
        """Combine wind and solar time series data."""
        # Get wind results
        if 'simulation_df' in self.wind.results:
            wind_df = self.wind.results['simulation_df'].copy()
        else:
            return
        
        # Get solar results
        if 'production_timeseries' in self.solar.results:
            solar_df = self.solar.results['production_timeseries'].copy()
        else:
            return
        
        # Align time series (this is simplified - may need more sophisticated alignment)
        if len(wind_df) == len(solar_df):
            combined_df = wind_df.copy()
            combined_df['solar_power_kW'] = solar_df['power_scaled'].values * 1000  # Convert to kW
            combined_df['total_power_kW'] = (
                combined_df['Power'].sum(axis=1) / 1000 +  # Convert W to kW
                combined_df['solar_power_kW']
            )
            
            self.combined_results['timeseries'] = combined_df
            self._log("Time series combined successfully")
    
    # ============================================================================
    # ECONOMIC ANALYSIS
    # ============================================================================
    
    def calculate_economics(self) -> 'HybridEnergyAnalysis':
        """
        Calculate economic metrics for the hybrid system.
        
        Returns:
            Self for method chaining
        """
        self._log("Calculating economic metrics...")
        
        # This is a placeholder for economic analysis
        # Would integrate with existing electricity price data
        
        try:
            from site_galvian.create_site import read_electricity_price
            
            # Load electricity prices
            price_data = read_electricity_price(
                self.config.economic.price_excel_path,
                include_leap_year=self.config.economic.include_leap_year,
                exchange_rate=self.config.economic.exchange_rate
            )
            
            # Calculate revenue if time series are available
            if 'timeseries' in self.combined_results:
                combined_df = self.combined_results['timeseries']
                
                # Align with price data (simplified)
                if len(combined_df) == len(price_data):
                    combined_df['price_USD_MWh'] = price_data['price'].values
                    combined_df['revenue_USD'] = (
                        combined_df['total_power_kW'] * combined_df['price_USD_MWh'] / 1000
                    )
                    
                    annual_revenue = combined_df['revenue_USD'].sum()
                    
                    self.economic_results = {
                        'annual_revenue_USD': annual_revenue,
                        'average_price_USD_MWh': price_data['price'].mean(),
                        'revenue_per_MWh': annual_revenue / (self.combined_results['totals']['total_annual_GWh'] * 1000)
                    }
                    
                    self._log(f"Economic analysis complete. Annual revenue: ${annual_revenue:,.0f}")
            
        except Exception as e:
            self._log(f"Economic analysis failed: {e}")
            raise
        
        return self
    
    # ============================================================================
    # REPORTING AND EXPORT
    # ============================================================================
    
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all analysis results."""
        summary = {
            'metadata': self.metadata,
            'configuration': {
                'site': self.config.site,
                'wind': self.config.wind,
                'solar': self.config.solar,
                'economic': self.config.economic
            },
            'wind_analysis': self.wind.get_summary(),
            'solar_analysis': self.solar.get_summary(),
            'combined_results': self.combined_results,
            'economic_results': self.economic_results
        }
        
        return summary
    
    def export_results(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Export all results to files.
        
        Args:
            output_dir: Output directory. If None, uses config default.
            
        Returns:
            Dictionary mapping result type to file path
        """
        output_dir = output_dir or self.config.output.results_dir
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime(self.config.output.timestamp_format)
        prefix = f"{self.config.output.results_prefix}_{timestamp}"
        
        exported_files = {}
        
        try:
            # Export comprehensive summary
            summary_path = os.path.join(output_dir, f"{prefix}_summary.json")
            import json
            with open(summary_path, 'w') as f:
                json.dump(self.get_comprehensive_summary(), f, indent=2, default=str)
            exported_files['summary'] = summary_path
            
            # Export combined time series if available
            if 'timeseries' in self.combined_results:
                timeseries_path = os.path.join(output_dir, f"{prefix}_timeseries.csv")
                self.combined_results['timeseries'].to_csv(timeseries_path, index=False)
                exported_files['timeseries'] = timeseries_path
            
            # Export wind results
            if 'simulation_df' in self.wind.results:
                wind_path = os.path.join(output_dir, f"{prefix}_wind_results.csv")
                self.wind.results['simulation_df'].to_csv(wind_path, index=False)
                exported_files['wind_results'] = wind_path
            
            # Export solar results
            if 'production_timeseries' in self.solar.results:
                solar_path = os.path.join(output_dir, f"{prefix}_solar_results.csv")
                self.solar.results['production_timeseries'].to_csv(solar_path, index=False)
                exported_files['solar_results'] = solar_path
            
            # Export shading analysis if available
            if 'shading_results' in self.solar.results:
                shading_path = os.path.join(output_dir, f"{prefix}_shading_analysis.csv")
                self.solar.results['shading_results'].to_csv(shading_path, index=False)
                exported_files['shading_analysis'] = shading_path
            
            self._log(f"Results exported to {output_dir}")
            
        except Exception as e:
            self._log(f"Export failed: {e}")
            raise
        
        return exported_files
    
    # ============================================================================
    # CONVENIENCE CLASS METHODS
    # ============================================================================
    
    @classmethod
    def from_defaults(cls, verbose: bool = True) -> 'HybridEnergyAnalysis':
        """Create analysis with default configuration."""
        config = AnalysisConfig.from_defaults()
        return cls(config, verbose=verbose)
    
    @classmethod
    def quick_analysis(cls, verbose: bool = True) -> 'HybridEnergyAnalysis':
        """Run quick analysis with defaults and return results."""
        analysis = cls.from_defaults(verbose=verbose)
        return analysis.run_full_analysis()
    
    def print_summary(self):
        """Print a formatted summary of results."""
        if not self.combined_results:
            print("No results available. Run analysis first.")
            return
        
        print("\n" + "="*60)
        print("HYBRID ENERGY ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\nSite Location: {self.config.site.latitude:.5f}°N, {self.config.site.longitude:.5f}°W")
        print(f"Analysis Period: {self.config.wind.start_year}-{self.config.wind.end_year}")
        
        totals = self.combined_results.get('totals', {})
        
        print(f"\nINSTALLED CAPACITY:")
        print(f"  Wind: {totals.get('wind_capacity_MW', 0):.1f} MW")
        print(f"  Solar: {totals.get('solar_capacity_MW', 0):.1f} MW")
        print(f"  Total: {totals.get('total_capacity_MW', 0):.1f} MW")
        
        print(f"\nANNUAL ENERGY PRODUCTION:")
        print(f"  Wind: {totals.get('wind_annual_GWh', 0):.2f} GWh")
        print(f"  Solar: {totals.get('solar_annual_GWh', 0):.2f} GWh")
        print(f"  Total: {totals.get('total_annual_GWh', 0):.2f} GWh")
        
        if 'combined_capacity_factor_pct' in totals:
            print(f"\nCombined Capacity Factor: {totals['combined_capacity_factor_pct']:.1f}%")
        
        if self.economic_results:
            print(f"\nECONOMIC RESULTS:")
            print(f"  Annual Revenue: ${self.economic_results.get('annual_revenue_USD', 0):,.0f}")
            print(f"  Average Price: ${self.economic_results.get('average_price_USD_MWh', 0):.2f}/MWh")
        
        print("\n" + "="*60) 