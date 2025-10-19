"""
Report generation for hybrid energy projects.

Create formatted text and markdown reports from analysis results.
"""

from typing import Union, Optional
from pathlib import Path
from datetime import datetime

from .results import HybridProjectResult


def generate_text_report(result: HybridProjectResult) -> str:
    """
    Generate plain text report.

    Args:
        result: HybridProjectResult

    Returns:
        Formatted text report string

    Example:
        >>> report = generate_text_report(project_result)
        >>> print(report)
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append(f"HYBRID ENERGY PROJECT ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Project Information
    lines.append("PROJECT INFORMATION")
    lines.append("-" * 80)
    lines.append(f"Project Name:        {result.project_name}")
    if result.location:
        lines.append(f"Location:            {result.location}")
    lines.append(f"Total Capacity:      {result.installed_capacity_mw:.1f} MW")
    lines.append(f"  Wind Capacity:     {result.wind_capacity_mw or 0:.1f} MW ({result.capacity_mix['wind']:.1%})")
    lines.append(f"  Solar Capacity:    {result.solar_capacity_mw or 0:.1f} MW ({result.capacity_mix['solar']:.1%})")
    lines.append("")

    # Production Summary
    lines.append("PRODUCTION SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Total Annual Energy Production:  {result.production.total_aep_gwh:.1f} GWh")
    lines.append(f"Combined Capacity Factor:        {result.production.combined_capacity_factor:.1%}")
    lines.append("")
    lines.append(f"Wind Production:")
    lines.append(f"  Annual Energy:     {result.production.wind_aep_gwh:.1f} GWh ({result.energy_mix['wind']:.1%})")
    if result.production.wind_capacity_factor:
        lines.append(f"  Capacity Factor:   {result.production.wind_capacity_factor:.1%}")
    if result.production.wind_result and result.production.wind_result.wake_losses is not None:
        lines.append(f"  Wake Losses:       {result.production.wind_result.wake_losses:.1%}")
    lines.append("")
    lines.append(f"Solar Production:")
    lines.append(f"  Annual Energy:     {result.production.solar_aep_gwh:.1f} GWh ({result.energy_mix['solar']:.1%})")
    if result.production.solar_capacity_factor:
        lines.append(f"  Capacity Factor:   {result.production.solar_capacity_factor:.1%}")
    if result.production.solar_result and result.production.solar_result.shading_losses is not None:
        lines.append(f"  Shading Losses:    {result.production.solar_result.shading_losses:.1%}")
    lines.append("")

    # Economic Summary
    lines.append("ECONOMIC ANALYSIS")
    lines.append("-" * 80)
    currency = result.economics.currency
    lines.append(f"Levelized Cost of Energy (LCOE): {result.economics.lcoe:.2f} {currency}/MWh")
    lines.append(f"Net Present Value (NPV):         {result.economics.npv/1e6:.2f} M{currency}")

    if result.economics.irr is not None:
        lines.append(f"Internal Rate of Return (IRR):   {result.economics.irr:.1%}")
    else:
        lines.append(f"Internal Rate of Return (IRR):   N/A")

    if result.economics.payback_period is not None:
        lines.append(f"Simple Payback Period:           {result.economics.payback_period:.1f} years")
    else:
        lines.append(f"Simple Payback Period:           Never")

    if result.economics.discounted_payback_period is not None:
        lines.append(f"Discounted Payback Period:       {result.economics.discounted_payback_period:.1f} years")
    else:
        lines.append(f"Discounted Payback Period:       Never")

    lines.append(f"Benefit-Cost Ratio:              {result.economics.benefit_cost_ratio:.2f}")
    lines.append(f"Profitability Index:             {result.economics.profitability_index:.2f}")
    lines.append("")

    # Footer
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    return "\n".join(lines)


def generate_markdown_report(result: HybridProjectResult) -> str:
    """
    Generate markdown report.

    Args:
        result: HybridProjectResult

    Returns:
        Formatted markdown report string

    Example:
        >>> report = generate_markdown_report(project_result)
        >>> with open("report.md", "w") as f:
        ...     f.write(report)
    """
    lines = []

    # Header
    lines.append(f"# Hybrid Energy Project Analysis Report")
    lines.append(f"**Project:** {result.project_name}")
    if result.location:
        lines.append(f"**Location:** {result.location}")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Project Information
    lines.append("## 1. Project Overview")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Total Installed Capacity | {result.installed_capacity_mw:.1f} MW |")
    lines.append(f"| Wind Capacity | {result.wind_capacity_mw or 0:.1f} MW ({result.capacity_mix['wind']:.1%}) |")
    lines.append(f"| Solar Capacity | {result.solar_capacity_mw or 0:.1f} MW ({result.capacity_mix['solar']:.1%}) |")
    lines.append("")

    # Production Summary
    lines.append("## 2. Production Analysis")
    lines.append("")
    lines.append("### 2.1 Overall Production")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Annual Energy Production | {result.production.total_aep_gwh:.1f} GWh |")
    lines.append(f"| Combined Capacity Factor | {result.production.combined_capacity_factor:.1%} |")
    lines.append("")

    lines.append("### 2.2 Energy Mix")
    lines.append("")
    lines.append("| Source | Production (GWh) | Share (%) | Capacity Factor |")
    lines.append("|--------|------------------|-----------|-----------------|")
    wind_cf = f"{result.production.wind_capacity_factor:.1%}" if result.production.wind_capacity_factor else "N/A"
    lines.append(f"| Wind | {result.production.wind_aep_gwh:.1f} | {result.energy_mix['wind']:.1%} | {wind_cf} |")
    solar_cf = f"{result.production.solar_capacity_factor:.1%}" if result.production.solar_capacity_factor else "N/A"
    lines.append(f"| Solar | {result.production.solar_aep_gwh:.1f} | {result.energy_mix['solar']:.1%} | {solar_cf} |")
    lines.append("")

    # Economic Analysis
    lines.append("## 3. Economic Analysis")
    lines.append("")
    currency = result.economics.currency
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Levelized Cost of Energy (LCOE) | {result.economics.lcoe:.2f} {currency}/MWh |")
    lines.append(f"| Net Present Value (NPV) | {result.economics.npv/1e6:.2f} M{currency} |")

    irr_str = f"{result.economics.irr:.1%}" if result.economics.irr else "N/A"
    lines.append(f"| Internal Rate of Return (IRR) | {irr_str} |")

    payback_str = f"{result.economics.payback_period:.1f} years" if result.economics.payback_period else "Never"
    lines.append(f"| Simple Payback Period | {payback_str} |")

    disc_payback_str = f"{result.economics.discounted_payback_period:.1f} years" if result.economics.discounted_payback_period else "Never"
    lines.append(f"| Discounted Payback Period | {disc_payback_str} |")

    lines.append(f"| Benefit-Cost Ratio | {result.economics.benefit_cost_ratio:.2f} |")
    lines.append(f"| Profitability Index | {result.economics.profitability_index:.2f} |")
    lines.append("")

    # Key Findings
    lines.append("## 4. Key Findings")
    lines.append("")
    lines.append(_generate_key_findings(result))
    lines.append("")

    return "\n".join(lines)


def _generate_key_findings(result: HybridProjectResult) -> str:
    """Generate key findings section based on results."""
    findings = []

    # Energy mix finding
    if result.energy_mix['wind'] > 0.7:
        findings.append(f"- **Wind-dominated project:** Wind contributes {result.energy_mix['wind']:.0%} of total energy production.")
    elif result.energy_mix['solar'] > 0.7:
        findings.append(f"- **Solar-dominated project:** Solar contributes {result.energy_mix['solar']:.0%} of total energy production.")
    else:
        findings.append(f"- **Balanced hybrid:** Wind and solar contributions are relatively balanced ({result.energy_mix['wind']:.0%} wind, {result.energy_mix['solar']:.0%} solar).")

    # Economic viability
    if result.economics.npv > 0:
        findings.append(f"- **Economically viable:** Positive NPV of {result.economics.npv/1e6:.1f}M {result.economics.currency} indicates project profitability.")
    else:
        findings.append(f"- **Economic concerns:** Negative NPV of {result.economics.npv/1e6:.1f}M {result.economics.currency} suggests project may not be profitable under current assumptions.")

    # IRR comparison
    if result.economics.irr and result.economics.irr > 0.12:
        findings.append(f"- **Strong returns:** IRR of {result.economics.irr:.1%} indicates attractive investment returns.")
    elif result.economics.irr and result.economics.irr > 0.08:
        findings.append(f"- **Moderate returns:** IRR of {result.economics.irr:.1%} meets typical project hurdle rates.")

    # Capacity factor
    if result.production.combined_capacity_factor > 0.45:
        findings.append(f"- **Excellent capacity factor:** Combined capacity factor of {result.production.combined_capacity_factor:.1%} is above industry average.")
    elif result.production.combined_capacity_factor > 0.35:
        findings.append(f"- **Good capacity factor:** Combined capacity factor of {result.production.combined_capacity_factor:.1%} meets industry standards.")

    return "\n".join(findings)


def save_report(
    result: HybridProjectResult,
    filepath: Union[str, Path],
    format: str = 'markdown'
) -> None:
    """
    Generate and save report to file.

    Args:
        result: HybridProjectResult
        filepath: Output file path
        format: Report format ('text' or 'markdown')

    Example:
        >>> save_report(project_result, "output/report.md", format='markdown')
        >>> save_report(project_result, "output/report.txt", format='text')
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if format == 'markdown':
        content = generate_markdown_report(result)
    elif format == 'text':
        content = generate_text_report(result)
    else:
        raise ValueError(f"Unknown format: {format}. Use 'text' or 'markdown'")

    with open(filepath, 'w') as f:
        f.write(content)


def generate_executive_summary(result: HybridProjectResult) -> str:
    """
    Generate concise executive summary.

    Args:
        result: HybridProjectResult

    Returns:
        Executive summary string

    Example:
        >>> summary = generate_executive_summary(project_result)
        >>> print(summary)
    """
    currency = result.economics.currency

    summary = f"""
EXECUTIVE SUMMARY
{result.project_name}

Project Capacity: {result.installed_capacity_mw:.0f} MW ({result.capacity_mix['wind']:.0%} wind, {result.capacity_mix['solar']:.0%} solar)
Annual Production: {result.production.total_aep_gwh:.0f} GWh
Capacity Factor: {result.production.combined_capacity_factor:.1%}

LCOE: {result.economics.lcoe:.1f} {currency}/MWh
NPV: {result.economics.npv/1e6:.1f} M{currency}
IRR: {result.economics.irr:.1%}" if result.economics.irr else "IRR: N/A
"""

    recommendation = ""
    if result.economics.npv > 0 and result.economics.irr and result.economics.irr > 0.10:
        recommendation = "RECOMMENDATION: PROCEED - Project demonstrates strong economic viability."
    elif result.economics.npv > 0:
        recommendation = "RECOMMENDATION: CONDITIONAL - Project is viable but returns are modest."
    else:
        recommendation = "RECOMMENDATION: RECONSIDER - Project economics require optimization."

    summary += f"\n{recommendation}"

    return summary.strip()
