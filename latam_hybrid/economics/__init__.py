"""
Economics and financial analysis module.

Provides financial modeling, LCOE/NPV/IRR calculations, revenue estimation,
and sensitivity analysis for hybrid energy projects.
"""

# Parameters
from .parameters import (
    CapexBreakdown,
    OpexBreakdown,
    RevenueParameters,
    FinancingParameters,
    EconomicParameters,
    create_wind_economics,
    create_solar_economics,
    create_hybrid_economics
)

# Financial metrics
from .metrics import (
    calculate_lcoe,
    calculate_npv,
    calculate_irr,
    calculate_payback_period,
    FinancialMetrics,
    calculate_all_metrics,
    compare_scenarios as compare_scenarios_metrics
)

# Revenue calculations
from .revenue import (
    calculate_revenue_timeseries,
    calculate_annual_revenue,
    calculate_revenue_profile,
    create_price_profile_tod,
    create_price_profile_seasonal,
    apply_price_profile_to_timeseries,
    calculate_merchant_revenue
)

# Sensitivity analysis
from .sensitivity import (
    SensitivityResult,
    sensitivity_analysis,
    ScenarioComparison,
    compare_scenarios,
    MonteCarloResult,
    monte_carlo_simulation
)


__all__ = [
    # Parameters
    'CapexBreakdown',
    'OpexBreakdown',
    'RevenueParameters',
    'FinancingParameters',
    'EconomicParameters',
    'create_wind_economics',
    'create_solar_economics',
    'create_hybrid_economics',

    # Metrics
    'calculate_lcoe',
    'calculate_npv',
    'calculate_irr',
    'calculate_payback_period',
    'FinancialMetrics',
    'calculate_all_metrics',
    'compare_scenarios_metrics',

    # Revenue
    'calculate_revenue_timeseries',
    'calculate_annual_revenue',
    'calculate_revenue_profile',
    'create_price_profile_tod',
    'create_price_profile_seasonal',
    'apply_price_profile_to_timeseries',
    'calculate_merchant_revenue',

    # Sensitivity
    'SensitivityResult',
    'sensitivity_analysis',
    'ScenarioComparison',
    'compare_scenarios',
    'MonteCarloResult',
    'monte_carlo_simulation',
]
