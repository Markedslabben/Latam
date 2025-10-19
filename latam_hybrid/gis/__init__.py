"""
GIS and spatial analysis module.

Provides geospatial operations, planning area management, and visualization
for hybrid energy projects.
"""

# Planning area management
from .area import SiteArea, load_planning_area

# Spatial utilities
from .spatial import (
    calculate_distance_matrix,
    haversine_distance,
    find_nearest_points,
    calculate_bearing,
    convert_crs,
    calculate_polygon_area,
    point_in_polygon,
    create_grid_points,
    calculate_setback_distance
)

# Visualization (optional, requires matplotlib)
try:
    from .visualization import (
        plot_site_map,
        plot_turbine_layout,
        plot_distance_heatmap,
        plot_wind_rose,
        plot_power_curve,
        plot_production_timeseries,
        quick_site_plot
    )
    _HAS_VISUALIZATION = True
except ImportError:
    _HAS_VISUALIZATION = False


__all__ = [
    # Area management
    'SiteArea',
    'load_planning_area',

    # Spatial operations
    'calculate_distance_matrix',
    'haversine_distance',
    'find_nearest_points',
    'calculate_bearing',
    'convert_crs',
    'calculate_polygon_area',
    'point_in_polygon',
    'create_grid_points',
    'calculate_setback_distance',
]

# Add visualization exports if available
if _HAS_VISUALIZATION:
    __all__.extend([
        'plot_site_map',
        'plot_turbine_layout',
        'plot_distance_heatmap',
        'plot_wind_rose',
        'plot_power_curve',
        'plot_production_timeseries',
        'quick_site_plot',
    ])
