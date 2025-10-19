"""
Revenue calculation from electricity sales.

Handles price profiles, curtailment, and availability factors.
"""

from typing import Optional, Dict
import pandas as pd
import numpy as np

from .parameters import RevenueParameters


def calculate_revenue_timeseries(
    power_timeseries: pd.DataFrame,
    revenue_params: RevenueParameters,
    power_column: str = 'power_kw'
) -> pd.DataFrame:
    """
    Calculate revenue timeseries from power production.

    Args:
        power_timeseries: DataFrame with power production (kW)
        revenue_params: Revenue parameters
        power_column: Name of power column in DataFrame

    Returns:
        DataFrame with power, price, and revenue columns

    Example:
        >>> power_ts = pd.DataFrame({
        ...     'power_kw': [1000, 2000, 1500],
        ... }, index=pd.date_range('2024-01-01', periods=3, freq='H'))
        >>> revenue_params = RevenueParameters(electricity_price=50.0)
        >>> revenue_ts = calculate_revenue_timeseries(power_ts, revenue_params)
    """
    if power_column not in power_timeseries.columns:
        raise ValueError(f"Column '{power_column}' not found in power_timeseries")

    result = power_timeseries.copy()

    # Get power in MW
    power_mw = result[power_column] / 1000

    # Apply curtailment and availability
    power_mw_adjusted = (
        power_mw *
        revenue_params.curtailment_factor *
        revenue_params.availability
    )

    # Get hourly prices
    if revenue_params.price_profile is not None:
        # Use hour-specific pricing
        hours = result.index.hour
        price_multipliers = np.array([
            revenue_params.price_profile.get(h, 1.0) for h in hours
        ])
        hourly_prices = revenue_params.electricity_price * price_multipliers
    else:
        # Flat pricing
        hourly_prices = revenue_params.electricity_price

    # Calculate revenue (MWh * price/MWh = revenue)
    result['power_mw_adjusted'] = power_mw_adjusted
    result['price_per_mwh'] = hourly_prices
    result['revenue'] = power_mw_adjusted * hourly_prices

    return result


def calculate_annual_revenue(
    annual_production_mwh: float,
    revenue_params: RevenueParameters,
    year_number: int = 1
) -> float:
    """
    Calculate annual revenue with price escalation.

    Args:
        annual_production_mwh: Annual energy production in MWh
        revenue_params: Revenue parameters
        year_number: Year number (1 = first year, for escalation)

    Returns:
        Annual revenue in currency

    Example:
        >>> revenue_params = RevenueParameters(
        ...     electricity_price=50.0,
        ...     price_escalation=0.02
        ... )
        >>> revenue_year_1 = calculate_annual_revenue(150000, revenue_params, year_number=1)
        >>> revenue_year_10 = calculate_annual_revenue(150000, revenue_params, year_number=10)
    """
    # Apply price escalation
    escalated_price = (
        revenue_params.electricity_price *
        (1 + revenue_params.price_escalation) ** (year_number - 1)
    )

    # Apply curtailment and availability
    adjusted_production = (
        annual_production_mwh *
        revenue_params.curtailment_factor *
        revenue_params.availability
    )

    revenue = adjusted_production * escalated_price

    return revenue


def calculate_revenue_profile(
    annual_production_mwh: float,
    revenue_params: RevenueParameters,
    project_lifetime: int = 25
) -> np.ndarray:
    """
    Calculate revenue for each year of project lifetime.

    Args:
        annual_production_mwh: Annual energy production in MWh
        revenue_params: Revenue parameters
        project_lifetime: Project lifetime in years

    Returns:
        Array of annual revenues (length = project_lifetime)

    Example:
        >>> revenue_params = RevenueParameters(
        ...     electricity_price=50.0,
        ...     price_escalation=0.02
        ... )
        >>> revenue_profile = calculate_revenue_profile(150000, revenue_params, 25)
    """
    revenues = np.zeros(project_lifetime)

    for year in range(project_lifetime):
        revenues[year] = calculate_annual_revenue(
            annual_production_mwh,
            revenue_params,
            year_number=year + 1
        )

    return revenues


def create_price_profile_tod(
    on_peak_multiplier: float = 1.5,
    off_peak_multiplier: float = 0.7,
    peak_hours: tuple = (8, 22)
) -> Dict[int, float]:
    """
    Create time-of-day price profile.

    Args:
        on_peak_multiplier: Price multiplier for peak hours
        off_peak_multiplier: Price multiplier for off-peak hours
        peak_hours: Tuple of (start_hour, end_hour) for peak period

    Returns:
        Dict mapping hour (0-23) to price multiplier

    Example:
        >>> price_profile = create_price_profile_tod(
        ...     on_peak_multiplier=1.8,
        ...     off_peak_multiplier=0.6,
        ...     peak_hours=(9, 21)
        ... )
    """
    profile = {}

    for hour in range(24):
        if peak_hours[0] <= hour < peak_hours[1]:
            profile[hour] = on_peak_multiplier
        else:
            profile[hour] = off_peak_multiplier

    return profile


def create_price_profile_seasonal(
    summer_multiplier: float = 1.3,
    winter_multiplier: float = 1.1,
    shoulder_multiplier: float = 0.9,
    summer_months: tuple = (6, 7, 8),
    winter_months: tuple = (12, 1, 2)
) -> Dict[int, float]:
    """
    Create seasonal price profile.

    Note: This returns monthly multipliers, not hourly.
    For hourly timeseries, map month to multiplier.

    Args:
        summer_multiplier: Price multiplier for summer months
        winter_multiplier: Price multiplier for winter months
        shoulder_multiplier: Price multiplier for shoulder months
        summer_months: Tuple of summer month numbers
        winter_months: Tuple of winter month numbers

    Returns:
        Dict mapping month (1-12) to price multiplier

    Example:
        >>> price_profile = create_price_profile_seasonal(
        ...     summer_multiplier=1.5,
        ...     winter_multiplier=1.2
        ... )
    """
    profile = {}

    for month in range(1, 13):
        if month in summer_months:
            profile[month] = summer_multiplier
        elif month in winter_months:
            profile[month] = winter_multiplier
        else:
            profile[month] = shoulder_multiplier

    return profile


def apply_price_profile_to_timeseries(
    power_timeseries: pd.DataFrame,
    base_price: float,
    price_profile: Dict[int, float],
    profile_type: str = 'hourly'
) -> pd.DataFrame:
    """
    Apply price profile to power timeseries.

    Args:
        power_timeseries: DataFrame with datetime index
        base_price: Base electricity price (currency/MWh)
        price_profile: Dict mapping time period to multiplier
        profile_type: 'hourly' or 'monthly'

    Returns:
        DataFrame with added 'price_per_mwh' column

    Example:
        >>> power_ts = pd.DataFrame({
        ...     'power_kw': [1000, 2000],
        ... }, index=pd.date_range('2024-01-01', periods=2, freq='H'))
        >>> price_profile = create_price_profile_tod()
        >>> ts_with_prices = apply_price_profile_to_timeseries(
        ...     power_ts, base_price=50.0, price_profile=price_profile
        ... )
    """
    result = power_timeseries.copy()

    if profile_type == 'hourly':
        # Map hour to price
        hours = result.index.hour
        multipliers = np.array([price_profile.get(h, 1.0) for h in hours])

    elif profile_type == 'monthly':
        # Map month to price
        months = result.index.month
        multipliers = np.array([price_profile.get(m, 1.0) for m in months])

    else:
        raise ValueError(f"Unknown profile_type: {profile_type}. Use 'hourly' or 'monthly'")

    result['price_per_mwh'] = base_price * multipliers

    return result


def calculate_merchant_revenue(
    power_timeseries: pd.DataFrame,
    spot_prices: pd.Series,
    power_column: str = 'power_kw',
    curtailment_factor: float = 1.0,
    availability: float = 0.97
) -> pd.DataFrame:
    """
    Calculate revenue using merchant (spot) prices.

    Args:
        power_timeseries: DataFrame with power production (kW)
        spot_prices: Series with spot prices (currency/MWh), aligned with power_timeseries
        power_column: Name of power column
        curtailment_factor: Grid curtailment factor (0-1)
        availability: Plant availability (0-1)

    Returns:
        DataFrame with power, spot prices, and revenue

    Example:
        >>> power_ts = pd.DataFrame({
        ...     'power_kw': [1000, 2000, 1500],
        ... }, index=pd.date_range('2024-01-01', periods=3, freq='H'))
        >>> spot_prices = pd.Series(
        ...     [45.0, 60.0, 50.0],
        ...     index=power_ts.index
        ... )
        >>> revenue_ts = calculate_merchant_revenue(power_ts, spot_prices)
    """
    if power_column not in power_timeseries.columns:
        raise ValueError(f"Column '{power_column}' not found in power_timeseries")

    # Align spot prices with power timeseries
    if not power_timeseries.index.equals(spot_prices.index):
        spot_prices = spot_prices.reindex(power_timeseries.index)

    result = power_timeseries.copy()

    # Get power in MW
    power_mw = result[power_column] / 1000

    # Apply curtailment and availability
    power_mw_adjusted = power_mw * curtailment_factor * availability

    result['power_mw_adjusted'] = power_mw_adjusted
    result['spot_price_per_mwh'] = spot_prices
    result['revenue'] = power_mw_adjusted * spot_prices

    return result
