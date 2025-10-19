"""
Export utilities for analysis results.

Support for CSV, JSON, Excel, and other formats.
"""

from typing import Union, Optional, Dict, Any
from pathlib import Path
import json
import pandas as pd

from .results import HybridProjectResult, HybridProductionResult
from ..economics import FinancialMetrics


def export_to_json(
    result: Union[HybridProjectResult, HybridProductionResult, FinancialMetrics],
    filepath: Union[str, Path],
    indent: int = 2
) -> None:
    """
    Export result to JSON file.

    Args:
        result: Result object to export
        filepath: Output file path
        indent: JSON indentation level

    Example:
        >>> export_to_json(project_result, "output/results.json")
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Get summary dict
    if hasattr(result, 'get_summary'):
        data = result.get_summary()
    else:
        # For FinancialMetrics, create dict manually
        data = {
            'lcoe': result.lcoe,
            'npv': result.npv,
            'irr': result.irr,
            'payback_period': result.payback_period,
            'discounted_payback_period': result.discounted_payback_period,
            'benefit_cost_ratio': result.benefit_cost_ratio,
            'profitability_index': result.profitability_index,
            'capacity_factor': result.capacity_factor,
            'currency': result.currency
        }

    # Convert to JSON-serializable format
    data_serializable = _make_json_serializable(data)

    with open(filepath, 'w') as f:
        json.dump(data_serializable, f, indent=indent)


def _make_json_serializable(obj: Any) -> Any:
    """Convert object to JSON-serializable format."""
    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif hasattr(obj, '__dict__'):
        return _make_json_serializable(obj.__dict__)
    else:
        return str(obj)


def export_to_csv(
    result: HybridProjectResult,
    output_dir: Union[str, Path],
    prefix: str = ""
) -> Dict[str, Path]:
    """
    Export result to multiple CSV files.

    Creates separate CSV files for timeseries and summary data.

    Args:
        result: HybridProjectResult to export
        output_dir: Output directory path
        prefix: Optional file prefix

    Returns:
        Dict mapping file type to filepath

    Example:
        >>> files = export_to_csv(project_result, "output/", prefix="hybrid_")
        >>> print(files['summary'])  # Path to summary.csv
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {}

    # Export summary
    summary_data = result.get_summary()
    summary_df = _flatten_dict_to_dataframe(summary_data)
    summary_path = output_dir / f"{prefix}summary.csv"
    summary_df.to_csv(summary_path)
    files['summary'] = summary_path

    # Export combined timeseries if available
    if result.production.combined_timeseries is not None:
        timeseries_path = output_dir / f"{prefix}timeseries.csv"
        result.production.combined_timeseries.to_csv(timeseries_path)
        files['timeseries'] = timeseries_path

    # Export wind timeseries if available
    if result.production.wind_result and result.production.wind_result.power_timeseries is not None:
        wind_path = output_dir / f"{prefix}wind_timeseries.csv"
        result.production.wind_result.power_timeseries.to_csv(wind_path)
        files['wind_timeseries'] = wind_path

    # Export solar timeseries if available
    if result.production.solar_result and result.production.solar_result.power_timeseries is not None:
        solar_path = output_dir / f"{prefix}solar_timeseries.csv"
        result.production.solar_result.power_timeseries.to_csv(solar_path)
        files['solar_timeseries'] = solar_path

    return files


def _flatten_dict_to_dataframe(d: Dict, parent_key: str = '', sep: str = '_') -> pd.DataFrame:
    """Flatten nested dictionary to DataFrame."""
    items = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(_flatten_dict_to_dataframe(v, new_key, sep=sep).to_dict('records'))
        else:
            items.append({new_key: v})

    # Combine all items
    result = {}
    for item in items:
        result.update(item)

    return pd.DataFrame([result])


def export_to_excel(
    result: HybridProjectResult,
    filepath: Union[str, Path],
    include_timeseries: bool = True
) -> None:
    """
    Export result to Excel file with multiple sheets.

    Args:
        result: HybridProjectResult to export
        filepath: Output Excel file path
        include_timeseries: Whether to include timeseries sheets

    Example:
        >>> export_to_excel(project_result, "output/results.xlsx")
    """
    try:
        import openpyxl  # Check if openpyxl available
    except ImportError:
        raise ImportError(
            "openpyxl required for Excel export. "
            "Install with: conda install -c conda-forge openpyxl"
        )

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = result.get_summary()
        summary_df = _flatten_dict_to_dataframe(summary_data)
        summary_df.T.to_excel(writer, sheet_name='Summary')

        # Production metrics
        production_metrics = {
            'Total AEP (GWh)': result.production.total_aep_gwh,
            'Combined Capacity Factor': result.production.combined_capacity_factor,
            'Wind AEP (GWh)': result.production.wind_aep_gwh,
            'Solar AEP (GWh)': result.production.solar_aep_gwh,
            'Wind Contribution (%)': result.production.wind_contribution * 100,
            'Solar Contribution (%)': result.production.solar_contribution * 100
        }
        prod_df = pd.DataFrame.from_dict(production_metrics, orient='index', columns=['Value'])
        prod_df.to_excel(writer, sheet_name='Production')

        # Economics metrics
        economics_metrics = {
            'LCOE (currency/MWh)': result.economics.lcoe,
            'NPV (currency)': result.economics.npv,
            'IRR (%)': result.economics.irr * 100 if result.economics.irr else None,
            'Payback Period (years)': result.economics.payback_period,
            'Discounted Payback (years)': result.economics.discounted_payback_period,
            'Benefit-Cost Ratio': result.economics.benefit_cost_ratio,
            'Profitability Index': result.economics.profitability_index,
            'Capacity Factor (%)': result.economics.capacity_factor * 100
        }
        econ_df = pd.DataFrame.from_dict(economics_metrics, orient='index', columns=['Value'])
        econ_df.to_excel(writer, sheet_name='Economics')

        # Timeseries sheets
        if include_timeseries:
            if result.production.combined_timeseries is not None:
                result.production.combined_timeseries.to_excel(writer, sheet_name='Combined Timeseries')

            if result.production.wind_result and result.production.wind_result.power_timeseries is not None:
                result.production.wind_result.power_timeseries.to_excel(writer, sheet_name='Wind Timeseries')

            if result.production.solar_result and result.production.solar_result.power_timeseries is not None:
                result.production.solar_result.power_timeseries.to_excel(writer, sheet_name='Solar Timeseries')


def export_summary_table(
    result: HybridProjectResult,
    filepath: Union[str, Path],
    format: str = 'csv'
) -> None:
    """
    Export concise summary table.

    Args:
        result: HybridProjectResult to export
        filepath: Output file path
        format: Output format ('csv', 'excel', or 'markdown')

    Example:
        >>> export_summary_table(project_result, "output/summary.md", format='markdown')
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create summary table
    summary = {
        'Project Name': result.project_name,
        'Location': result.location or 'N/A',
        'Total Capacity (MW)': result.installed_capacity_mw,
        'Wind Capacity (MW)': result.wind_capacity_mw or 0,
        'Solar Capacity (MW)': result.solar_capacity_mw or 0,
        'Annual Energy Production (GWh)': result.production.total_aep_gwh,
        'Combined Capacity Factor (%)': result.production.combined_capacity_factor * 100,
        'LCOE (currency/MWh)': result.economics.lcoe,
        'NPV (M currency)': result.economics.npv / 1e6,
        'IRR (%)': result.economics.irr * 100 if result.economics.irr else None,
        'Payback Period (years)': result.economics.payback_period
    }

    df = pd.DataFrame.from_dict(summary, orient='index', columns=['Value'])

    if format == 'csv':
        df.to_csv(filepath)
    elif format == 'excel':
        df.to_excel(filepath)
    elif format == 'markdown':
        with open(filepath, 'w') as f:
            f.write(df.to_markdown())
    else:
        raise ValueError(f"Unknown format: {format}. Use 'csv', 'excel', or 'markdown'")


def export_all(
    result: HybridProjectResult,
    output_dir: Union[str, Path],
    prefix: str = "",
    formats: list = ['json', 'csv', 'excel']
) -> Dict[str, Any]:
    """
    Export result to all available formats.

    Args:
        result: HybridProjectResult to export
        output_dir: Output directory
        prefix: File prefix
        formats: List of formats to export ('json', 'csv', 'excel', 'markdown')

    Returns:
        Dict mapping format to output file paths

    Example:
        >>> files = export_all(project_result, "output/", prefix="hybrid_")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    exported_files = {}

    if 'json' in formats:
        json_path = output_dir / f"{prefix}results.json"
        export_to_json(result, json_path)
        exported_files['json'] = json_path

    if 'csv' in formats:
        csv_files = export_to_csv(result, output_dir, prefix=prefix)
        exported_files['csv'] = csv_files

    if 'excel' in formats:
        excel_path = output_dir / f"{prefix}results.xlsx"
        export_to_excel(result, excel_path)
        exported_files['excel'] = excel_path

    if 'markdown' in formats:
        md_path = output_dir / f"{prefix}summary.md"
        export_summary_table(result, md_path, format='markdown')
        exported_files['markdown'] = md_path

    return exported_files
