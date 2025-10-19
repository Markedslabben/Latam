"""
Result aggregation for hybrid energy analysis.

Combines wind, solar, and economic results into structured containers.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from ..core import WindSimulationResult, SolarProductionResult
from ..economics import FinancialMetrics


@dataclass
class HybridProductionResult:
    """
    Combined production results for hybrid wind+solar project.

    Aggregates wind and solar production with combined timeseries and metrics.
    """
    wind_result: Optional[WindSimulationResult] = None
    solar_result: Optional[SolarProductionResult] = None

    # Combined metrics
    total_aep_gwh: float = 0.0
    combined_capacity_factor: float = 0.0

    # Optional combined timeseries
    combined_timeseries: Optional[pd.DataFrame] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate combined metrics from wind and solar results."""
        if self.wind_result is None and self.solar_result is None:
            raise ValueError("At least one of wind_result or solar_result must be provided")

        # Calculate total AEP
        wind_aep = self.wind_result.aep_gwh if self.wind_result else 0.0
        solar_aep = self.solar_result.aep_gwh if self.solar_result else 0.0
        self.total_aep_gwh = wind_aep + solar_aep

        # Calculate combined capacity factor if capacity info available
        if self.metadata.get('installed_capacity_mw'):
            total_capacity_mw = self.metadata['installed_capacity_mw']
            hours_per_year = 8760
            max_annual_mwh = total_capacity_mw * hours_per_year
            self.combined_capacity_factor = (self.total_aep_gwh * 1000) / max_annual_mwh

    @property
    def wind_capacity_factor(self) -> Optional[float]:
        """Wind capacity factor."""
        return self.wind_result.capacity_factor if self.wind_result else None

    @property
    def solar_capacity_factor(self) -> Optional[float]:
        """Solar capacity factor."""
        return self.solar_result.capacity_factor if self.solar_result else None

    @property
    def wind_aep_gwh(self) -> float:
        """Wind annual energy production in GWh."""
        return self.wind_result.aep_gwh if self.wind_result else 0.0

    @property
    def solar_aep_gwh(self) -> float:
        """Solar annual energy production in GWh."""
        return self.solar_result.aep_gwh if self.solar_result else 0.0

    @property
    def wind_contribution(self) -> float:
        """Wind contribution as fraction of total (0-1)."""
        if self.total_aep_gwh == 0:
            return 0.0
        return self.wind_aep_gwh / self.total_aep_gwh

    @property
    def solar_contribution(self) -> float:
        """Solar contribution as fraction of total (0-1)."""
        if self.total_aep_gwh == 0:
            return 0.0
        return self.solar_aep_gwh / self.total_aep_gwh

    def get_summary(self) -> Dict[str, Any]:
        """Get summary dictionary."""
        summary = {
            'total_aep_gwh': self.total_aep_gwh,
            'combined_capacity_factor': self.combined_capacity_factor,
            'wind_contribution': self.wind_contribution,
            'solar_contribution': self.solar_contribution
        }

        if self.wind_result:
            summary['wind'] = {
                'aep_gwh': self.wind_aep_gwh,
                'capacity_factor': self.wind_capacity_factor,
                'wake_losses': self.wind_result.wake_losses
            }

        if self.solar_result:
            summary['solar'] = {
                'aep_gwh': self.solar_aep_gwh,
                'capacity_factor': self.solar_capacity_factor,
                'shading_losses': self.solar_result.shading_losses
            }

        return summary


@dataclass
class HybridProjectResult:
    """
    Complete hybrid project analysis results.

    Combines production and economic results with project metadata.
    """
    # Production results
    production: HybridProductionResult

    # Economic results
    economics: FinancialMetrics

    # Project information
    project_name: str = "Hybrid Project"
    location: Optional[str] = None
    installed_capacity_mw: Optional[float] = None
    wind_capacity_mw: Optional[float] = None
    solar_capacity_mw: Optional[float] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def capacity_mix(self) -> Dict[str, float]:
        """Capacity mix percentages."""
        if not self.installed_capacity_mw or self.installed_capacity_mw == 0:
            return {'wind': 0.0, 'solar': 0.0}

        wind_pct = (self.wind_capacity_mw or 0) / self.installed_capacity_mw
        solar_pct = (self.solar_capacity_mw or 0) / self.installed_capacity_mw

        return {'wind': wind_pct, 'solar': solar_pct}

    @property
    def energy_mix(self) -> Dict[str, float]:
        """Energy production mix percentages."""
        return {
            'wind': self.production.wind_contribution,
            'solar': self.production.solar_contribution
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive project summary."""
        summary = {
            'project': {
                'name': self.project_name,
                'location': self.location,
                'installed_capacity_mw': self.installed_capacity_mw,
                'wind_capacity_mw': self.wind_capacity_mw,
                'solar_capacity_mw': self.solar_capacity_mw,
                'capacity_mix': self.capacity_mix,
                'energy_mix': self.energy_mix
            },
            'production': self.production.get_summary(),
            'economics': {
                'lcoe': self.economics.lcoe,
                'npv': self.economics.npv,
                'irr': self.economics.irr,
                'payback_period': self.economics.payback_period,
                'capacity_factor': self.economics.capacity_factor,
                'currency': self.economics.currency
            }
        }

        return summary

    def __repr__(self) -> str:
        return (
            f"HybridProjectResult(\n"
            f"  Project: {self.project_name}\n"
            f"  Capacity: {self.installed_capacity_mw}MW "
            f"({self.capacity_mix['wind']:.0%} wind, {self.capacity_mix['solar']:.0%} solar)\n"
            f"  AEP: {self.production.total_aep_gwh:.1f} GWh\n"
            f"  LCOE: {self.economics.lcoe:.2f} {self.economics.currency}/MWh\n"
            f"  NPV: {self.economics.npv/1e6:.1f}M {self.economics.currency}\n"
            f"  IRR: {self.economics.irr:.1%}" if self.economics.irr else "  IRR: N/A\n"
            f")"
        )


def combine_production_timeseries(
    wind_timeseries: Optional[pd.DataFrame] = None,
    solar_timeseries: Optional[pd.DataFrame] = None,
    wind_power_column: str = 'power_kw',
    solar_power_column: str = 'power_kw'
) -> pd.DataFrame:
    """
    Combine wind and solar production timeseries.

    Args:
        wind_timeseries: Wind production DataFrame
        solar_timeseries: Solar production DataFrame
        wind_power_column: Name of wind power column
        solar_power_column: Name of solar power column

    Returns:
        Combined DataFrame with wind, solar, and total power

    Example:
        >>> combined = combine_production_timeseries(
        ...     wind_timeseries=wind_result.power_timeseries,
        ...     solar_timeseries=solar_result.power_timeseries
        ... )
    """
    if wind_timeseries is None and solar_timeseries is None:
        raise ValueError("At least one timeseries must be provided")

    # Determine index (use wind if available, else solar)
    if wind_timeseries is not None:
        index = wind_timeseries.index
    else:
        index = solar_timeseries.index

    # Initialize result
    result = pd.DataFrame(index=index)

    # Add wind power
    if wind_timeseries is not None:
        if wind_power_column in wind_timeseries.columns:
            result['wind_power_kw'] = wind_timeseries[wind_power_column]
        else:
            result['wind_power_kw'] = 0.0
    else:
        result['wind_power_kw'] = 0.0

    # Add solar power
    if solar_timeseries is not None:
        if solar_power_column in solar_timeseries.columns:
            # Align solar timeseries with result index
            solar_aligned = solar_timeseries[solar_power_column].reindex(index, fill_value=0.0)
            result['solar_power_kw'] = solar_aligned
        else:
            result['solar_power_kw'] = 0.0
    else:
        result['solar_power_kw'] = 0.0

    # Calculate total
    result['total_power_kw'] = result['wind_power_kw'] + result['solar_power_kw']

    # Calculate contributions
    total_nonzero = result['total_power_kw'].replace(0, np.nan)
    result['wind_contribution'] = result['wind_power_kw'] / total_nonzero
    result['solar_contribution'] = result['solar_power_kw'] / total_nonzero
    result[['wind_contribution', 'solar_contribution']] = result[['wind_contribution', 'solar_contribution']].fillna(0)

    return result


def create_hybrid_result(
    wind_result: Optional[WindSimulationResult] = None,
    solar_result: Optional[SolarProductionResult] = None,
    economic_metrics: Optional[FinancialMetrics] = None,
    project_name: str = "Hybrid Project",
    wind_capacity_mw: Optional[float] = None,
    solar_capacity_mw: Optional[float] = None,
    **kwargs
) -> HybridProjectResult:
    """
    Create complete hybrid project result from components.

    Args:
        wind_result: Wind production result
        solar_result: Solar production result
        economic_metrics: Financial metrics
        project_name: Project name
        wind_capacity_mw: Wind installed capacity
        solar_capacity_mw: Solar installed capacity
        **kwargs: Additional metadata

    Returns:
        HybridProjectResult

    Example:
        >>> result = create_hybrid_result(
        ...     wind_result=wind_production,
        ...     solar_result=solar_production,
        ...     economic_metrics=financial_metrics,
        ...     project_name="Chile Hybrid 1",
        ...     wind_capacity_mw=50,
        ...     solar_capacity_mw=10
        ... )
    """
    # Calculate total capacity
    total_capacity_mw = (wind_capacity_mw or 0) + (solar_capacity_mw or 0)

    # Create production result
    production = HybridProductionResult(
        wind_result=wind_result,
        solar_result=solar_result,
        metadata={
            'installed_capacity_mw': total_capacity_mw,
            **kwargs
        }
    )

    # Combine timeseries if both available
    if wind_result and solar_result and wind_result.power_timeseries is not None and solar_result.power_timeseries is not None:
        production.combined_timeseries = combine_production_timeseries(
            wind_result.power_timeseries,
            solar_result.power_timeseries
        )

    # Create project result
    if economic_metrics is None:
        raise ValueError("Economic metrics required for project result")

    project_result = HybridProjectResult(
        production=production,
        economics=economic_metrics,
        project_name=project_name,
        installed_capacity_mw=total_capacity_mw,
        wind_capacity_mw=wind_capacity_mw,
        solar_capacity_mw=solar_capacity_mw,
        metadata=kwargs
    )

    return project_result
