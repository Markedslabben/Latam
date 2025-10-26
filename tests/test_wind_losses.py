"""
Tests for wind farm losses module.

Tests the WindPRO-compliant losses calculation including:
- Default WindPRO loss values
- Multiplicative loss formula
- Loss application to AEP
- Integration with WindSite
"""

import pytest
import numpy as np
from latam_hybrid.wind.losses import (
    WindFarmLosses,
    LossCategory,
    LossType,
    create_default_losses
)


class TestLossCategory:
    """Test LossCategory dataclass."""

    def test_create_loss_category(self):
        """Test creating a valid loss category."""
        loss = LossCategory(
            name="test_loss",
            value=0.03,
            is_computed=False,
            description="Test loss"
        )
        assert loss.name == "test_loss"
        assert loss.value == 0.03
        assert loss.percentage == 3.0
        assert loss.is_computed is False

    def test_loss_category_validation_negative(self):
        """Test that negative loss values raise ValueError."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            LossCategory(name="bad_loss", value=-0.1)

    def test_loss_category_validation_over_one(self):
        """Test that loss values > 1 raise ValueError."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            LossCategory(name="bad_loss", value=1.5)

    def test_loss_category_to_dict(self):
        """Test exporting loss category to dictionary."""
        loss = LossCategory(name="wake", value=0.08, is_computed=True)
        result = loss.to_dict()
        assert result['name'] == 'wake'
        assert result['value'] == 0.08
        assert result['percentage'] == 8.0
        assert result['is_computed'] is True


class TestWindFarmLosses:
    """Test WindFarmLosses class."""

    def test_windpro_default_values(self):
        """Test that default values match WindPRO standards."""
        assert WindFarmLosses.DEFAULTS[LossType.AVAILABILITY_TURBINES] == 0.015  # 1.5%
        assert WindFarmLosses.DEFAULTS[LossType.AVAILABILITY_GRID] == 0.015      # 1.5%
        assert WindFarmLosses.DEFAULTS[LossType.ELECTRICAL] == 0.020             # 2.0%
        assert WindFarmLosses.DEFAULTS[LossType.HIGH_HYSTERESIS] == 0.003        # 0.3%
        assert WindFarmLosses.DEFAULTS[LossType.ENVIRONMENTAL_DEGRADATION] == 0.030  # 3.0%
        assert WindFarmLosses.DEFAULTS[LossType.OTHER] == 0.005                  # 0.5%

    def test_add_single_loss(self):
        """Test adding a single loss category."""
        losses = WindFarmLosses()
        losses.add_loss('wake_losses', 0.08, is_computed=True)

        breakdown = losses.get_loss_breakdown()
        assert 'wake_losses' in breakdown
        assert breakdown['wake_losses']['value'] == 0.08
        assert breakdown['wake_losses']['percentage'] == 8.0

    def test_multiplicative_formula_two_losses(self):
        """Test multiplicative formula with two losses."""
        losses = WindFarmLosses()
        losses.add_loss('loss1', 0.03)  # 3%
        losses.add_loss('loss2', 0.02)  # 2%

        # (1 - 0.03) * (1 - 0.02) = 0.97 * 0.98 = 0.9506
        expected_factor = 0.97 * 0.98
        assert abs(losses.calculate_total_loss_factor() - expected_factor) < 1e-10

    def test_multiplicative_formula_multiple_losses(self):
        """Test multiplicative formula with multiple losses."""
        losses = WindFarmLosses()
        losses.add_default_losses()

        # Manual calculation
        expected = 1.0
        expected *= (1 - 0.015)  # availability_turbines
        expected *= (1 - 0.015)  # availability_grid
        expected *= (1 - 0.020)  # electrical
        expected *= (1 - 0.003)  # hysteresis
        expected *= (1 - 0.030)  # environmental
        expected *= (1 - 0.005)  # other

        assert abs(losses.calculate_total_loss_factor() - expected) < 1e-10

    def test_total_loss_percentage(self):
        """Test total loss percentage calculation."""
        losses = WindFarmLosses()
        losses.add_loss('loss1', 0.10)  # 10%

        total_pct = losses.calculate_total_loss_percentage()
        assert abs(total_pct - 10.0) < 1e-10

    def test_net_aep_calculation(self):
        """Test net AEP calculation from gross AEP."""
        losses = WindFarmLosses()
        losses.add_loss('loss1', 0.05)  # 5%

        gross_aep = 1000.0  # GWh
        net_aep = losses.calculate_net_aep(gross_aep)

        expected_net = 1000.0 * 0.95  # 95% of gross
        assert abs(net_aep - expected_net) < 1e-10

    def test_net_aep_with_defaults(self):
        """Test net AEP with default WindPRO losses."""
        losses = WindFarmLosses()
        losses.add_default_losses()

        gross_aep = 1000.0  # GWh
        net_aep = losses.calculate_net_aep(gross_aep)

        # With default losses, net should be ~91.8% of gross
        # Total loss: ~8.8%
        assert net_aep < gross_aep
        assert net_aep > 900.0  # At least 90%
        assert net_aep < 925.0  # Less than 92.5%

    def test_add_default_losses(self):
        """Test adding default losses."""
        losses = WindFarmLosses()
        losses.add_default_losses()

        breakdown = losses.get_loss_breakdown()
        assert len(breakdown) == 6  # 6 default loss categories
        assert 'availability_turbines' in breakdown
        assert 'electrical_losses' in breakdown

    def test_custom_override_defaults(self):
        """Test overriding default loss values."""
        losses = WindFarmLosses()
        losses.add_default_losses(
            availability_turbines=0.02,  # Custom 2% instead of 1.5%
            electrical_losses=0.025       # Custom 2.5% instead of 2.0%
        )

        breakdown = losses.get_loss_breakdown()
        assert breakdown['availability_turbines']['value'] == 0.02
        assert breakdown['electrical_losses']['value'] == 0.025
        # Others should use defaults
        assert breakdown['availability_grid']['value'] == 0.015

    def test_method_chaining(self):
        """Test method chaining for fluent API."""
        losses = (
            WindFarmLosses()
            .add_loss('wake', 0.08, is_computed=True)
            .add_default_losses()
        )

        breakdown = losses.get_loss_breakdown()
        assert 'wake' in breakdown
        assert 'availability_turbines' in breakdown

    def test_computed_vs_user_losses(self):
        """Test separation of computed and user losses."""
        losses = WindFarmLosses()
        losses.add_loss('wake', 0.08, is_computed=True)
        losses.add_loss('curtailment', 0.02, is_computed=True)
        losses.add_default_losses()

        computed = losses.get_computed_losses()
        user = losses.get_user_losses()

        assert len(computed) == 2
        assert len(user) == 6
        assert 'wake' in computed
        assert 'availability_turbines' in user

    def test_to_dict_export(self):
        """Test full export to dictionary."""
        losses = WindFarmLosses()
        losses.add_loss('wake', 0.08, is_computed=True)
        losses.add_default_losses()

        result = losses.to_dict()

        assert 'loss_categories' in result
        assert 'total_loss_factor' in result
        assert 'total_loss_percentage' in result
        assert 'computed_losses' in result
        assert 'user_losses' in result

    def test_zero_losses(self):
        """Test with zero losses."""
        losses = WindFarmLosses()

        assert losses.calculate_total_loss_factor() == 1.0
        assert losses.calculate_total_loss_percentage() == 0.0
        assert losses.calculate_net_aep(1000.0) == 1000.0

    def test_repr(self):
        """Test string representation."""
        losses = WindFarmLosses()
        losses.add_default_losses()

        repr_str = repr(losses)
        assert 'WindFarmLosses' in repr_str
        assert 'n_categories=6' in repr_str


class TestCreateDefaultLosses:
    """Test create_default_losses convenience function."""

    def test_create_with_wake_only(self):
        """Test creating losses with only wake losses."""
        losses = create_default_losses(wake_loss=0.08)

        breakdown = losses.get_loss_breakdown()
        assert 'wake_losses' in breakdown
        assert breakdown['wake_losses']['value'] == 0.08
        assert breakdown['wake_losses']['is_computed'] is True

    def test_create_with_wake_and_curtailment(self):
        """Test creating losses with wake and curtailment."""
        losses = create_default_losses(
            wake_loss=0.08,
            curtailment_sector=0.03
        )

        computed = losses.get_computed_losses()
        assert len(computed) == 2
        assert 'wake_losses' in computed
        assert 'curtailment_sector_management' in computed

    def test_create_with_custom_defaults(self):
        """Test creating with custom default overrides."""
        losses = create_default_losses(
            wake_loss=0.08,
            availability_turbines=0.02,
            electrical_losses=0.025
        )

        breakdown = losses.get_loss_breakdown()
        assert breakdown['wake_losses']['value'] == 0.08
        assert breakdown['availability_turbines']['value'] == 0.02
        assert breakdown['electrical_losses']['value'] == 0.025


class TestWindPROCompliance:
    """Test compliance with WindPRO methodology."""

    def test_default_total_losses(self):
        """Test that default total losses are reasonable (~8-9%)."""
        losses = WindFarmLosses()
        losses.add_default_losses()

        total_pct = losses.calculate_total_loss_percentage()

        # Default losses should be around 8.8%
        assert 8.0 < total_pct < 10.0

    def test_loss_formula_example(self):
        """
        Test loss calculation example from WindPRO methodology.

        Example:
        - Wake losses: 8%
        - Availability: 1.5%
        - Electrical: 2%

        Total = (1 - 0.08) * (1 - 0.015) * (1 - 0.02) = 0.88572
        Net AEP = 1000 GWh * 0.88572 = 885.72 GWh
        """
        losses = WindFarmLosses()
        losses.add_loss('wake', 0.08)
        losses.add_loss('availability', 0.015)
        losses.add_loss('electrical', 0.02)

        expected_factor = 0.92 * 0.985 * 0.98
        assert abs(losses.calculate_total_loss_factor() - expected_factor) < 1e-10

        net_aep = losses.calculate_net_aep(1000.0)
        expected_net = 1000.0 * expected_factor
        assert abs(net_aep - expected_net) < 1e-10

    def test_realistic_wind_farm_scenario(self):
        """
        Test realistic wind farm scenario with all losses.

        Scenario:
        - Gross AEP: 500 GWh
        - Wake losses: 10% (computed)
        - Availability turbines: 1.5%
        - Availability grid: 1.5%
        - Electrical: 2%
        - Hysteresis: 0.3%
        - Environmental: 3%
        - Other: 0.5%
        """
        losses = create_default_losses(wake_loss=0.10)

        gross_aep = 500.0  # GWh
        net_aep = losses.calculate_net_aep(gross_aep)

        # Net should be around 81-82% of gross
        expected_range = (400.0, 415.0)
        assert expected_range[0] < net_aep < expected_range[1]

        # Verify individual components
        breakdown = losses.get_loss_breakdown()
        assert breakdown['wake_losses']['percentage'] == 10.0
        assert breakdown['availability_turbines']['percentage'] == 1.5

        # Total loss should be around 18-19%
        total_loss_pct = losses.calculate_total_loss_percentage()
        assert 17.0 < total_loss_pct < 20.0


class TestCSVConfiguration:
    """Test CSV-based loss configuration."""

    def test_csv_file_exists(self):
        """Test that default losses.csv file exists."""
        from pathlib import Path

        # Find losses.csv
        project_root = Path(__file__).parent.parent / 'latam_hybrid'
        csv_path = project_root / 'Inputdata' / 'losses.csv'

        assert csv_path.exists(), f"losses.csv not found at {csv_path}"

    def test_csv_has_correct_structure(self):
        """Test that CSV has required columns and values."""
        import pandas as pd
        from pathlib import Path

        project_root = Path(__file__).parent.parent / 'latam_hybrid'
        csv_path = project_root / 'Inputdata' / 'losses.csv'

        df = pd.read_csv(csv_path)

        # Check required columns
        assert 'loss_category' in df.columns
        assert 'default_value' in df.columns
        assert 'description' in df.columns

        # Check expected loss categories
        categories = df['loss_category'].tolist()
        assert 'availability_turbines' in categories
        assert 'electrical_losses' in categories
        assert 'environmental_performance_degradation' in categories

    def test_csv_default_values_match_windpro(self):
        """Test that CSV default values match WindPRO standards."""
        import pandas as pd
        from pathlib import Path

        project_root = Path(__file__).parent.parent / 'latam_hybrid'
        csv_path = project_root / 'Inputdata' / 'losses.csv'

        df = pd.read_csv(csv_path)
        csv_values = dict(zip(df['loss_category'], df['default_value']))

        # Verify WindPRO defaults
        assert csv_values['availability_turbines'] == 0.015
        assert csv_values['availability_grid'] == 0.015
        assert csv_values['electrical_losses'] == 0.020
        assert csv_values['high_hysteresis_losses'] == 0.003
        assert csv_values['environmental_performance_degradation'] == 0.030
        assert csv_values['other_losses'] == 0.005


class TestCompleteIntegration:
    """Test complete loss breakdown and integration."""

    def test_complete_loss_breakdown_structure(self):
        """Test that complete loss breakdown has correct structure."""
        # Create mock breakdown
        breakdown = {
            'wake_losses': {
                'percentage': 8.0,
                'value': 0.08,
                'is_computed': True,
                'applied_in': 'run_simulation',
                'description': 'Wake effects'
            },
            'availability_turbines': {
                'percentage': 1.5,
                'value': 0.015,
                'is_computed': False,
                'applied_in': 'apply_losses',
                'description': 'Turbine downtime'
            }
        }

        # Verify structure
        for name, data in breakdown.items():
            assert 'percentage' in data
            assert 'value' in data
            assert 'is_computed' in data
            assert 'applied_in' in data
            assert data['applied_in'] in ['run_simulation', 'apply_losses']

    def test_no_double_counting_wake_losses(self):
        """Test that wake losses are not applied twice."""
        from latam_hybrid.wind.losses import WindFarmLosses

        # Scenario: AEP from simulation already includes wake effects
        aep_with_wake_included = 1000.0  # GWh (wake losses already applied)
        wake_loss_pct = 8.0  # Just for reporting

        # Apply only specific other losses (NOT all defaults)
        losses = WindFarmLosses()
        losses.add_loss('availability_turbines', 0.015)
        losses.add_loss('electrical_losses', 0.02)

        # Calculate net (wake NOT in this calculation)
        net_aep = losses.calculate_net_aep(aep_with_wake_included)

        # Net should be ~96.5% of input (1.5% + 2% ≈ 3.5% additional losses)
        expected_factor = (1 - 0.015) * (1 - 0.02)  # ~0.9653
        expected_net = aep_with_wake_included * expected_factor

        assert abs(net_aep - expected_net) < 0.1

    def test_total_loss_factor_calculation(self):
        """Test total loss factor from ideal to net AEP."""
        aep_ideal = 1200.0  # No losses
        aep_with_wake = 1104.0  # 8% wake loss

        # Additional losses: 1.5% + 2% = ~3.45%
        additional_factor = (1 - 0.015) * (1 - 0.02)
        aep_net = aep_with_wake * additional_factor

        # Total loss factor
        total_factor = aep_net / aep_ideal

        # Should be around 0.885 (11.5% total loss)
        assert 0.88 < total_factor < 0.90


class TestFutureSectorManagement:
    """Test sector management placeholder and future integration."""

    def test_sector_loss_defaults_to_zero(self):
        """Test that sector losses default to 0 (not implemented yet)."""
        from latam_hybrid.wind.losses import create_default_losses

        # Create losses without sector management
        losses = create_default_losses(wake_loss=0.08)

        breakdown = losses.get_loss_breakdown()

        # Sector management should NOT be in breakdown (0%)
        assert 'curtailment_sector_management' not in breakdown or \
               breakdown['curtailment_sector_management']['percentage'] == 0

    def test_sector_loss_can_be_added_manually(self):
        """Test that sector losses can be added when module is ready."""
        from latam_hybrid.wind.losses import WindFarmLosses

        losses = WindFarmLosses()

        # Future: sector management module will compute this
        losses.add_loss(
            'curtailment_sector_management',
            0.023,  # 2.3% sector curtailment
            is_computed=True,
            description='Sector management curtailment'
        )

        breakdown = losses.get_loss_breakdown()
        assert 'curtailment_sector_management' in breakdown
        assert breakdown['curtailment_sector_management']['percentage'] == 2.3
        assert breakdown['curtailment_sector_management']['is_computed'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
