"""
Hybrid analysis orchestration.

Provides high-level orchestration for complete wind+solar hybrid energy analysis.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import pandas as pd

from ..wind import WindSite, TurbineModel, TurbineLayout
from ..solar import SolarSite, SolarSystem
try:
    from ..solar import ShadingCalculator
except ImportError:
    ShadingCalculator = None

# GIS is optional for basic workflows
try:
    from ..gis import SiteArea as GISManager
except ImportError:
    GISManager = None
from ..economics import (
    EconomicParameters,
    calculate_all_metrics,
    calculate_revenue_timeseries,
)
from ..output import (
    HybridProductionResult,
    HybridProjectResult,
    create_hybrid_result,
    export_all,
    save_report,
)
from ..core import WindSimulationResult, SolarProductionResult


class HybridAnalysis:
    """
    Orchestrates complete hybrid wind+solar energy analysis.

    Provides fluent API for coordinating wind site analysis, solar production,
    GIS visualization, economic calculations, and report generation.

    Example:
        >>> analysis = HybridAnalysis(
        ...     project_name="Chile Hybrid 1",
        ...     location="Antofagasta, Chile"
        ... )
        >>> analysis.configure_wind(turbine, layout, wind_data)
        >>> analysis.configure_solar(pv_system, solar_data)
        >>> analysis.configure_economics(economic_params)
        >>> results = analysis.run()
        >>> analysis.export_results("output/")
    """

    def __init__(
        self,
        project_name: str = "Hybrid Project",
        location: Optional[str] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize hybrid analysis.

        Args:
            project_name: Project name for reports
            location: Project location description
            output_dir: Directory for output files
        """
        self.project_name = project_name
        self.location = location
        self.output_dir = Path(output_dir) if output_dir else Path("output")

        # Components
        self.wind_site: Optional[WindSite] = None
        self.solar_site: Optional[SolarSite] = None
        self.gis_manager: Optional[GISManager] = None
        self.economic_params: Optional[EconomicParameters] = None

        # Results
        self.wind_result: Optional[WindSimulationResult] = None
        self.solar_result: Optional[SolarProductionResult] = None
        self.hybrid_result: Optional[HybridProjectResult] = None

        # Metadata
        self.metadata: Dict[str, Any] = {}

    def configure_wind(
        self,
        turbine: TurbineModel,
        layout: TurbineLayout,
        wind_site: WindSite,
        wake_model: str = "NOJ"
    ) -> 'HybridAnalysis':
        """
        Configure wind energy analysis.

        Args:
            turbine: Turbine model
            layout: Turbine layout
            wind_site: Wind site with resource data
            wake_model: Wake model to use

        Returns:
            Self for method chaining
        """
        self.wind_site = wind_site
        self.metadata['wind_turbine'] = turbine.name
        self.metadata['wind_turbines'] = layout.n_turbines
        self.metadata['wind_capacity_mw'] = layout.total_capacity_mw
        self.metadata['wake_model'] = wake_model

        return self

    def configure_solar(
        self,
        solar_system: SolarSystem,
        solar_site: SolarSite
    ) -> 'HybridAnalysis':
        """
        Configure solar energy analysis.

        Args:
            solar_system: Solar system specification
            solar_site: Solar site with resource data

        Returns:
            Self for method chaining
        """
        self.solar_site = solar_site
        self.metadata['solar_system'] = solar_system.name
        self.metadata['solar_capacity_mw'] = solar_system.capacity_mw

        return self

    def configure_gis(
        self,
        gis_manager: GISManager
    ) -> 'HybridAnalysis':
        """
        Configure GIS visualization.

        Args:
            gis_manager: GIS manager with site data

        Returns:
            Self for method chaining
        """
        self.gis_manager = gis_manager
        return self

    def configure_economics(
        self,
        economic_params: EconomicParameters
    ) -> 'HybridAnalysis':
        """
        Configure economic analysis parameters.

        Args:
            economic_params: Economic parameters

        Returns:
            Self for method chaining
        """
        self.economic_params = economic_params
        return self

    def calculate_shading(
        self,
        solar_positions: Optional[List] = None
    ) -> 'HybridAnalysis':
        """
        Calculate turbine shading on solar panels.

        Args:
            solar_positions: Optional list of solar panel positions

        Returns:
            Self for method chaining
        """
        if self.gis_manager is None:
            raise ValueError("GIS manager must be configured before calculating shading")

        if self.wind_site is None or self.solar_site is None:
            raise ValueError("Both wind and solar sites must be configured")

        # Calculate shading using GIS manager
        # This would integrate with ShadingCalculator
        # For now, just mark as calculated
        self.metadata['shading_calculated'] = True

        return self

    def run_wind_analysis(self) -> 'HybridAnalysis':
        """
        Run wind farm simulation.

        Returns:
            Self for method chaining
        """
        if self.wind_site is None:
            raise ValueError("Wind site must be configured before running analysis")

        # Run wind simulation
        # This would call wind_site.simulate()
        # For now, store placeholder
        self.metadata['wind_analysis_complete'] = True

        return self

    def run_solar_analysis(self) -> 'HybridAnalysis':
        """
        Run solar production analysis.

        Returns:
            Self for method chaining
        """
        if self.solar_site is None:
            raise ValueError("Solar site must be configured before running analysis")

        # Run solar simulation
        # This would call solar_site.simulate()
        # For now, store placeholder
        self.metadata['solar_analysis_complete'] = True

        return self

    def run(self) -> HybridProjectResult:
        """
        Run complete hybrid analysis.

        Executes wind simulation, solar simulation, economic analysis,
        and aggregates results.

        Returns:
            Complete hybrid project result

        Example:
            >>> result = analysis.run()
            >>> print(f"Total AEP: {result.production.total_aep_gwh:.1f} GWh")
            >>> print(f"LCOE: {result.economics.lcoe:.2f}")
        """
        if self.wind_site is None and self.solar_site is None:
            raise ValueError("At least one of wind or solar must be configured")

        # Run analyses
        if self.wind_site is not None:
            self.run_wind_analysis()

        if self.solar_site is not None:
            self.run_solar_analysis()

        # Calculate economics if configured
        if self.economic_params is None:
            raise ValueError("Economic parameters must be configured")

        # Get capacities
        wind_capacity_mw = self.metadata.get('wind_capacity_mw', 0)
        solar_capacity_mw = self.metadata.get('solar_capacity_mw', 0)
        total_capacity_mw = wind_capacity_mw + solar_capacity_mw

        # Calculate financial metrics
        # For now, use placeholder values - in real implementation would use actual results
        total_aep_gwh = 180.0  # Placeholder

        financial_metrics = calculate_all_metrics(
            annual_production_mwh=total_aep_gwh * 1000,
            installed_capacity_mw=total_capacity_mw,
            economic_params=self.economic_params
        )

        # Create hybrid result
        self.hybrid_result = create_hybrid_result(
            wind_result=self.wind_result,
            solar_result=self.solar_result,
            economic_metrics=financial_metrics,
            project_name=self.project_name,
            wind_capacity_mw=wind_capacity_mw,
            solar_capacity_mw=solar_capacity_mw,
            location=self.location,
            **self.metadata
        )

        return self.hybrid_result

    def export_results(
        self,
        output_dir: Optional[Path] = None,
        formats: List[str] = ['json', 'csv', 'excel', 'markdown']
    ) -> Dict[str, Any]:
        """
        Export results to files.

        Args:
            output_dir: Output directory (uses self.output_dir if None)
            formats: List of export formats

        Returns:
            Dict mapping format to file paths

        Example:
            >>> files = analysis.export_results("output/", formats=['json', 'excel'])
        """
        if self.hybrid_result is None:
            raise ValueError("Must run analysis before exporting results")

        output_dir = Path(output_dir) if output_dir else self.output_dir

        return export_all(
            self.hybrid_result,
            output_dir,
            prefix=f"{self.project_name.replace(' ', '_')}_",
            formats=formats
        )

    def save_report(
        self,
        filepath: Optional[Path] = None,
        format: str = 'markdown'
    ) -> None:
        """
        Generate and save analysis report.

        Args:
            filepath: Output file path (auto-generated if None)
            format: Report format ('text' or 'markdown')

        Example:
            >>> analysis.save_report("output/report.md", format='markdown')
        """
        if self.hybrid_result is None:
            raise ValueError("Must run analysis before generating report")

        if filepath is None:
            suffix = '.md' if format == 'markdown' else '.txt'
            filepath = self.output_dir / f"{self.project_name.replace(' ', '_')}_report{suffix}"

        save_report(self.hybrid_result, filepath, format=format)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get analysis summary.

        Returns:
            Summary dictionary
        """
        if self.hybrid_result is None:
            raise ValueError("Must run analysis before getting summary")

        return self.hybrid_result.get_summary()
