"""
Economic parameters for hybrid energy projects.

Dataclasses for cost structures, revenue assumptions, and financial parameters.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class CapexBreakdown:
    """
    Capital expenditure breakdown.

    All costs in the same currency (e.g., USD, EUR).
    """
    turbine_cost: float = 0.0  # Wind turbine equipment cost
    solar_module_cost: float = 0.0  # Solar panel cost
    inverter_cost: float = 0.0  # Inverter cost
    balance_of_system: float = 0.0  # BOS (cables, transformers, etc.)
    civil_works: float = 0.0  # Foundation, roads, site preparation
    grid_connection: float = 0.0  # Grid connection infrastructure
    development_cost: float = 0.0  # Development, permitting, studies
    contingency: float = 0.0  # Contingency reserve
    other: float = 0.0  # Other capital costs

    @property
    def total(self) -> float:
        """Total CAPEX."""
        return (
            self.turbine_cost +
            self.solar_module_cost +
            self.inverter_cost +
            self.balance_of_system +
            self.civil_works +
            self.grid_connection +
            self.development_cost +
            self.contingency +
            self.other
        )


@dataclass(frozen=True)
class OpexBreakdown:
    """
    Operating expenditure breakdown (annual).

    All costs in the same currency per year.
    """
    fixed_om: float = 0.0  # Fixed O&M (staff, administration)
    variable_om: float = 0.0  # Variable O&M (per MWh produced)
    insurance: float = 0.0  # Annual insurance premium
    land_lease: float = 0.0  # Land lease payments
    grid_fees: float = 0.0  # Grid connection fees
    management: float = 0.0  # Management and administration
    reserve_fund: float = 0.0  # Reserve fund contribution
    other: float = 0.0  # Other operating costs

    @property
    def total_fixed(self) -> float:
        """Total fixed OPEX (independent of production)."""
        return (
            self.fixed_om +
            self.insurance +
            self.land_lease +
            self.grid_fees +
            self.management +
            self.reserve_fund +
            self.other
        )

    @property
    def total_variable_per_mwh(self) -> float:
        """Variable OPEX per MWh produced."""
        return self.variable_om


@dataclass(frozen=True)
class RevenueParameters:
    """
    Revenue calculation parameters.
    """
    electricity_price: float  # Base electricity price (currency/MWh)
    price_escalation: float = 0.02  # Annual price escalation rate (2% default)
    curtailment_factor: float = 1.0  # Grid curtailment (1.0 = no curtailment)
    availability: float = 0.97  # Plant availability (97% default)

    # Price profile (optional - if None, uses flat electricity_price)
    price_profile: Optional[Dict[int, float]] = None  # {hour: price_multiplier}

    def __post_init__(self):
        """Validate parameters."""
        if self.electricity_price <= 0:
            raise ValueError("Electricity price must be positive")
        if not 0 <= self.curtailment_factor <= 1:
            raise ValueError("Curtailment factor must be between 0 and 1")
        if not 0 <= self.availability <= 1:
            raise ValueError("Availability must be between 0 and 1")


@dataclass(frozen=True)
class FinancingParameters:
    """
    Project financing parameters.
    """
    project_lifetime: int = 25  # Project lifetime in years
    discount_rate: float = 0.08  # Discount rate (WACC)
    inflation_rate: float = 0.02  # Inflation rate
    tax_rate: float = 0.25  # Corporate tax rate

    # Debt financing (optional)
    debt_ratio: float = 0.0  # Debt to total capital (0 = 100% equity)
    debt_interest_rate: float = 0.0  # Interest rate on debt
    debt_term: int = 0  # Debt repayment period in years

    # Depreciation
    depreciation_period: int = 20  # Depreciation period in years
    depreciation_method: str = 'straight_line'  # 'straight_line' or 'declining_balance'

    def __post_init__(self):
        """Validate parameters."""
        if self.project_lifetime <= 0:
            raise ValueError("Project lifetime must be positive")
        if self.discount_rate < 0:
            raise ValueError("Discount rate cannot be negative")
        if not 0 <= self.debt_ratio <= 1:
            raise ValueError("Debt ratio must be between 0 and 1")
        if not 0 <= self.tax_rate <= 1:
            raise ValueError("Tax rate must be between 0 and 1")
        if self.depreciation_period > self.project_lifetime:
            raise ValueError("Depreciation period cannot exceed project lifetime")


@dataclass(frozen=True)
class EconomicParameters:
    """
    Complete economic parameters for hybrid project analysis.

    Example:
        >>> capex = CapexBreakdown(
        ...     turbine_cost=40_000_000,
        ...     solar_module_cost=10_000_000,
        ...     balance_of_system=5_000_000
        ... )
        >>> opex = OpexBreakdown(
        ...     fixed_om=500_000,
        ...     variable_om=2.0
        ... )
        >>> revenue = RevenueParameters(electricity_price=50.0)
        >>> financing = FinancingParameters(
        ...     project_lifetime=25,
        ...     discount_rate=0.08
        ... )
        >>> params = EconomicParameters(
        ...     capex=capex,
        ...     opex=opex,
        ...     revenue=revenue,
        ...     financing=financing
        ... )
    """
    capex: CapexBreakdown
    opex: OpexBreakdown
    revenue: RevenueParameters
    financing: FinancingParameters

    # Metadata
    currency: str = "USD"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_capex(self) -> float:
        """Total capital expenditure."""
        return self.capex.total

    @property
    def annual_fixed_opex(self) -> float:
        """Annual fixed operating costs."""
        return self.opex.total_fixed

    @property
    def variable_opex_per_mwh(self) -> float:
        """Variable operating cost per MWh."""
        return self.opex.total_variable_per_mwh

    def __repr__(self) -> str:
        return (
            f"EconomicParameters("
            f"CAPEX={self.total_capex/1e6:.1f}M {self.currency}, "
            f"Fixed OPEX={self.annual_fixed_opex/1e3:.0f}k {self.currency}/yr, "
            f"Price={self.revenue.electricity_price} {self.currency}/MWh)"
        )


# Convenience functions for common parameter sets

def create_wind_economics(
    capacity_mw: float,
    capex_per_kw: float = 1400,
    fixed_opex_per_kw_year: float = 35,
    electricity_price: float = 50.0,
    project_lifetime: int = 25,
    discount_rate: float = 0.08,
    **kwargs
) -> EconomicParameters:
    """
    Create economic parameters for wind project using typical ratios.

    Args:
        capacity_mw: Installed wind capacity in MW
        capex_per_kw: Capital cost per kW (default $1400/kW)
        fixed_opex_per_kw_year: Fixed O&M per kW per year (default $35/kW/yr)
        electricity_price: Electricity price in currency/MWh
        project_lifetime: Project lifetime in years
        discount_rate: Discount rate (WACC)
        **kwargs: Additional parameters for customization

    Returns:
        EconomicParameters instance
    """
    total_capacity_kw = capacity_mw * 1000
    total_capex = total_capacity_kw * capex_per_kw

    # Typical breakdown (can be overridden via kwargs)
    capex = CapexBreakdown(
        turbine_cost=total_capex * 0.70,
        balance_of_system=total_capex * 0.15,
        civil_works=total_capex * 0.08,
        grid_connection=total_capex * 0.05,
        contingency=total_capex * 0.02
    )

    annual_fixed_opex = total_capacity_kw * fixed_opex_per_kw_year

    opex = OpexBreakdown(
        fixed_om=annual_fixed_opex * 0.70,
        insurance=annual_fixed_opex * 0.15,
        land_lease=annual_fixed_opex * 0.10,
        management=annual_fixed_opex * 0.05
    )

    revenue = RevenueParameters(electricity_price=electricity_price)

    financing = FinancingParameters(
        project_lifetime=project_lifetime,
        discount_rate=discount_rate
    )

    return EconomicParameters(
        capex=capex,
        opex=opex,
        revenue=revenue,
        financing=financing,
        **kwargs
    )


def create_solar_economics(
    capacity_mw: float,
    capex_per_kw: float = 900,
    fixed_opex_per_kw_year: float = 15,
    electricity_price: float = 50.0,
    project_lifetime: int = 25,
    discount_rate: float = 0.08,
    **kwargs
) -> EconomicParameters:
    """
    Create economic parameters for solar project using typical ratios.

    Args:
        capacity_mw: Installed solar capacity in MW
        capex_per_kw: Capital cost per kW (default $900/kW)
        fixed_opex_per_kw_year: Fixed O&M per kW per year (default $15/kW/yr)
        electricity_price: Electricity price in currency/MWh
        project_lifetime: Project lifetime in years
        discount_rate: Discount rate (WACC)
        **kwargs: Additional parameters for customization

    Returns:
        EconomicParameters instance
    """
    total_capacity_kw = capacity_mw * 1000
    total_capex = total_capacity_kw * capex_per_kw

    # Typical breakdown
    capex = CapexBreakdown(
        solar_module_cost=total_capex * 0.40,
        inverter_cost=total_capex * 0.10,
        balance_of_system=total_capex * 0.30,
        civil_works=total_capex * 0.10,
        grid_connection=total_capex * 0.08,
        contingency=total_capex * 0.02
    )

    annual_fixed_opex = total_capacity_kw * fixed_opex_per_kw_year

    opex = OpexBreakdown(
        fixed_om=annual_fixed_opex * 0.60,
        insurance=annual_fixed_opex * 0.20,
        land_lease=annual_fixed_opex * 0.15,
        management=annual_fixed_opex * 0.05
    )

    revenue = RevenueParameters(electricity_price=electricity_price)

    financing = FinancingParameters(
        project_lifetime=project_lifetime,
        discount_rate=discount_rate
    )

    return EconomicParameters(
        capex=capex,
        opex=opex,
        revenue=revenue,
        financing=financing,
        **kwargs
    )


def create_hybrid_economics(
    wind_capacity_mw: float,
    solar_capacity_mw: float,
    wind_capex_per_kw: float = 1400,
    solar_capex_per_kw: float = 900,
    wind_opex_per_kw_year: float = 35,
    solar_opex_per_kw_year: float = 15,
    electricity_price: float = 50.0,
    project_lifetime: int = 25,
    discount_rate: float = 0.08,
    **kwargs
) -> EconomicParameters:
    """
    Create economic parameters for hybrid wind+solar project.

    Args:
        wind_capacity_mw: Installed wind capacity in MW
        solar_capacity_mw: Installed solar capacity in MW
        wind_capex_per_kw: Wind capital cost per kW
        solar_capex_per_kw: Solar capital cost per kW
        wind_opex_per_kw_year: Wind O&M per kW per year
        solar_opex_per_kw_year: Solar O&M per kW per year
        electricity_price: Electricity price in currency/MWh
        project_lifetime: Project lifetime in years
        discount_rate: Discount rate (WACC)
        **kwargs: Additional parameters

    Returns:
        EconomicParameters instance
    """
    wind_kw = wind_capacity_mw * 1000
    solar_kw = solar_capacity_mw * 1000

    wind_capex = wind_kw * wind_capex_per_kw
    solar_capex = solar_kw * solar_capex_per_kw

    # Combined CAPEX with shared infrastructure savings
    shared_savings = 0.05  # 5% savings on shared infrastructure

    capex = CapexBreakdown(
        turbine_cost=wind_capex * 0.70,
        solar_module_cost=solar_capex * 0.40,
        inverter_cost=solar_capex * 0.10,
        balance_of_system=(wind_capex * 0.15 + solar_capex * 0.30) * (1 - shared_savings),
        civil_works=(wind_capex * 0.08 + solar_capex * 0.10) * (1 - shared_savings),
        grid_connection=(wind_capex * 0.05 + solar_capex * 0.08) * (1 - shared_savings),
        contingency=(wind_capex + solar_capex) * 0.02
    )

    wind_opex = wind_kw * wind_opex_per_kw_year
    solar_opex = solar_kw * solar_opex_per_kw_year
    total_opex = wind_opex + solar_opex

    opex = OpexBreakdown(
        fixed_om=total_opex * 0.65,
        insurance=total_opex * 0.18,
        land_lease=total_opex * 0.12,
        management=total_opex * 0.05
    )

    revenue = RevenueParameters(electricity_price=electricity_price)

    financing = FinancingParameters(
        project_lifetime=project_lifetime,
        discount_rate=discount_rate
    )

    return EconomicParameters(
        capex=capex,
        opex=opex,
        revenue=revenue,
        financing=financing,
        **kwargs
    )
