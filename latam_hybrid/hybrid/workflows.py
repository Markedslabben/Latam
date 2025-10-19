"""
Common workflow patterns for hybrid energy analysis.

Provides pre-built workflows and convenience functions for typical analysis scenarios.
"""

from typing import Optional, Dict, Any, Union
from pathlib import Path
import pandas as pd

from .analysis import HybridAnalysis
from ..wind import TurbineModel, TurbineLayout, WindSite
from ..solar import SolarSite, SolarSystem
from ..economics import (
    EconomicParameters,
    create_wind_economics,
    create_solar_economics,
    create_hybrid_economics,
)
from ..output import HybridProjectResult


def analyze_wind_solar_hybrid(
    project_name: str,
    turbine: TurbineModel,
    turbine_layout: TurbineLayout,
    wind_site: WindSite,
    solar_system: SolarSystem,
    solar_site: SolarSite,
    economic_params: EconomicParameters,
    location: Optional[str] = None,
    wake_model: str = "NOJ",
    output_dir: Optional[Path] = None,
    export_formats: list = ['json', 'excel', 'markdown']
) -> HybridProjectResult:
    """
    Complete wind+solar hybrid analysis workflow.

    Runs full analysis pipeline: wind simulation, solar simulation,
    economic analysis, and exports results.

    Args:
        project_name: Project name
        turbine: Turbine model
        turbine_layout: Turbine layout
        wind_site: Wind site with resource data
        solar_system: PV system specification
        solar_site: Solar site with resource data
        economic_params: Economic parameters
        location: Project location description
        wake_model: Wake model for wind analysis
        output_dir: Output directory for results
        export_formats: List of export formats

    Returns:
        Complete hybrid project result

    Example:
        >>> result = analyze_wind_solar_hybrid(
        ...     project_name="Chile Hybrid 1",
        ...     turbine=turbine_model,
        ...     turbine_layout=layout,
        ...     wind_site=wind_site,
        ...     solar_system=solar_system,
        ...     solar_site=solar_site,
        ...     economic_params=economics,
        ...     location="Antofagasta, Chile"
        ... )
        >>> print(f"NPV: {result.economics.npv/1e6:.1f}M")
    """
    # Create analysis orchestrator
    analysis = HybridAnalysis(
        project_name=project_name,
        location=location,
        output_dir=output_dir
    )

    # Configure components
    analysis.configure_wind(turbine, turbine_layout, wind_site, wake_model)
    analysis.configure_solar(solar_system, solar_site)
    analysis.configure_economics(economic_params)

    # Run analysis
    result = analysis.run()

    # Export results
    if output_dir:
        analysis.export_results(formats=export_formats)
        analysis.save_report(format='markdown')

    return result


def analyze_wind_only(
    project_name: str,
    turbine: TurbineModel,
    turbine_layout: TurbineLayout,
    wind_site: WindSite,
    economic_params: Optional[EconomicParameters] = None,
    location: Optional[str] = None,
    wake_model: str = "NOJ",
    output_dir: Optional[Path] = None
) -> HybridProjectResult:
    """
    Wind-only analysis workflow.

    Args:
        project_name: Project name
        turbine: Turbine model
        turbine_layout: Turbine layout
        wind_site: Wind site with resource data
        economic_params: Economic parameters (auto-generated if None)
        location: Project location
        wake_model: Wake model
        output_dir: Output directory

    Returns:
        Project result (wind-only)

    Example:
        >>> result = analyze_wind_only(
        ...     project_name="Wind Farm 1",
        ...     turbine=turbine_model,
        ...     turbine_layout=layout,
        ...     wind_site=wind_site
        ... )
    """
    # Auto-generate economics if not provided
    if economic_params is None:
        economic_params = create_wind_economics(
            capacity_mw=turbine_layout.total_capacity_mw
        )

    # Create analysis
    analysis = HybridAnalysis(
        project_name=project_name,
        location=location,
        output_dir=output_dir
    )

    analysis.configure_wind(turbine, turbine_layout, wind_site, wake_model)
    analysis.configure_economics(economic_params)

    # Run and return
    result = analysis.run()

    if output_dir:
        analysis.export_results()
        analysis.save_report()

    return result


def analyze_solar_only(
    project_name: str,
    solar_system: SolarSystem,
    solar_site: SolarSite,
    economic_params: Optional[EconomicParameters] = None,
    location: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> HybridProjectResult:
    """
    Solar-only analysis workflow.

    Args:
        project_name: Project name
        solar_system: PV system specification
        solar_site: Solar site with resource data
        economic_params: Economic parameters (auto-generated if None)
        location: Project location
        output_dir: Output directory

    Returns:
        Project result (solar-only)

    Example:
        >>> result = analyze_solar_only(
        ...     project_name="Solar Farm 1",
        ...     solar_system=solar_system,
        ...     solar_site=solar_site
        ... )
    """
    # Auto-generate economics if not provided
    if economic_params is None:
        economic_params = create_solar_economics(
            capacity_mw=solar_system.capacity_mw
        )

    # Create analysis
    analysis = HybridAnalysis(
        project_name=project_name,
        location=location,
        output_dir=output_dir
    )

    analysis.configure_solar(solar_system, solar_site)
    analysis.configure_economics(economic_params)

    # Run and return
    result = analysis.run()

    if output_dir:
        analysis.export_results()
        analysis.save_report()

    return result


def quick_feasibility_study(
    project_name: str,
    wind_capacity_mw: Optional[float] = None,
    solar_capacity_mw: Optional[float] = None,
    annual_wind_production_gwh: Optional[float] = None,
    annual_solar_production_gwh: Optional[float] = None,
    electricity_price: float = 50.0,
    location: Optional[str] = None,
    **economic_kwargs
) -> HybridProjectResult:
    """
    Quick feasibility study without detailed simulation.

    Useful for early-stage screening or comparing scenarios.

    Args:
        project_name: Project name
        wind_capacity_mw: Wind installed capacity
        solar_capacity_mw: Solar installed capacity
        annual_wind_production_gwh: Estimated annual wind production
        annual_solar_production_gwh: Estimated annual solar production
        electricity_price: Electricity price (currency/MWh)
        location: Project location
        **economic_kwargs: Additional economic parameters

    Returns:
        Project result with economic analysis

    Example:
        >>> result = quick_feasibility_study(
        ...     project_name="Quick Study",
        ...     wind_capacity_mw=50,
        ...     solar_capacity_mw=10,
        ...     annual_wind_production_gwh=150,
        ...     annual_solar_production_gwh=30,
        ...     electricity_price=55
        ... )
        >>> print(f"LCOE: {result.economics.lcoe:.2f}")
    """
    if (wind_capacity_mw is None and solar_capacity_mw is None):
        raise ValueError("At least one capacity must be specified")

    # Create economic parameters
    total_capacity_mw = (wind_capacity_mw or 0) + (solar_capacity_mw or 0)

    if wind_capacity_mw and solar_capacity_mw:
        economic_params = create_hybrid_economics(
            wind_capacity_mw=wind_capacity_mw,
            solar_capacity_mw=solar_capacity_mw,
            electricity_price=electricity_price,
            **economic_kwargs
        )
    elif wind_capacity_mw:
        economic_params = create_wind_economics(
            capacity_mw=wind_capacity_mw,
            electricity_price=electricity_price,
            **economic_kwargs
        )
    else:
        economic_params = create_solar_economics(
            capacity_mw=solar_capacity_mw,
            electricity_price=electricity_price,
            **economic_kwargs
        )

    # Calculate metrics directly
    from ..economics import calculate_all_metrics

    total_production_gwh = (annual_wind_production_gwh or 0) + (annual_solar_production_gwh or 0)

    metrics = calculate_all_metrics(
        annual_production_mwh=total_production_gwh * 1000,
        installed_capacity_mw=total_capacity_mw,
        economic_params=economic_params
    )

    # Create minimal result structure
    from ..output import HybridProductionResult, HybridProjectResult, create_hybrid_result

    # Create placeholder production results
    from ..core import WindSimulationResult, SolarProductionResult

    wind_result = None
    if annual_wind_production_gwh:
        wind_result = WindSimulationResult(
            power_timeseries=pd.DataFrame(),  # Empty placeholder
            aep_gwh=annual_wind_production_gwh,
            capacity_factor=annual_wind_production_gwh * 1000 / (wind_capacity_mw * 8760),
            wake_losses=0.08,  # Typical value
            metadata={'type': 'feasibility_estimate'}
        )

    solar_result = None
    if annual_solar_production_gwh:
        solar_result = SolarProductionResult(
            power_timeseries=pd.DataFrame(),  # Empty placeholder
            aep_gwh=annual_solar_production_gwh,
            capacity_factor=annual_solar_production_gwh * 1000 / (solar_capacity_mw * 8760),
            shading_losses=0.0,
            metadata={'type': 'feasibility_estimate'}
        )

    result = create_hybrid_result(
        wind_result=wind_result,
        solar_result=solar_result,
        economic_metrics=metrics,
        project_name=project_name,
        wind_capacity_mw=wind_capacity_mw,
        solar_capacity_mw=solar_capacity_mw,
        location=location,
        analysis_type='feasibility_study'
    )

    return result


def compare_scenarios(
    base_scenario: Dict[str, Any],
    scenarios: Dict[str, Dict[str, Any]],
    output_dir: Optional[Path] = None
) -> pd.DataFrame:
    """
    Compare multiple project scenarios.

    Args:
        base_scenario: Base scenario parameters
        scenarios: Dict of scenario name to parameter overrides
        output_dir: Output directory for comparison table

    Returns:
        DataFrame comparing scenarios

    Example:
        >>> base = {
        ...     'project_name': 'Base',
        ...     'wind_capacity_mw': 50,
        ...     'solar_capacity_mw': 10,
        ...     'annual_wind_production_gwh': 150,
        ...     'annual_solar_production_gwh': 30
        ... }
        >>> scenarios = {
        ...     'High Wind': {'wind_capacity_mw': 75},
        ...     'High Solar': {'solar_capacity_mw': 20},
        ...     'Low Price': {'electricity_price': 40}
        ... }
        >>> comparison = compare_scenarios(base, scenarios)
    """
    results = []

    # Run base scenario
    base_result = quick_feasibility_study(**base_scenario)
    results.append({
        'Scenario': 'Base',
        'Wind MW': base_scenario.get('wind_capacity_mw', 0),
        'Solar MW': base_scenario.get('solar_capacity_mw', 0),
        'AEP GWh': base_result.production.total_aep_gwh,
        'LCOE': base_result.economics.lcoe,
        'NPV M': base_result.economics.npv / 1e6,
        'IRR %': base_result.economics.irr * 100 if base_result.economics.irr else None
    })

    # Run alternative scenarios
    for scenario_name, overrides in scenarios.items():
        scenario_params = {**base_scenario, **overrides}
        scenario_params['project_name'] = scenario_name

        result = quick_feasibility_study(**scenario_params)

        results.append({
            'Scenario': scenario_name,
            'Wind MW': scenario_params.get('wind_capacity_mw', 0),
            'Solar MW': scenario_params.get('solar_capacity_mw', 0),
            'AEP GWh': result.production.total_aep_gwh,
            'LCOE': result.economics.lcoe,
            'NPV M': result.economics.npv / 1e6,
            'IRR %': result.economics.irr * 100 if result.economics.irr else None
        })

    # Create comparison DataFrame
    comparison_df = pd.DataFrame(results)

    # Export if output directory specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        comparison_df.to_csv(output_dir / 'scenario_comparison.csv', index=False)

    return comparison_df
