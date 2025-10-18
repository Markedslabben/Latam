"""
Configuration management for energy analysis pipelines.

Centralizes all parameters and file paths used across wind and solar analysis.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import os


@dataclass
class WindConfig:
    """Configuration for wind energy analysis."""
    
    # Turbine parameters
    turbine_csv_path: str = "Inputdata/Nordex N164.csv"
    turbine_name: str = "Nordex N164"
    turbine_diameter: float = 164.0  # meters
    hub_height: float = 163.0  # meters
    
    # Site data
    vortex_data_path: str = "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    layout_csv_path: str = "Inputdata/turbine_layout_13.csv"
    
    # Time period
    start_year: int = 2014
    end_year: int = 2024
    include_leap_year: bool = False
    
    # Wake modeling
    wake_model: str = "BastankhahGaussianDeficit"  # Options: "NoWakeDeficit", "BastankhahGaussianDeficit", "NOJDeficit"
    
    # Wind distribution analysis
    n_sectors: int = 16
    
    # Sector management (allowed wind directions for operation)
    allowed_sectors: List[Tuple[int, int]] = field(default_factory=lambda: [(60, 120), (240, 300)])
    wake_loss_sectors: List[Tuple[int, int]] = field(default_factory=lambda: [(60, 120), (240, 300)])
    
    # Turbine specifications
    rated_power_MW: float = 7.0


@dataclass 
class SolarConfig:
    """Configuration for solar energy analysis."""
    
    # PV system parameters
    pvgis_csv_path: str = "Inputdata/PVGIS timeseries.csv"
    installed_capacity_MW: float = 120.0
    module_type: str = "LONGi_LR5_72HPH_540M"
    
    # Site parameters
    azimuth: float = 180.0  # degrees (180 = south-facing)
    tilt: float = 20.0  # degrees
    albedo: float = 0.2
    
    # Time alignment
    time_shift_hours: int = -4  # Shift for timezone alignment
    time_offset_minutes: int = 30  # Offset for price data alignment


@dataclass
class ShadingConfig:
    """Configuration for shading analysis."""
    
    # Tower parameters
    tower_height: float = 164.0  # meters
    tower_diameter_base: float = 6.0  # meters
    tower_diameter_top: float = 3.0  # meters
    tower_location: Tuple[float, float] = (0.0, 0.0)  # (x, y) coordinates
    
    # Analysis grid
    analysis_distances: List[int] = field(default_factory=lambda: list(range(10, 151, 10)))
    analysis_azimuths: List[int] = field(default_factory=lambda: list(range(0, 361, 30)))


@dataclass
class EconomicConfig:
    """Configuration for economic analysis."""
    
    # Electricity pricing
    price_excel_path: str = "Inputdata/20250505 Spotmarket Prices_2024.xlsx"
    exchange_rate: float = 59.45  # RD$ to USD
    include_leap_year: bool = False


@dataclass
class SiteConfig:
    """Configuration for site location and environmental parameters."""
    
    # Geographic location
    latitude: float = 19.71814
    longitude: float = -71.35602
    altitude: float = 300.0  # meters
    timezone: str = "UTC-4"
    
    # Environmental
    default_turbulence_intensity: float = 0.1


@dataclass
class OutputConfig:
    """Configuration for output files and directories."""
    
    # Output directories
    results_dir: str = "results"
    plots_dir: str = "plots"
    output_dir: str = "output"
    
    # File naming
    results_prefix: str = "analysis"
    timestamp_format: str = "%Y%m%d_%H%M%S"
    
    # Plot settings
    plot_dpi: int = 300
    plot_format: str = "png"


@dataclass
class AnalysisConfig:
    """Main configuration class combining all analysis parameters."""
    
    # Sub-configurations
    site: SiteConfig = field(default_factory=SiteConfig)
    wind: WindConfig = field(default_factory=WindConfig)
    solar: SolarConfig = field(default_factory=SolarConfig)
    shading: ShadingConfig = field(default_factory=ShadingConfig)
    economic: EconomicConfig = field(default_factory=EconomicConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Global settings
    debug: bool = False
    verbose: bool = True
    
    @classmethod
    def from_defaults(cls):
        """Create configuration with all default values."""
        return cls()
    
    @classmethod
    def from_dict(cls, config_dict: dict):
        """Create configuration from dictionary."""
        # This would implement loading from JSON/YAML if needed
        return cls(**config_dict)
    
    def validate_paths(self) -> List[str]:
        """Validate that all required input files exist."""
        missing_files = []
        
        # Check wind files
        if not os.path.exists(self.wind.turbine_csv_path):
            missing_files.append(self.wind.turbine_csv_path)
        if not os.path.exists(self.wind.vortex_data_path):
            missing_files.append(self.wind.vortex_data_path)
        if not os.path.exists(self.wind.layout_csv_path):
            missing_files.append(self.wind.layout_csv_path)
            
        # Check solar files
        if not os.path.exists(self.solar.pvgis_csv_path):
            missing_files.append(self.solar.pvgis_csv_path)
            
        # Check economic files
        if not os.path.exists(self.economic.price_excel_path):
            missing_files.append(self.economic.price_excel_path)
            
        return missing_files
    
    def create_output_dirs(self):
        """Create output directories if they don't exist."""
        for dir_path in [self.output.results_dir, self.output.plots_dir, self.output.output_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def summary(self) -> str:
        """Return a summary of the configuration."""
        return f"""
Analysis Configuration Summary:
==============================
Site: {self.site.latitude:.5f}°N, {self.site.longitude:.5f}°W
Wind Analysis: {self.wind.start_year}-{self.wind.end_year}
Solar Capacity: {self.solar.installed_capacity_MW} MW
Wind Turbines: {self.wind.turbine_name}
Wake Model: {self.wind.wake_model}
Output Directory: {self.output.results_dir}
""" 