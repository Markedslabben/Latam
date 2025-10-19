"""
Sensitivity analysis for hybrid energy project economics.

Tornado diagrams, scenario analysis, and Monte Carlo simulations.
"""

from typing import Dict, List, Tuple, Callable, Optional
import numpy as np
from dataclasses import dataclass, field

from .parameters import EconomicParameters
from .metrics import calculate_all_metrics, FinancialMetrics


@dataclass
class SensitivityResult:
    """
    Result of sensitivity analysis for one parameter.
    """
    parameter_name: str
    base_value: float
    low_value: float
    high_value: float
    base_metric: float
    low_metric: float
    high_metric: float
    impact_range: float  # high_metric - low_metric

    @property
    def relative_impact(self) -> float:
        """Relative impact as percentage of base metric."""
        if self.base_metric == 0:
            return 0
        return abs(self.impact_range / self.base_metric)


def sensitivity_analysis(
    annual_production_mwh: float,
    installed_capacity_mw: float,
    base_economic_params: EconomicParameters,
    parameter_variations: Dict[str, Tuple[float, float]],
    metric: str = 'npv'
) -> List[SensitivityResult]:
    """
    Perform sensitivity analysis on economic parameters.

    Args:
        annual_production_mwh: Annual energy production in MWh
        installed_capacity_mw: Installed capacity in MW
        base_economic_params: Base case economic parameters
        parameter_variations: Dict mapping parameter name to (low_multiplier, high_multiplier)
        metric: Which metric to analyze ('npv', 'irr', 'lcoe', 'payback_period')

    Returns:
        List of SensitivityResult sorted by impact magnitude

    Example:
        >>> params = create_wind_economics(capacity_mw=50, electricity_price=55)
        >>> variations = {
        ...     'electricity_price': (0.8, 1.2),  # ±20%
        ...     'capex': (0.9, 1.1),  # ±10%
        ...     'discount_rate': (0.9, 1.1)  # ±10%
        ... }
        >>> results = sensitivity_analysis(
        ...     annual_production_mwh=150000,
        ...     installed_capacity_mw=50,
        ...     base_economic_params=params,
        ...     parameter_variations=variations,
        ...     metric='npv'
        ... )
    """
    results = []

    # Calculate base case
    base_metrics = calculate_all_metrics(
        annual_production_mwh,
        installed_capacity_mw,
        base_economic_params
    )
    base_metric_value = getattr(base_metrics, metric)

    for param_name, (low_mult, high_mult) in parameter_variations.items():
        # Get base parameter value
        base_value = _get_parameter_value(base_economic_params, param_name)

        # Calculate low case
        low_params = _modify_parameter(base_economic_params, param_name, base_value * low_mult)
        low_metrics = calculate_all_metrics(
            annual_production_mwh,
            installed_capacity_mw,
            low_params
        )
        low_metric_value = getattr(low_metrics, metric)

        # Calculate high case
        high_params = _modify_parameter(base_economic_params, param_name, base_value * high_mult)
        high_metrics = calculate_all_metrics(
            annual_production_mwh,
            installed_capacity_mw,
            high_params
        )
        high_metric_value = getattr(high_metrics, metric)

        result = SensitivityResult(
            parameter_name=param_name,
            base_value=base_value,
            low_value=base_value * low_mult,
            high_value=base_value * high_mult,
            base_metric=base_metric_value,
            low_metric=low_metric_value,
            high_metric=high_metric_value,
            impact_range=high_metric_value - low_metric_value
        )

        results.append(result)

    # Sort by impact magnitude (descending)
    results.sort(key=lambda r: abs(r.impact_range), reverse=True)

    return results


def _get_parameter_value(params: EconomicParameters, param_name: str) -> float:
    """Get parameter value by name."""
    if param_name == 'electricity_price':
        return params.revenue.electricity_price
    elif param_name == 'capex':
        return params.total_capex
    elif param_name == 'fixed_opex':
        return params.annual_fixed_opex
    elif param_name == 'discount_rate':
        return params.financing.discount_rate
    elif param_name == 'curtailment_factor':
        return params.revenue.curtailment_factor
    elif param_name == 'availability':
        return params.revenue.availability
    else:
        raise ValueError(f"Unknown parameter: {param_name}")


def _modify_parameter(params: EconomicParameters, param_name: str, new_value: float) -> EconomicParameters:
    """Create new EconomicParameters with modified parameter."""
    from dataclasses import replace

    if param_name == 'electricity_price':
        new_revenue = replace(params.revenue, electricity_price=new_value)
        return replace(params, revenue=new_revenue)

    elif param_name == 'capex':
        # Scale all CAPEX components proportionally
        scale_factor = new_value / params.total_capex
        new_capex = replace(
            params.capex,
            turbine_cost=params.capex.turbine_cost * scale_factor,
            solar_module_cost=params.capex.solar_module_cost * scale_factor,
            inverter_cost=params.capex.inverter_cost * scale_factor,
            balance_of_system=params.capex.balance_of_system * scale_factor,
            civil_works=params.capex.civil_works * scale_factor,
            grid_connection=params.capex.grid_connection * scale_factor,
            development_cost=params.capex.development_cost * scale_factor,
            contingency=params.capex.contingency * scale_factor,
            other=params.capex.other * scale_factor
        )
        return replace(params, capex=new_capex)

    elif param_name == 'fixed_opex':
        # Scale all fixed OPEX components proportionally
        scale_factor = new_value / params.annual_fixed_opex
        new_opex = replace(
            params.opex,
            fixed_om=params.opex.fixed_om * scale_factor,
            insurance=params.opex.insurance * scale_factor,
            land_lease=params.opex.land_lease * scale_factor,
            grid_fees=params.opex.grid_fees * scale_factor,
            management=params.opex.management * scale_factor,
            reserve_fund=params.opex.reserve_fund * scale_factor,
            other=params.opex.other * scale_factor
        )
        return replace(params, opex=new_opex)

    elif param_name == 'discount_rate':
        new_financing = replace(params.financing, discount_rate=new_value)
        return replace(params, financing=new_financing)

    elif param_name == 'curtailment_factor':
        new_revenue = replace(params.revenue, curtailment_factor=new_value)
        return replace(params, revenue=new_revenue)

    elif param_name == 'availability':
        new_revenue = replace(params.revenue, availability=new_value)
        return replace(params, revenue=new_revenue)

    else:
        raise ValueError(f"Unknown parameter: {param_name}")


@dataclass
class ScenarioComparison:
    """
    Comparison of multiple scenarios.
    """
    scenarios: Dict[str, FinancialMetrics]
    best_scenario: str
    worst_scenario: str
    metric_used: str = 'npv'

    def get_ranking(self) -> List[Tuple[str, float]]:
        """Get scenarios ranked by metric."""
        if self.metric_used == 'lcoe':
            # Lower is better for LCOE
            ranked = sorted(
                [(name, getattr(metrics, self.metric_used))
                 for name, metrics in self.scenarios.items()],
                key=lambda x: x[1]
            )
        else:
            # Higher is better for NPV, IRR, etc.
            ranked = sorted(
                [(name, getattr(metrics, self.metric_used))
                 for name, metrics in self.scenarios.items()],
                key=lambda x: x[1] if x[1] is not None else -np.inf,
                reverse=True
            )
        return ranked


def compare_scenarios(
    scenarios: Dict[str, Tuple[float, float, EconomicParameters]],
    metric: str = 'npv'
) -> ScenarioComparison:
    """
    Compare multiple economic scenarios.

    Args:
        scenarios: Dict mapping scenario name to (annual_production_mwh, capacity_mw, economic_params)
        metric: Metric for comparison ('npv', 'irr', 'lcoe')

    Returns:
        ScenarioComparison with rankings

    Example:
        >>> scenarios = {
        ...     'Base': (150000, 50, base_params),
        ...     'High Price': (150000, 50, high_price_params),
        ...     'Low Cost': (150000, 50, low_cost_params)
        ... }
        >>> comparison = compare_scenarios(scenarios, metric='npv')
        >>> print(f"Best scenario: {comparison.best_scenario}")
    """
    scenario_metrics = {}

    for name, (production, capacity, params) in scenarios.items():
        scenario_metrics[name] = calculate_all_metrics(production, capacity, params)

    # Determine best/worst
    ranking = []
    for name, metrics in scenario_metrics.items():
        metric_value = getattr(metrics, metric)
        if metric_value is not None:
            ranking.append((name, metric_value))

    if metric == 'lcoe':
        # Lower is better
        ranking.sort(key=lambda x: x[1])
    else:
        # Higher is better
        ranking.sort(key=lambda x: x[1], reverse=True)

    best_scenario = ranking[0][0] if ranking else None
    worst_scenario = ranking[-1][0] if ranking else None

    return ScenarioComparison(
        scenarios=scenario_metrics,
        best_scenario=best_scenario,
        worst_scenario=worst_scenario,
        metric_used=metric
    )


@dataclass
class MonteCarloResult:
    """
    Result of Monte Carlo simulation.
    """
    metric_name: str
    simulations: np.ndarray
    mean: float
    median: float
    std: float
    percentile_5: float
    percentile_95: float
    confidence_interval_90: Tuple[float, float]

    @property
    def probability_positive(self) -> float:
        """Probability that metric is positive (for NPV, IRR)."""
        return (self.simulations > 0).mean()


def monte_carlo_simulation(
    annual_production_mwh: float,
    installed_capacity_mw: float,
    base_economic_params: EconomicParameters,
    parameter_distributions: Dict[str, Callable[[], float]],
    n_simulations: int = 1000,
    metric: str = 'npv',
    random_seed: Optional[int] = None
) -> MonteCarloResult:
    """
    Perform Monte Carlo simulation for economic uncertainty analysis.

    Args:
        annual_production_mwh: Annual energy production in MWh
        installed_capacity_mw: Installed capacity in MW
        base_economic_params: Base case economic parameters
        parameter_distributions: Dict mapping parameter name to sampling function
        n_simulations: Number of simulations to run
        metric: Which metric to analyze ('npv', 'irr', 'lcoe')
        random_seed: Random seed for reproducibility

    Returns:
        MonteCarloResult with statistics

    Example:
        >>> import numpy as np
        >>> params = create_wind_economics(capacity_mw=50)
        >>> distributions = {
        ...     'electricity_price': lambda: np.random.normal(55, 5),
        ...     'capex': lambda: np.random.normal(70e6, 5e6),
        ...     'availability': lambda: np.random.uniform(0.94, 0.98)
        ... }
        >>> mc_result = monte_carlo_simulation(
        ...     annual_production_mwh=150000,
        ...     installed_capacity_mw=50,
        ...     base_economic_params=params,
        ...     parameter_distributions=distributions,
        ...     n_simulations=1000
        ... )
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    results = np.zeros(n_simulations)

    for i in range(n_simulations):
        # Sample parameters
        params = base_economic_params

        for param_name, sample_fn in parameter_distributions.items():
            sampled_value = sample_fn()
            params = _modify_parameter(params, param_name, sampled_value)

        # Calculate metrics
        metrics = calculate_all_metrics(
            annual_production_mwh,
            installed_capacity_mw,
            params
        )

        metric_value = getattr(metrics, metric)
        results[i] = metric_value if metric_value is not None else np.nan

    # Remove NaN values
    results = results[~np.isnan(results)]

    # Calculate statistics
    mean = np.mean(results)
    median = np.median(results)
    std = np.std(results)
    p5 = np.percentile(results, 5)
    p95 = np.percentile(results, 95)

    return MonteCarloResult(
        metric_name=metric,
        simulations=results,
        mean=mean,
        median=median,
        std=std,
        percentile_5=p5,
        percentile_95=p95,
        confidence_interval_90=(p5, p95)
    )
