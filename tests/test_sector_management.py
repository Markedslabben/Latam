"""
Tests for wind turbine sector management functionality.

Tests sector curtailment where turbines are stopped when wind comes from
prohibited directions.
"""

import pytest
import pandas as pd
import numpy as np
from latam_hybrid.core.data_models import SectorManagementConfig
from latam_hybrid.wind.sector_management import (
    is_direction_in_sectors,
    calculate_sector_availability,
    validate_sector_ranges,
    create_sector_mask,
    get_sector_statistics
)


class TestSectorValidation:
    """Test sector range validation."""

    def test_valid_single_sector(self):
        """Test validation with single valid sector."""
        sectors = [(60, 120)]
        validate_sector_ranges(sectors)  # Should not raise

    def test_valid_multiple_sectors(self):
        """Test validation with multiple valid sectors."""
        sectors = [(60, 120), (240, 300)]
        validate_sector_ranges(sectors)  # Should not raise

    def test_invalid_start_greater_than_end(self):
        """Test that start > end raises error."""
        sectors = [(120, 60)]
        with pytest.raises(ValueError, match="Sector start must be <= end"):
            validate_sector_ranges(sectors)

    def test_invalid_negative_angle(self):
        """Test that negative angles raise error."""
        sectors = [(-10, 60)]
        with pytest.raises(ValueError, match="must be in \\[0, 360\\]"):
            validate_sector_ranges(sectors)

    def test_invalid_angle_over_360(self):
        """Test that angles > 360 raise error."""
        sectors = [(60, 370)]
        with pytest.raises(ValueError, match="must be in \\[0, 360\\]"):
            validate_sector_ranges(sectors)

    def test_invalid_empty_sectors(self):
        """Test that empty sector list raises error."""
        with pytest.raises(ValueError, match="must be a non-empty list"):
            validate_sector_ranges([])

    def test_edge_case_0_to_360(self):
        """Test edge case of 0-360 degree sector."""
        sectors = [(0, 360)]
        validate_sector_ranges(sectors)  # Should not raise


class TestDirectionChecking:
    """Test wind direction checking against sectors."""

    def test_direction_in_single_sector(self):
        """Test direction within single allowed sector."""
        sectors = [(60, 120)]
        assert is_direction_in_sectors(90, sectors) is True
        assert is_direction_in_sectors(60, sectors) is True
        assert is_direction_in_sectors(120, sectors) is True

    def test_direction_outside_single_sector(self):
        """Test direction outside single allowed sector."""
        sectors = [(60, 120)]
        assert is_direction_in_sectors(45, sectors) is False
        assert is_direction_in_sectors(150, sectors) is False
        assert is_direction_in_sectors(270, sectors) is False

    def test_direction_in_multiple_sectors(self):
        """Test direction in any of multiple sectors."""
        sectors = [(60, 120), (240, 300)]

        # In first sector
        assert is_direction_in_sectors(90, sectors) is True

        # In second sector
        assert is_direction_in_sectors(270, sectors) is True

        # Between sectors
        assert is_direction_in_sectors(180, sectors) is False

        # Before first sector
        assert is_direction_in_sectors(30, sectors) is False

        # After second sector
        assert is_direction_in_sectors(330, sectors) is False

    def test_direction_normalization(self):
        """Test that directions are properly normalized to [0, 360)."""
        sectors = [(60, 120)]

        # Test 360 wraps to 0
        assert is_direction_in_sectors(360, sectors) is False

        # Test negative values wrap
        assert is_direction_in_sectors(-10, sectors) is False

    def test_edge_directions(self):
        """Test directions at sector boundaries."""
        sectors = [(60, 120), (240, 300)]

        # At boundaries (inclusive)
        assert is_direction_in_sectors(60, sectors) is True
        assert is_direction_in_sectors(120, sectors) is True
        assert is_direction_in_sectors(240, sectors) is True
        assert is_direction_in_sectors(300, sectors) is True

        # Just outside boundaries
        assert is_direction_in_sectors(59, sectors) is False
        assert is_direction_in_sectors(121, sectors) is False
        assert is_direction_in_sectors(239, sectors) is False
        assert is_direction_in_sectors(301, sectors) is False


class TestAvailabilityCalculation:
    """Test sector availability calculation from wind data."""

    def test_simple_availability(self):
        """Test availability calculation with known wind data."""
        # Create wind data: 5 timestamps, 2 in allowed sectors
        wind_data = pd.DataFrame({
            'wd': [45, 90, 150, 270, 330]  # 90° and 270° are in [(60,120), (240,300)]
        })

        turbine_sectors = {
            1: [(60, 120), (240, 300)]
        }

        availability = calculate_sector_availability(wind_data, turbine_sectors)

        assert 1 in availability
        assert availability[1] == pytest.approx(0.4, rel=0.01)  # 2/5 = 40%

    def test_full_availability(self):
        """Test 100% availability when all wind in allowed sectors."""
        wind_data = pd.DataFrame({
            'wd': [70, 80, 90, 100, 110]  # All in (60, 120)
        })

        turbine_sectors = {
            1: [(60, 120)]
        }

        availability = calculate_sector_availability(wind_data, turbine_sectors)
        assert availability[1] == pytest.approx(1.0, rel=0.01)

    def test_zero_availability(self):
        """Test 0% availability when no wind in allowed sectors."""
        wind_data = pd.DataFrame({
            'wd': [0, 30, 150, 180, 330]  # None in [(60,120), (240,300)]
        })

        turbine_sectors = {
            1: [(60, 120), (240, 300)]
        }

        availability = calculate_sector_availability(wind_data, turbine_sectors)
        assert availability[1] == pytest.approx(0.0, rel=0.01)

    def test_multiple_turbines(self):
        """Test availability calculation for multiple turbines."""
        wind_data = pd.DataFrame({
            'wd': [45, 90, 150, 270, 330]
        })

        turbine_sectors = {
            1: [(60, 120), (240, 300)],  # 40% (90, 270)
            3: [(0, 60), (300, 360)]     # 40% (45, 330)
        }

        availability = calculate_sector_availability(wind_data, turbine_sectors)

        assert 1 in availability
        assert 3 in availability
        assert availability[1] == pytest.approx(0.4, rel=0.01)
        assert availability[3] == pytest.approx(0.4, rel=0.01)

    def test_different_availabilities(self):
        """Test different availabilities for different turbines."""
        wind_data = pd.DataFrame({
            'wd': [70, 80, 90, 100, 110]  # All in (60, 120)
        })

        turbine_sectors = {
            1: [(60, 120)],      # 100% available
            2: [(240, 300)]      # 0% available
        }

        availability = calculate_sector_availability(wind_data, turbine_sectors)
        assert availability[1] == pytest.approx(1.0, rel=0.01)
        assert availability[2] == pytest.approx(0.0, rel=0.01)

    def test_missing_wd_column(self):
        """Test error when wind data missing 'wd' column."""
        wind_data = pd.DataFrame({
            'ws': [5, 6, 7, 8, 9]  # No 'wd' column
        })

        turbine_sectors = {1: [(60, 120)]}

        with pytest.raises(ValueError, match="must contain 'wd'"):
            calculate_sector_availability(wind_data, turbine_sectors)


class TestSectorMask:
    """Test sector mask creation."""

    def test_simple_mask(self):
        """Test mask creation for simple case."""
        wind_dirs = np.array([45, 90, 150, 270])
        turbine_sectors = {1: [(60, 120), (240, 300)]}
        n_turbines = 2

        mask = create_sector_mask(wind_dirs, turbine_sectors, n_turbines)

        # Shape should be (n_timesteps, n_turbines)
        assert mask.shape == (4, 2)

        # Turbine 1 (index 0) mask: [False, True, False, True]
        np.testing.assert_array_equal(mask[:, 0], [False, True, False, True])

        # Turbine 2 (index 1) has no restrictions: all True
        np.testing.assert_array_equal(mask[:, 1], [True, True, True, True])

    def test_all_turbines_restricted(self):
        """Test mask when all turbines have restrictions."""
        wind_dirs = np.array([90, 270])
        turbine_sectors = {
            1: [(60, 120)],     # First timestep only
            2: [(240, 300)]     # Second timestep only
        }
        n_turbines = 2

        mask = create_sector_mask(wind_dirs, turbine_sectors, n_turbines)

        np.testing.assert_array_equal(mask[:, 0], [True, False])
        np.testing.assert_array_equal(mask[:, 1], [False, True])

    def test_invalid_turbine_id(self):
        """Test error when turbine ID out of range."""
        wind_dirs = np.array([90])
        turbine_sectors = {5: [(60, 120)]}  # Turbine 5, but only 2 turbines
        n_turbines = 2

        with pytest.raises(ValueError, match="out of range"):
            create_sector_mask(wind_dirs, turbine_sectors, n_turbines)


class TestSectorStatistics:
    """Test sector statistics calculation."""

    def test_basic_statistics(self):
        """Test statistics calculation."""
        wind_data = pd.DataFrame({
            'wd': [45, 90, 150, 270, 330, 60, 250, 180, 100, 280]  # 10 hours
        })

        turbine_sectors = {
            1: [(60, 120), (240, 300)]  # 90, 270, 60, 250, 100, 280 = 6/10 = 60%
        }

        stats = get_sector_statistics(wind_data, turbine_sectors)

        assert 1 in stats
        assert stats[1]['availability'] == pytest.approx(0.6, rel=0.01)
        assert stats[1]['curtailment'] == pytest.approx(0.4, rel=0.01)
        assert stats[1]['allowed_hours_per_year'] == pytest.approx(6.0, rel=0.01)
        assert stats[1]['stopped_hours_per_year'] == pytest.approx(4.0, rel=0.01)


class TestSectorManagementConfig:
    """Test SectorManagementConfig dataclass."""

    def test_valid_config(self):
        """Test creating valid configuration."""
        config = SectorManagementConfig(
            turbine_sectors={
                1: [(60, 120), (240, 300)],
                3: [(60, 120), (240, 300)]
            },
            metadata={'reason': 'Noise restrictions'}
        )

        assert config.turbine_sectors[1] == [(60, 120), (240, 300)]
        assert config.metadata['reason'] == 'Noise restrictions'

    def test_invalid_turbine_id_zero(self):
        """Test that turbine ID must be positive."""
        with pytest.raises(ValueError, match="positive integer"):
            SectorManagementConfig(
                turbine_sectors={0: [(60, 120)]}
            )

    def test_invalid_turbine_id_negative(self):
        """Test that turbine ID cannot be negative."""
        with pytest.raises(ValueError, match="positive integer"):
            SectorManagementConfig(
                turbine_sectors={-1: [(60, 120)]}
            )

    def test_invalid_empty_sectors(self):
        """Test that sectors cannot be empty."""
        with pytest.raises(ValueError, match="at least one sector range"):
            SectorManagementConfig(
                turbine_sectors={1: []}
            )

    def test_invalid_sector_angles(self):
        """Test that sector angles must be in valid range."""
        with pytest.raises(ValueError, match="must be in \\[0, 360\\]"):
            SectorManagementConfig(
                turbine_sectors={1: [(60, 400)]}
            )

    def test_invalid_sector_order(self):
        """Test that start must be <= end."""
        with pytest.raises(ValueError, match="start must be <= end"):
            SectorManagementConfig(
                turbine_sectors={1: [(120, 60)]}
            )
