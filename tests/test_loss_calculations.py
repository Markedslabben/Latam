"""
Unit tests for wind farm loss calculations.

Tests verify correctness of:
- Per-turbine wake loss calculations
- Energy-based sector management losses
- Other losses (availability, electrical, etc.)
- Loss cascade integrity
"""

import pytest
import numpy as np
from pathlib import Path


@pytest.fixture
def simulation_result():
    """
    Fixture providing a WindSimulationResult with test data.

    Uses actual simulation with year 2020 data for realistic validation.
    """
    import sys
    from latam_hybrid.wind import WindSite
    from latam_hybrid.wind.turbine import TurbineModel
    from latam_hybrid.wind.layout import TurbineLayout
    from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG
    from latam_hybrid.core.data_models import WindData
    import pandas as pd

    # File paths
    project_root = Path(__file__).parent.parent
    wind_data_path = project_root / "latam_hybrid" / "Inputdata" / "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    turbine_path = project_root / "latam_hybrid" / "Inputdata" / "Nordex N164.csv"
    layout_path = project_root / "latam_hybrid" / "Inputdata" / "Turbine_layout_13.csv"
    losses_path = project_root / "latam_hybrid" / "Inputdata" / "losses.csv"

    # Load turbine CSV
    turbine_df = pd.read_csv(turbine_path, header=None, names=['ws', 'power', 'ct'])
    temp_turbine_path = project_root / "tests" / "temp_nordex_n164.csv"
    turbine_df.to_csv(temp_turbine_path, index=False)

    # Load wind data
    site = WindSite.from_file(
        str(wind_data_path),
        source_type='vortex',
        height=164.0,
        skiprows=3,
        column_mapping={'ws': 'M(m/s)', 'wd': 'D(deg)'}
    )

    # Filter to year 2020 for testing
    ANALYSIS_YEAR = 2020
    years_from_2014 = ANALYSIS_YEAR - 2014
    start_idx = 4 + (years_from_2014 * 8760)
    leap_days = sum(1 for y in range(2014, ANALYSIS_YEAR)
                   if (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0))
    start_idx += leap_days * 24
    is_leap = ((ANALYSIS_YEAR % 4 == 0 and ANALYSIS_YEAR % 100 != 0) or
              (ANALYSIS_YEAR % 400 == 0))
    year_hours = 8784 if is_leap else 8760
    end_idx = start_idx + year_hours

    filtered_timeseries = site.wind_data.timeseries.iloc[start_idx:end_idx].copy()
    filtered_wind_data = WindData(
        timeseries=filtered_timeseries,
        height=site.wind_data.height,
        timezone_offset=site.wind_data.timezone_offset,
        source=site.wind_data.source,
        metadata=site.wind_data.metadata
    )
    object.__setattr__(site, 'wind_data', filtered_wind_data)

    # Run simulation
    result = (
        site
        .with_turbine(
            TurbineModel.from_csv(
                str(temp_turbine_path),
                name="Nordex N164",
                hub_height=164,
                rotor_diameter=164,
                rated_power=7000
            )
        )
        .set_layout(
            TurbineLayout.from_csv(
                str(layout_path),
                x_column='x_coord',
                y_column='y_coord',
                crs='EPSG:32719'
            )
        )
        .set_sector_management(SECTOR_MANAGEMENT_CONFIG)
        .run_simulation(
            wake_model='Bastankhah_Gaussian',
            simulation_method='timeseries',
            compute_losses=True
        )
        .apply_losses(loss_config_file=str(losses_path))
        .calculate_production()
    )

    # Cleanup
    temp_turbine_path.unlink()

    return result


class TestLossCascadeIntegrity:
    """Test that loss cascade sums correctly: ideal - wake - sector - other = net"""

    def test_loss_cascade_sum(self, simulation_result):
        """Verify loss cascade: ideal - wake - sector - other ≈ net"""
        ideal = np.array(simulation_result.metadata['ideal_per_turbine_gwh'])
        wake_loss = np.array(simulation_result.metadata['wake_loss_per_turbine_gwh'])
        sector_loss = np.array(simulation_result.metadata['sector_loss_per_turbine_gwh'])
        other_loss = np.array(simulation_result.metadata['other_loss_per_turbine_gwh'])
        net = np.array(simulation_result.turbine_production_gwh)

        # Calculate residual (should be near zero)
        residual = ideal - wake_loss - sector_loss - other_loss - net

        # Check maximum error is negligible (< 1e-6 GWh = 1 kWh)
        max_error = np.max(np.abs(residual))
        assert max_error < 1e-6, f"Loss cascade residual too large: {max_error:.9f} GWh"

    def test_total_farm_sum(self, simulation_result):
        """Verify farm totals match sum of per-turbine values"""
        net = np.array(simulation_result.turbine_production_gwh)
        farm_total = simulation_result.aep_gwh

        sum_of_turbines = net.sum()
        error = abs(sum_of_turbines - farm_total)

        assert error < 0.01, f"Farm total mismatch: {sum_of_turbines:.2f} vs {farm_total:.2f} GWh"


class TestOtherLossesCorrection:
    """Test that other losses are calculated correctly (not swapped)"""

    def test_other_losses_not_swapped(self, simulation_result):
        """Verify other losses are 8.8% of production before other losses, not 91.2%"""
        ideal = np.array(simulation_result.metadata['ideal_per_turbine_gwh'])
        wake_loss = np.array(simulation_result.metadata['wake_loss_per_turbine_gwh'])
        sector_loss = np.array(simulation_result.metadata['sector_loss_per_turbine_gwh'])
        other_loss = np.array(simulation_result.metadata['other_loss_per_turbine_gwh'])

        # Production before other losses
        production_before_other = ideal - wake_loss - sector_loss

        # Other losses should be ~8.8% of production before other losses
        expected_other_loss_pct = 8.8  # From losses.csv configuration
        actual_other_loss_pct = (other_loss.sum() / production_before_other.sum()) * 100

        # Allow 0.5% tolerance for rounding
        assert abs(actual_other_loss_pct - expected_other_loss_pct) < 0.5, \
            f"Other losses incorrect: {actual_other_loss_pct:.2f}% (expected ~{expected_other_loss_pct}%)"

    def test_net_production_reasonable(self, simulation_result):
        """Verify net production is ~91.2% of production before other losses (not 8.8%)"""
        ideal = np.array(simulation_result.metadata['ideal_per_turbine_gwh'])
        wake_loss = np.array(simulation_result.metadata['wake_loss_per_turbine_gwh'])
        sector_loss = np.array(simulation_result.metadata['sector_loss_per_turbine_gwh'])
        net = np.array(simulation_result.turbine_production_gwh)

        # Production before other losses
        production_before_other = ideal - wake_loss - sector_loss

        # Net should be ~91.2% of production before other losses
        expected_remaining_pct = 91.2  # 100% - 8.8% losses
        actual_remaining_pct = (net.sum() / production_before_other.sum()) * 100

        # Allow 0.5% tolerance
        assert abs(actual_remaining_pct - expected_remaining_pct) < 0.5, \
            f"Net production incorrect: {actual_remaining_pct:.2f}% (expected ~{expected_remaining_pct}%)"


class TestSectorManagementLosses:
    """Test energy-based sector management loss calculation"""

    def test_unrestricted_turbines_zero_sector_loss(self, simulation_result):
        """Verify unrestricted turbines have zero sector losses"""
        from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG

        sector_loss = np.array(simulation_result.metadata['sector_loss_per_turbine_gwh'])

        # Get list of unrestricted turbines (all turbines not in restriction list)
        all_turbines = set(range(1, 14))  # 1-13
        restricted_turbines = set(SECTOR_MANAGEMENT_CONFIG.turbine_sectors.keys())
        unrestricted_turbines = all_turbines - restricted_turbines

        for turbine_id in unrestricted_turbines:
            turbine_idx = turbine_id - 1
            assert sector_loss[turbine_idx] == 0.0, \
                f"Turbine {turbine_id} should have zero sector loss but has {sector_loss[turbine_idx]:.3f} GWh"

    def test_restricted_turbines_have_sector_loss(self, simulation_result):
        """Verify restricted turbines have non-zero sector losses"""
        from latam_hybrid.Inputdata.sector_config import SECTOR_MANAGEMENT_CONFIG

        sector_loss = np.array(simulation_result.metadata['sector_loss_per_turbine_gwh'])

        for turbine_id in SECTOR_MANAGEMENT_CONFIG.turbine_sectors.keys():
            turbine_idx = turbine_id - 1
            assert sector_loss[turbine_idx] > 0, \
                f"Restricted turbine {turbine_id} should have sector loss but has {sector_loss[turbine_idx]:.3f} GWh"

    def test_sector_loss_energy_based_not_time_based(self, simulation_result):
        """Verify sector losses use energy-based calculation (not time-based)"""
        # Energy-based calculation should give ~5-6% farm-level sector losses
        # Time-based would give ~12-13% (much higher)

        sector_loss_pct = simulation_result.sector_loss_percent

        # Energy-based should be in 4-8% range
        assert 4.0 <= sector_loss_pct <= 8.0, \
            f"Sector loss {sector_loss_pct:.2f}% outside expected range (4-8%) - may be using time-based calculation"

        # Definitely should NOT be > 10% (time-based range)
        assert sector_loss_pct < 10.0, \
            f"Sector loss {sector_loss_pct:.2f}% too high - likely using time-based calculation"


class TestWakeLosses:
    """Test wake loss calculations"""

    def test_wake_losses_vary_by_turbine(self, simulation_result):
        """Verify wake losses vary across turbines (position-dependent)"""
        wake_loss = np.array(simulation_result.metadata['wake_loss_per_turbine_gwh'])

        # Check that not all wake losses are identical
        wake_loss_std = np.std(wake_loss)
        assert wake_loss_std > 0.1, "Wake losses should vary by turbine position"

    def test_wake_losses_positive(self, simulation_result):
        """Verify all wake losses are positive (or zero)"""
        wake_loss = np.array(simulation_result.metadata['wake_loss_per_turbine_gwh'])

        assert np.all(wake_loss >= 0), "Wake losses cannot be negative"

    def test_wake_loss_farm_level(self, simulation_result):
        """Verify farm-level wake loss percentage matches sum of per-turbine"""
        ideal = np.array(simulation_result.metadata['ideal_per_turbine_gwh'])
        wake_loss = np.array(simulation_result.metadata['wake_loss_per_turbine_gwh'])

        farm_wake_pct = (wake_loss.sum() / ideal.sum()) * 100
        reported_wake_pct = simulation_result.wake_loss_percent

        # Allow 0.1% tolerance for rounding
        assert abs(farm_wake_pct - reported_wake_pct) < 0.1, \
            f"Farm wake loss mismatch: {farm_wake_pct:.2f}% vs {reported_wake_pct:.2f}%"


class TestCapacityFactor:
    """Test capacity factor calculations"""

    def test_capacity_factor_in_valid_range(self, simulation_result):
        """Verify capacity factor is between 0 and 1"""
        cf = simulation_result.capacity_factor

        assert 0 <= cf <= 1, f"Capacity factor {cf:.2f} outside valid range [0, 1]"

    def test_capacity_factor_calculation(self, simulation_result):
        """Verify capacity factor calculation is correct"""
        total_capacity_mw = simulation_result.metadata.get('total_capacity_mw', 91.0)
        aep_gwh = simulation_result.aep_gwh

        # CF = (GWh/yr × 1000 MWh/GWh) / (rated_power_MW × 8760 hr/yr)
        expected_cf = (aep_gwh * 1000) / (total_capacity_mw * 8760)
        actual_cf = simulation_result.capacity_factor

        # Allow 0.001 tolerance (0.1%)
        assert abs(actual_cf - expected_cf) < 0.001, \
            f"Capacity factor calculation error: {actual_cf:.4f} vs {expected_cf:.4f}"


class TestMetadataStructure:
    """Test that metadata contains required fields"""

    def test_metadata_contains_per_turbine_losses(self, simulation_result):
        """Verify metadata contains all required per-turbine loss arrays"""
        required_keys = [
            'ideal_per_turbine_gwh',
            'wake_loss_per_turbine_gwh',
            'sector_loss_per_turbine_gwh',
            'other_loss_per_turbine_gwh'
        ]

        for key in required_keys:
            assert key in simulation_result.metadata, f"Missing metadata key: {key}"

    def test_metadata_array_lengths(self, simulation_result):
        """Verify all per-turbine arrays have same length"""
        ideal = simulation_result.metadata['ideal_per_turbine_gwh']
        wake_loss = simulation_result.metadata['wake_loss_per_turbine_gwh']
        sector_loss = simulation_result.metadata['sector_loss_per_turbine_gwh']
        other_loss = simulation_result.metadata['other_loss_per_turbine_gwh']
        net = simulation_result.turbine_production_gwh

        n_turbines = len(net)

        assert len(ideal) == n_turbines, "Ideal production array length mismatch"
        assert len(wake_loss) == n_turbines, "Wake loss array length mismatch"
        assert len(sector_loss) == n_turbines, "Sector loss array length mismatch"
        assert len(other_loss) == n_turbines, "Other loss array length mismatch"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
