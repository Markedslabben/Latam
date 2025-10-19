"""
Solar energy analysis module.

Provides PV system configuration, solar site analysis, and shading calculations.
"""

from .system import SolarSystem, PVSystemConfig, create_solar_system
from .site import SolarSite, create_solar_site
from .shading import ShadingCalculator, calculate_simple_shading_loss

__all__ = [
    'SolarSystem',
    'PVSystemConfig',
    'create_solar_system',
    'SolarSite',
    'create_solar_site',
    'ShadingCalculator',
    'calculate_simple_shading_loss',
]
