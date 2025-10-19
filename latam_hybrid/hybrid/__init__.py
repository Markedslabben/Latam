"""
Hybrid analysis module.

Provides high-level orchestration and workflows for complete wind+solar
hybrid energy analysis.
"""

from .analysis import HybridAnalysis

from .workflows import (
    analyze_wind_solar_hybrid,
    analyze_wind_only,
    analyze_solar_only,
    quick_feasibility_study,
    compare_scenarios,
)

__all__ = [
    # Orchestration
    'HybridAnalysis',

    # Workflows
    'analyze_wind_solar_hybrid',
    'analyze_wind_only',
    'analyze_solar_only',
    'quick_feasibility_study',
    'compare_scenarios',
]
