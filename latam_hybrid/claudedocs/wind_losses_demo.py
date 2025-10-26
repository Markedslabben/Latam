"""
Wind Farm Losses Module - Demonstration Script

This script demonstrates the key features of the wind farm losses module.
"""

from latam_hybrid.wind.losses import WindFarmLosses, create_default_losses, LossType


def demo_basic_usage():
    """Demonstrate basic losses calculation."""
    print("=" * 60)
    print("Demo 1: Basic Losses Calculation")
    print("=" * 60)

    # Create losses manager
    losses = WindFarmLosses()

    # Add wake losses (typically from PyWake simulation)
    losses.add_loss('wake_losses', 0.08, is_computed=True,
                    description="Wake losses from turbine interactions")

    # Add default WindPRO losses
    losses.add_default_losses()

    # Calculate results
    gross_aep = 1000.0  # GWh
    net_aep = losses.calculate_net_aep(gross_aep)
    total_loss_pct = losses.calculate_total_loss_percentage()

    print(f"\nGross AEP: {gross_aep:.2f} GWh")
    print(f"Net AEP: {net_aep:.2f} GWh")
    print(f"Total loss factor: {losses.calculate_total_loss_factor():.4f}")
    print(f"Total losses: {total_loss_pct:.2f}%")

    print("\nDetailed Loss Breakdown:")
    print("-" * 60)
    breakdown = losses.get_loss_breakdown()
    for name, data in breakdown.items():
        computed_flag = " (computed)" if data['is_computed'] else ""
        print(f"  {name:40s}: {data['percentage']:6.2f}%{computed_flag}")

    print()


def demo_custom_losses():
    """Demonstrate custom loss values."""
    print("=" * 60)
    print("Demo 2: Custom Loss Values")
    print("=" * 60)

    losses = WindFarmLosses()

    # Add wake losses
    losses.add_loss('wake_losses', 0.10, is_computed=True)

    # Add custom loss values
    losses.add_default_losses(
        availability_turbines=0.02,      # 2% instead of 1.5%
        electrical_losses=0.025,         # 2.5% instead of 2.0%
        environmental_degradation=0.04   # 4% instead of 3.0%
    )

    gross_aep = 500.0  # GWh
    net_aep = losses.calculate_net_aep(gross_aep)

    print(f"\nGross AEP: {gross_aep:.2f} GWh")
    print(f"Net AEP: {net_aep:.2f} GWh")
    print(f"Energy lost: {gross_aep - net_aep:.2f} GWh")
    print(f"Total losses: {losses.calculate_total_loss_percentage():.2f}%")

    print("\nCustom vs Default:")
    print("-" * 60)
    custom_breakdown = losses.get_loss_breakdown()
    defaults = WindFarmLosses.DEFAULTS

    for loss_type in [LossType.AVAILABILITY_TURBINES, LossType.ELECTRICAL,
                      LossType.ENVIRONMENTAL_DEGRADATION]:
        custom_val = custom_breakdown[loss_type.value]['percentage']
        default_val = defaults[loss_type] * 100
        diff = custom_val - default_val
        print(f"  {loss_type.value:40s}: {custom_val:.2f}% "
              f"(default: {default_val:.2f}%, diff: {diff:+.2f}%)")

    print()


def demo_convenience_function():
    """Demonstrate convenience function."""
    print("=" * 60)
    print("Demo 3: Convenience Function")
    print("=" * 60)

    # Quick setup with create_default_losses
    losses = create_default_losses(
        wake_loss=0.09,
        curtailment_sector=0.03,
        availability_turbines=0.018
    )

    gross_aep = 750.0  # GWh
    net_aep = losses.calculate_net_aep(gross_aep)

    print(f"\nGross AEP: {gross_aep:.2f} GWh")
    print(f"Net AEP: {net_aep:.2f} GWh")

    # Separate computed and user losses
    print("\nComputed Losses:")
    print("-" * 60)
    for name, loss in losses.get_computed_losses().items():
        print(f"  {name:40s}: {loss.percentage:.2f}%")

    print("\nUser-Specified Losses:")
    print("-" * 60)
    for name, loss in losses.get_user_losses().items():
        print(f"  {name:40s}: {loss.percentage:.2f}%")

    print()


def demo_multiplicative_formula():
    """Demonstrate multiplicative vs additive formula."""
    print("=" * 60)
    print("Demo 4: Multiplicative Formula Explanation")
    print("=" * 60)

    losses = WindFarmLosses()
    losses.add_loss('loss1', 0.03)  # 3%
    losses.add_loss('loss2', 0.02)  # 2%

    # Additive (wrong)
    additive_loss = 0.03 + 0.02  # 5%
    additive_factor = 1 - additive_loss  # 0.95

    # Multiplicative (correct)
    multiplicative_factor = losses.calculate_total_loss_factor()  # 0.9506
    multiplicative_loss = 1 - multiplicative_factor  # 0.0494 = 4.94%

    print("\nExample: 3% and 2% losses")
    print("-" * 60)
    print(f"Additive approach (WRONG):")
    print(f"  Total loss: {additive_loss * 100:.2f}%")
    print(f"  Loss factor: {additive_factor:.4f}")

    print(f"\nMultiplicative approach (CORRECT):")
    print(f"  Total loss: {multiplicative_loss * 100:.2f}%")
    print(f"  Loss factor: {multiplicative_factor:.4f}")

    print(f"\nDifference: {(multiplicative_loss - additive_loss) * 100:.2f} percentage points")

    # Impact on AEP
    gross_aep = 1000.0
    additive_aep = gross_aep * additive_factor
    multiplicative_aep = gross_aep * multiplicative_factor

    print(f"\nImpact on 1000 GWh gross AEP:")
    print(f"  Additive: {additive_aep:.2f} GWh")
    print(f"  Multiplicative: {multiplicative_aep:.2f} GWh")
    print(f"  Difference: {multiplicative_aep - additive_aep:.2f} GWh")

    print()


def demo_realistic_scenario():
    """Demonstrate realistic wind farm scenario."""
    print("=" * 60)
    print("Demo 5: Realistic 100 MW Wind Farm Scenario")
    print("=" * 60)

    # Typical 100 MW wind farm
    capacity_mw = 100
    capacity_factor_gross = 0.40  # 40% gross capacity factor
    gross_aep = capacity_mw * 8760 / 1000 * capacity_factor_gross  # GWh

    print(f"\nWind Farm Parameters:")
    print(f"  Capacity: {capacity_mw} MW")
    print(f"  Gross capacity factor: {capacity_factor_gross * 100:.1f}%")
    print(f"  Gross AEP: {gross_aep:.2f} GWh")

    # Apply typical losses
    losses = create_default_losses(wake_loss=0.095)  # 9.5% wake losses

    net_aep = losses.calculate_net_aep(gross_aep)
    net_capacity_factor = net_aep / (capacity_mw * 8760 / 1000)

    print(f"\nResults:")
    print(f"  Net AEP: {net_aep:.2f} GWh")
    print(f"  Net capacity factor: {net_capacity_factor * 100:.1f}%")
    print(f"  Total losses: {losses.calculate_total_loss_percentage():.2f}%")
    print(f"  Energy lost: {gross_aep - net_aep:.2f} GWh/year")

    # Revenue impact
    electricity_price = 50  # USD/MWh
    gross_revenue = gross_aep * 1000 * electricity_price
    net_revenue = net_aep * 1000 * electricity_price
    revenue_loss = gross_revenue - net_revenue

    print(f"\nRevenue Impact (@ ${electricity_price}/MWh):")
    print(f"  Gross revenue: ${gross_revenue:,.0f}/year")
    print(f"  Net revenue: ${net_revenue:,.0f}/year")
    print(f"  Revenue lost to losses: ${revenue_loss:,.0f}/year")

    print("\nLoss Breakdown:")
    print("-" * 60)
    breakdown = losses.get_loss_breakdown()
    for name, data in breakdown.items():
        energy_loss = gross_aep * data['value']
        revenue_impact = energy_loss * 1000 * electricity_price
        print(f"  {name:40s}: {data['percentage']:5.2f}% "
              f"({energy_loss:5.2f} GWh, ${revenue_impact:>10,.0f})")

    print()


def demo_export_and_reporting():
    """Demonstrate export and reporting capabilities."""
    print("=" * 60)
    print("Demo 6: Export and Reporting")
    print("=" * 60)

    losses = create_default_losses(wake_loss=0.08)

    # Export to dictionary
    export = losses.to_dict()

    print("\nExported Data Structure:")
    print("-" * 60)
    print(f"Total loss factor: {export['total_loss_factor']:.4f}")
    print(f"Total loss percentage: {export['total_loss_percentage']:.2f}%")

    print(f"\nComputed losses: {len(export['computed_losses'])} categories")
    for name, pct in export['computed_losses'].items():
        print(f"  - {name}: {pct:.2f}%")

    print(f"\nUser-specified losses: {len(export['user_losses'])} categories")
    for name, pct in export['user_losses'].items():
        print(f"  - {name}: {pct:.2f}%")

    print(f"\nTotal categories: {len(export['loss_categories'])}")

    # This could be saved to JSON for reporting
    import json
    json_str = json.dumps(export, indent=2)
    print("\nJSON export ready for reporting/storage")
    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  Wind Farm Losses Module - Demonstration".center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    print("\n")

    demo_basic_usage()
    demo_custom_losses()
    demo_convenience_function()
    demo_multiplicative_formula()
    demo_realistic_scenario()
    demo_export_and_reporting()

    print("=" * 60)
    print("All demonstrations completed successfully!")
    print("=" * 60)
    print()


if __name__ == '__main__':
    main()
