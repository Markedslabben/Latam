"""
Sector Management Demonstration Script

This script demonstrates how to configure and use sector management for
wind turbine curtailment when turbines must be stopped for certain wind directions.
"""

import pandas as pd
import numpy as np
from latam_hybrid.core import SectorManagementConfig
from latam_hybrid.wind.sector_management import (
    is_direction_in_sectors,
    calculate_sector_availability,
    get_sector_statistics
)


def demo_basic_sector_config():
    """Demonstrate basic sector management configuration."""
    print("=" * 70)
    print("Demo 1: Basic Sector Management Configuration")
    print("=" * 70)

    # Example: Turbines 1,3,5,7,9,12 restricted to 60-120° and 240-300°
    sector_config = SectorManagementConfig(
        turbine_sectors={
            1: [(60, 120), (240, 300)],
            3: [(60, 120), (240, 300)],
            5: [(60, 120), (240, 300)],
            7: [(60, 120), (240, 300)],
            9: [(60, 120), (240, 300)],
            12: [(60, 120), (240, 300)]
        },
        metadata={'reason': 'Noise restrictions from nearby residents'}
    )

    print("\nSector Configuration:")
    print(f"  Restricted turbines: {list(sector_config.turbine_sectors.keys())}")
    print(f"  Allowed sectors: {sector_config.turbine_sectors[1]}")
    print(f"  Reason: {sector_config.metadata.get('reason', 'N/A')}")

    print("\nInterpretation:")
    print("  ✅ Turbines RUN when wind is 60-120° or 240-300°")
    print("  ❌ Turbines STOP when wind is 0-60°, 120-240°, or 300-360°")
    print()


def demo_direction_checking():
    """Demonstrate wind direction checking."""
    print("=" * 70)
    print("Demo 2: Wind Direction Checking")
    print("=" * 70)

    sectors = [(60, 120), (240, 300)]

    print("\nAllowed sectors:", sectors)
    print("\nChecking various wind directions:")
    print("-" * 70)

    test_directions = [0, 45, 60, 90, 120, 150, 180, 240, 270, 300, 330, 360]

    for wd in test_directions:
        is_allowed = is_direction_in_sectors(wd, sectors)
        status = "✅ RUN" if is_allowed else "❌ STOP"
        print(f"  Wind @ {wd:3d}°: {status}")

    print()


def demo_availability_calculation():
    """Demonstrate availability calculation from wind data."""
    print("=" * 70)
    print("Demo 3: Availability Calculation from Wind Data")
    print("=" * 70)

    # Create sample wind data (one year hourly)
    np.random.seed(42)
    hours = 8760
    wind_data = pd.DataFrame({
        'wd': np.random.uniform(0, 360, hours)  # Random wind directions
    })

    # Calculate availability for different sector configurations
    configs = {
        'Restrictive (60-120° only)': {
            1: [(60, 120)]
        },
        'Moderate (60-120°, 240-300°)': {
            1: [(60, 120), (240, 300)]
        },
        'Permissive (0-180°)': {
            1: [(0, 180)]
        }
    }

    print("\nWind data: 8760 hours (1 year)")
    print("\nAvailability comparison:")
    print("-" * 70)

    for config_name, turbine_sectors in configs.items():
        availability = calculate_sector_availability(wind_data, turbine_sectors)
        avail_pct = availability[1] * 100
        hours_allowed = availability[1] * hours
        hours_stopped = (1 - availability[1]) * hours

        print(f"\n{config_name}:")
        print(f"  Availability: {avail_pct:.1f}%")
        print(f"  Running: {hours_allowed:.0f} hours/year")
        print(f"  Stopped: {hours_stopped:.0f} hours/year")

    print()


def demo_sector_statistics():
    """Demonstrate detailed sector statistics."""
    print("=" * 70)
    print("Demo 4: Detailed Sector Statistics")
    print("=" * 70)

    # Create realistic wind data with prevailing direction
    np.random.seed(42)
    hours = 8760

    # Simulate wind rose with prevailing southwest (225°)
    wind_data = pd.DataFrame({
        'wd': np.random.normal(225, 60, hours) % 360
    })

    # Sector configuration
    turbine_sectors = {
        1: [(60, 120), (240, 300)],   # Partial overlap with prevailing wind
        3: [(180, 270)]               # Good overlap with prevailing wind
    }

    print("\nWind rose: Prevailing wind from Southwest (~225°)")
    print("\nTurbine configurations:")
    print("  Turbine 1: Allowed 60-120° and 240-300°")
    print("  Turbine 3: Allowed 180-270°")

    stats = get_sector_statistics(wind_data, turbine_sectors)

    print("\nDetailed Statistics:")
    print("-" * 70)

    for turbine_id, stat in stats.items():
        print(f"\nTurbine {turbine_id}:")
        print(f"  Availability:    {stat['availability']*100:6.2f}%")
        print(f"  Curtailment:     {stat['curtailment']*100:6.2f}%")
        print(f"  Running hours:   {stat['allowed_hours_per_year']:6.0f} hrs/year")
        print(f"  Stopped hours:   {stat['stopped_hours_per_year']:6.0f} hrs/year")

    print()


def demo_energy_loss_estimation():
    """Demonstrate energy loss estimation from sector management."""
    print("=" * 70)
    print("Demo 5: Energy Loss Estimation")
    print("=" * 70)

    # Simulate wind farm
    np.random.seed(42)
    hours = 8760
    wind_data = pd.DataFrame({
        'wd': np.random.uniform(0, 360, hours)
    })

    # Sector configuration
    turbine_sectors = {
        1: [(60, 120), (240, 300)],
        3: [(60, 120), (240, 300)],
        5: [(60, 120), (240, 300)]
    }

    # Calculate availability
    availability = calculate_sector_availability(wind_data, turbine_sectors)

    # Assumptions
    turbine_capacity_mw = 5.0  # 5 MW turbine
    capacity_factor_base = 0.40  # 40% CF without curtailment
    n_restricted_turbines = len(turbine_sectors)
    n_total_turbines = 13

    print("\nWind Farm Configuration:")
    print(f"  Total turbines: {n_total_turbines}")
    print(f"  Restricted turbines: {n_restricted_turbines} (turbines {list(turbine_sectors.keys())})")
    print(f"  Turbine capacity: {turbine_capacity_mw} MW")
    print(f"  Base capacity factor: {capacity_factor_base*100:.1f}%")

    # Calculate energy loss
    avg_availability = np.mean(list(availability.values()))
    base_aep_per_turbine = turbine_capacity_mw * 8760 / 1000 * capacity_factor_base  # GWh

    # Unrestricted turbines
    n_unrestricted = n_total_turbines - n_restricted_turbines
    aep_unrestricted = n_unrestricted * base_aep_per_turbine

    # Restricted turbines
    aep_restricted_actual = n_restricted_turbines * base_aep_per_turbine * avg_availability
    aep_restricted_potential = n_restricted_turbines * base_aep_per_turbine
    energy_lost = aep_restricted_potential - aep_restricted_actual

    # Total
    total_aep_with_sectors = aep_unrestricted + aep_restricted_actual
    total_aep_no_sectors = n_total_turbines * base_aep_per_turbine
    sector_loss_pct = (energy_lost / total_aep_no_sectors) * 100

    print("\nEnergy Production Analysis:")
    print("-" * 70)
    print(f"  Average availability (restricted turbines): {avg_availability*100:.1f}%")
    print(f"\n  Unrestricted turbines ({n_unrestricted}):")
    print(f"    AEP: {aep_unrestricted:.2f} GWh/year")
    print(f"\n  Restricted turbines ({n_restricted_turbines}):")
    print(f"    Potential AEP: {aep_restricted_potential:.2f} GWh/year")
    print(f"    Actual AEP:    {aep_restricted_actual:.2f} GWh/year")
    print(f"    Energy lost:   {energy_lost:.2f} GWh/year")
    print(f"\n  Total Wind Farm:")
    print(f"    AEP (no sectors):   {total_aep_no_sectors:.2f} GWh/year")
    print(f"    AEP (with sectors): {total_aep_with_sectors:.2f} GWh/year")
    print(f"    Sector loss:        {sector_loss_pct:.2f}%")

    # Revenue impact
    electricity_price = 50  # USD/MWh
    revenue_lost = energy_lost * 1000 * electricity_price

    print(f"\nRevenue Impact (@ ${electricity_price}/MWh):")
    print(f"  Annual revenue lost: ${revenue_lost:,.0f}")
    print(f"  20-year project loss: ${revenue_lost * 20:,.0f}")

    print()


def demo_different_sectors_per_turbine():
    """Demonstrate different sector configurations per turbine."""
    print("=" * 70)
    print("Demo 6: Different Sectors Per Turbine")
    print("=" * 70)

    # Create wind data
    np.random.seed(42)
    hours = 8760
    wind_data = pd.DataFrame({
        'wd': np.random.uniform(0, 360, hours)
    })

    # Different sectors per turbine
    turbine_sectors = {
        1: [(60, 120), (240, 300)],    # Northeast and Southwest
        3: [(0, 90)],                   # North to East only
        5: [(180, 270)],                # South to West only
        7: [(90, 180), (270, 360)]     # East to South, West to North
    }

    print("\nTurbine Configurations:")
    for tid, sectors in turbine_sectors.items():
        print(f"  Turbine {tid}: {sectors}")

    availability = calculate_sector_availability(wind_data, turbine_sectors)

    print("\nAvailability Results:")
    print("-" * 70)
    for tid in sorted(turbine_sectors.keys()):
        avail_pct = availability[tid] * 100
        print(f"  Turbine {tid}: {avail_pct:.1f}% available ({availability[tid]*8760:.0f} hrs/year)")

    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  Wind Turbine Sector Management - Demonstration".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")

    demo_basic_sector_config()
    demo_direction_checking()
    demo_availability_calculation()
    demo_sector_statistics()
    demo_energy_loss_estimation()
    demo_different_sectors_per_turbine()

    print("=" * 70)
    print("All demonstrations completed successfully!")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Sector management stops turbines when wind from prohibited directions")
    print("  2. Each turbine can have different allowed sector ranges")
    print("  3. Availability = % of time wind is in allowed sectors")
    print("  4. Sector losses calculated via comparative simulation")
    print("  5. Use SectorManagementConfig to configure in your code")
    print()


if __name__ == '__main__':
    main()
