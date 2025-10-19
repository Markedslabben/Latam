"""
Financial metrics calculations for hybrid energy projects.

LCOE, NPV, IRR, payback period, and other economic indicators.
"""

from typing import Tuple, Optional, Dict, List
import numpy as np
from dataclasses import dataclass

from .parameters import EconomicParameters


def calculate_lcoe(
    annual_production_mwh: float,
    economic_params: EconomicParameters
) -> float:
    """
    Calculate Levelized Cost of Energy (LCOE).

    LCOE = (Sum of discounted costs) / (Sum of discounted production)

    Args:
        annual_production_mwh: Annual energy production in MWh
        economic_params: Economic parameters

    Returns:
        LCOE in currency/MWh

    Example:
        >>> params = create_wind_economics(capacity_mw=50, capex_per_kw=1400)
        >>> lcoe = calculate_lcoe(annual_production_mwh=150000, economic_params=params)
    """
    n_years = economic_params.financing.project_lifetime
    discount_rate = economic_params.financing.discount_rate

    # Initial investment
    capex = economic_params.total_capex

    # Annual costs (fixed + variable)
    fixed_opex = economic_params.annual_fixed_opex
    variable_opex_per_mwh = economic_params.variable_opex_per_mwh

    # Calculate present value of costs
    pv_costs = capex  # Initial investment

    for year in range(1, n_years + 1):
        discount_factor = (1 + discount_rate) ** year
        annual_opex = fixed_opex + (annual_production_mwh * variable_opex_per_mwh)
        pv_costs += annual_opex / discount_factor

    # Calculate present value of production
    pv_production = 0
    for year in range(1, n_years + 1):
        discount_factor = (1 + discount_rate) ** year
        pv_production += annual_production_mwh / discount_factor

    lcoe = pv_costs / pv_production

    return lcoe


def calculate_npv(
    annual_production_mwh: float,
    economic_params: EconomicParameters,
    production_profile: Optional[np.ndarray] = None
) -> float:
    """
    Calculate Net Present Value (NPV).

    Args:
        annual_production_mwh: Annual energy production in MWh (or average if profile provided)
        economic_params: Economic parameters
        production_profile: Optional array of annual production (length = project_lifetime)

    Returns:
        NPV in currency

    Example:
        >>> params = create_wind_economics(capacity_mw=50, electricity_price=50)
        >>> npv = calculate_npv(annual_production_mwh=150000, economic_params=params)
    """
    n_years = economic_params.financing.project_lifetime
    discount_rate = economic_params.financing.discount_rate

    # Initial investment (negative cash flow)
    npv = -economic_params.total_capex

    # Use production profile if provided, otherwise assume constant production
    if production_profile is None:
        production_profile = np.full(n_years, annual_production_mwh)
    elif len(production_profile) != n_years:
        raise ValueError(
            f"Production profile length ({len(production_profile)}) "
            f"must match project lifetime ({n_years})"
        )

    # Annual cash flows
    for year in range(1, n_years + 1):
        production_year = production_profile[year - 1]

        # Revenue
        price_escalation = economic_params.revenue.price_escalation
        electricity_price = (
            economic_params.revenue.electricity_price *
            (1 + price_escalation) ** (year - 1)
        )

        revenue = (
            production_year *
            electricity_price *
            economic_params.revenue.curtailment_factor *
            economic_params.revenue.availability
        )

        # Operating costs
        fixed_opex = economic_params.annual_fixed_opex
        variable_opex = production_year * economic_params.variable_opex_per_mwh
        total_opex = fixed_opex + variable_opex

        # Net cash flow for this year
        cash_flow = revenue - total_opex

        # Discount to present value
        discount_factor = (1 + discount_rate) ** year
        npv += cash_flow / discount_factor

    return npv


def calculate_irr(
    annual_production_mwh: float,
    economic_params: EconomicParameters,
    production_profile: Optional[np.ndarray] = None,
    max_iterations: int = 1000,
    tolerance: float = 1e-6
) -> Optional[float]:
    """
    Calculate Internal Rate of Return (IRR).

    Uses Newton-Raphson method to find IRR where NPV = 0.

    Args:
        annual_production_mwh: Annual energy production in MWh
        economic_params: Economic parameters
        production_profile: Optional array of annual production
        max_iterations: Maximum iterations for convergence
        tolerance: Convergence tolerance

    Returns:
        IRR as decimal (e.g., 0.12 for 12%) or None if not found

    Example:
        >>> params = create_wind_economics(capacity_mw=50, electricity_price=60)
        >>> irr = calculate_irr(annual_production_mwh=150000, economic_params=params)
    """
    n_years = economic_params.financing.project_lifetime

    # Build cash flow array
    cash_flows = np.zeros(n_years + 1)
    cash_flows[0] = -economic_params.total_capex  # Initial investment

    if production_profile is None:
        production_profile = np.full(n_years, annual_production_mwh)

    for year in range(1, n_years + 1):
        production_year = production_profile[year - 1]

        # Revenue with price escalation
        price_escalation = economic_params.revenue.price_escalation
        electricity_price = (
            economic_params.revenue.electricity_price *
            (1 + price_escalation) ** (year - 1)
        )

        revenue = (
            production_year *
            electricity_price *
            economic_params.revenue.curtailment_factor *
            economic_params.revenue.availability
        )

        # Costs
        fixed_opex = economic_params.annual_fixed_opex
        variable_opex = production_year * economic_params.variable_opex_per_mwh

        cash_flows[year] = revenue - fixed_opex - variable_opex

    # Use numpy's IRR calculation (faster and more robust)
    try:
        irr = np.irr(cash_flows)
        if np.isnan(irr) or np.isinf(irr):
            return None
        return irr
    except:
        # Fallback to Newton-Raphson if numpy.irr fails
        return _irr_newton_raphson(cash_flows, max_iterations, tolerance)


def _irr_newton_raphson(
    cash_flows: np.ndarray,
    max_iterations: int,
    tolerance: float
) -> Optional[float]:
    """Newton-Raphson method for IRR calculation."""
    rate = 0.1  # Initial guess

    for _ in range(max_iterations):
        # Calculate NPV and derivative at current rate
        npv = 0
        dnpv = 0

        for t, cf in enumerate(cash_flows):
            npv += cf / ((1 + rate) ** t)
            if t > 0:
                dnpv -= t * cf / ((1 + rate) ** (t + 1))

        if abs(npv) < tolerance:
            return rate

        if abs(dnpv) < 1e-10:  # Avoid division by zero
            return None

        # Newton-Raphson update
        rate = rate - npv / dnpv

        # Keep rate in reasonable bounds
        if rate < -0.99 or rate > 10:
            return None

    return None  # Did not converge


def calculate_payback_period(
    annual_production_mwh: float,
    economic_params: EconomicParameters,
    discounted: bool = True
) -> Optional[float]:
    """
    Calculate payback period in years.

    Args:
        annual_production_mwh: Annual energy production in MWh
        economic_params: Economic parameters
        discounted: If True, use discounted cash flows (DPP), else simple payback

    Returns:
        Payback period in years, or None if never pays back

    Example:
        >>> params = create_wind_economics(capacity_mw=50, electricity_price=60)
        >>> payback = calculate_payback_period(150000, params, discounted=True)
    """
    n_years = economic_params.financing.project_lifetime
    discount_rate = economic_params.financing.discount_rate if discounted else 0

    cumulative_cash_flow = -economic_params.total_capex

    for year in range(1, n_years + 1):
        # Revenue with price escalation
        price_escalation = economic_params.revenue.price_escalation
        electricity_price = (
            economic_params.revenue.electricity_price *
            (1 + price_escalation) ** (year - 1)
        )

        revenue = (
            annual_production_mwh *
            electricity_price *
            economic_params.revenue.curtailment_factor *
            economic_params.revenue.availability
        )

        # Costs
        fixed_opex = economic_params.annual_fixed_opex
        variable_opex = annual_production_mwh * economic_params.variable_opex_per_mwh

        cash_flow = revenue - fixed_opex - variable_opex

        # Discount if needed
        if discounted:
            cash_flow /= (1 + discount_rate) ** year

        cumulative_cash_flow += cash_flow

        # Check if we've paid back
        if cumulative_cash_flow >= 0:
            # Interpolate to get fractional year
            prev_cumulative = cumulative_cash_flow - cash_flow
            fraction = -prev_cumulative / cash_flow
            return year - 1 + fraction

    return None  # Never pays back within project lifetime


@dataclass
class FinancialMetrics:
    """
    Complete financial metrics for a project.
    """
    lcoe: float  # Levelized Cost of Energy (currency/MWh)
    npv: float  # Net Present Value (currency)
    irr: Optional[float]  # Internal Rate of Return (decimal)
    payback_period: Optional[float]  # Payback period (years)
    discounted_payback_period: Optional[float]  # Discounted payback (years)

    # Additional metrics
    benefit_cost_ratio: float  # Benefit/Cost ratio
    profitability_index: float  # (NPV + Initial Investment) / Initial Investment

    # Metadata
    annual_production_mwh: float
    capacity_factor: float
    currency: str

    def __repr__(self) -> str:
        irr_str = f"{self.irr:.1%}" if self.irr is not None else "N/A"
        payback_str = f"{self.payback_period:.1f}yr" if self.payback_period else "Never"

        return (
            f"FinancialMetrics(\n"
            f"  LCOE: {self.lcoe:.2f} {self.currency}/MWh\n"
            f"  NPV: {self.npv/1e6:.2f}M {self.currency}\n"
            f"  IRR: {irr_str}\n"
            f"  Payback: {payback_str}\n"
            f"  CF: {self.capacity_factor:.1%}\n"
            f")"
        )


def calculate_all_metrics(
    annual_production_mwh: float,
    installed_capacity_mw: float,
    economic_params: EconomicParameters,
    production_profile: Optional[np.ndarray] = None
) -> FinancialMetrics:
    """
    Calculate all financial metrics in one call.

    Args:
        annual_production_mwh: Annual energy production in MWh
        installed_capacity_mw: Installed capacity in MW
        economic_params: Economic parameters
        production_profile: Optional array of annual production

    Returns:
        FinancialMetrics with all calculated indicators

    Example:
        >>> params = create_wind_economics(capacity_mw=50, electricity_price=55)
        >>> metrics = calculate_all_metrics(
        ...     annual_production_mwh=150000,
        ...     installed_capacity_mw=50,
        ...     economic_params=params
        ... )
        >>> print(metrics)
    """
    # Calculate capacity factor
    hours_per_year = 8760
    max_annual_mwh = installed_capacity_mw * hours_per_year
    capacity_factor = annual_production_mwh / max_annual_mwh

    # Calculate all metrics
    lcoe = calculate_lcoe(annual_production_mwh, economic_params)
    npv = calculate_npv(annual_production_mwh, economic_params, production_profile)
    irr = calculate_irr(annual_production_mwh, economic_params, production_profile)

    payback_simple = calculate_payback_period(
        annual_production_mwh,
        economic_params,
        discounted=False
    )

    payback_discounted = calculate_payback_period(
        annual_production_mwh,
        economic_params,
        discounted=True
    )

    # Calculate benefit/cost ratio
    total_pv_revenue = npv + economic_params.total_capex
    bcr = total_pv_revenue / economic_params.total_capex if economic_params.total_capex > 0 else 0

    # Profitability index
    pi = (npv + economic_params.total_capex) / economic_params.total_capex if economic_params.total_capex > 0 else 0

    return FinancialMetrics(
        lcoe=lcoe,
        npv=npv,
        irr=irr,
        payback_period=payback_simple,
        discounted_payback_period=payback_discounted,
        benefit_cost_ratio=bcr,
        profitability_index=pi,
        annual_production_mwh=annual_production_mwh,
        capacity_factor=capacity_factor,
        currency=economic_params.currency
    )


def compare_scenarios(
    scenarios: Dict[str, Tuple[float, float, EconomicParameters]]
) -> Dict[str, FinancialMetrics]:
    """
    Compare multiple economic scenarios.

    Args:
        scenarios: Dict mapping scenario name to (annual_production_mwh, capacity_mw, economic_params)

    Returns:
        Dict mapping scenario name to FinancialMetrics

    Example:
        >>> scenarios = {
        ...     'Base': (150000, 50, base_params),
        ...     'High Price': (150000, 50, high_price_params),
        ...     'Low Cost': (150000, 50, low_cost_params)
        ... }
        >>> results = compare_scenarios(scenarios)
    """
    results = {}

    for name, (production, capacity, params) in scenarios.items():
        results[name] = calculate_all_metrics(production, capacity, params)

    return results
