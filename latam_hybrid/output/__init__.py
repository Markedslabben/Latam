"""
Output and reporting module.

Provides result aggregation, export utilities, and report generation
for hybrid energy project analysis.
"""

# Result containers
from .results import (
    HybridProductionResult,
    HybridProjectResult,
    combine_production_timeseries,
    create_hybrid_result
)

# Export utilities
from .export import (
    export_to_json,
    export_to_csv,
    export_to_excel,
    export_summary_table,
    export_all,
    export_per_turbine_losses_table
)

# Report generation
from .reports import (
    generate_text_report,
    generate_markdown_report,
    generate_executive_summary,
    save_report
)


__all__ = [
    # Results
    'HybridProductionResult',
    'HybridProjectResult',
    'combine_production_timeseries',
    'create_hybrid_result',

    # Export
    'export_to_json',
    'export_to_csv',
    'export_to_excel',
    'export_summary_table',
    'export_all',
    'export_per_turbine_losses_table',

    # Reports
    'generate_text_report',
    'generate_markdown_report',
    'generate_executive_summary',
    'save_report',
]
