"""
Sector management utilities for wind turbine curtailment.

This module provides functions for managing wind turbine sector curtailment,
where turbines are stopped when wind comes from prohibited directions.
"""

from typing import List, Tuple, Dict
import pandas as pd
import numpy as np


def is_direction_in_sectors(
    wd: float,
    sectors: List[Tuple[float, float]]
) -> bool:
    """
    Check if wind direction falls within allowed sectors.

    Args:
        wd: Wind direction in degrees (0-360)
        sectors: List of allowed sector ranges as (start, end) tuples
                Example: [(60, 120), (240, 300)] means allowed in 60-120° and 240-300°

    Returns:
        True if wind direction is in any allowed sector (turbine runs)
        False if wind direction is in prohibited sectors (turbine stops)

    Example:
        >>> is_direction_in_sectors(90, [(60, 120), (240, 300)])
        True
        >>> is_direction_in_sectors(150, [(60, 120), (240, 300)])
        False
    """
    # Normalize wind direction to [0, 360)
    wd = wd % 360

    # Check if wd falls in any allowed sector
    for start, end in sectors:
        if start <= wd <= end:
            return True

    return False


def calculate_sector_availability(
    wind_data: pd.DataFrame,
    turbine_sectors: Dict[int, List[Tuple[float, float]]]
) -> Dict[int, float]:
    """
    Calculate availability (fraction of time turbines can operate) based on sector management.

    Uses actual wind direction time series to calculate the percentage of time
    each turbine is allowed to operate based on its sector restrictions.

    Args:
        wind_data: DataFrame with 'wd' (wind direction) column
        turbine_sectors: Dict mapping turbine_id to allowed sector ranges
                        Format: {turbine_id: [(start, end), ...]}

    Returns:
        Dict mapping turbine_id to availability fraction (0-1)
        Example: {1: 0.33, 3: 0.33} means turbines can run 33% of the time

    Example:
        >>> import pandas as pd
        >>> wind_data = pd.DataFrame({'wd': [45, 90, 150, 270, 330]})
        >>> sectors = {1: [(60, 120), (240, 300)]}
        >>> availability = calculate_sector_availability(wind_data, sectors)
        >>> availability[1]  # 2 out of 5 timestamps allowed
        0.4
    """
    if 'wd' not in wind_data.columns:
        raise ValueError("wind_data must contain 'wd' (wind direction) column")

    wind_directions = wind_data['wd'].values
    total_timesteps = len(wind_directions)

    availability = {}

    for turbine_id, sectors in turbine_sectors.items():
        # Count how many timesteps have wind in allowed sectors
        allowed_timesteps = sum(
            is_direction_in_sectors(wd, sectors)
            for wd in wind_directions
        )

        # Calculate availability fraction
        availability[turbine_id] = allowed_timesteps / total_timesteps if total_timesteps > 0 else 0.0

    return availability


def validate_sector_ranges(sectors: List[Tuple[float, float]]) -> None:
    """
    Validate sector angle ranges.

    Args:
        sectors: List of sector ranges as (start, end) tuples

    Raises:
        ValueError: If sector ranges are invalid

    Example:
        >>> validate_sector_ranges([(60, 120), (240, 300)])  # OK
        >>> validate_sector_ranges([(120, 60)])  # Raises ValueError
        Traceback (most recent call last):
        ...
        ValueError: Sector start must be <= end, got (120, 60)
    """
    if not sectors or not isinstance(sectors, list):
        raise ValueError("Sectors must be a non-empty list")

    for start, end in sectors:
        # Check types
        if not (isinstance(start, (int, float)) and isinstance(end, (int, float))):
            raise ValueError(f"Sector angles must be numbers, got ({start}, {end})")

        # Check range
        if not (0 <= start <= 360 and 0 <= end <= 360):
            raise ValueError(f"Sector angles must be in [0, 360], got ({start}, {end})")

        # Check order
        if start > end:
            raise ValueError(f"Sector start must be <= end, got ({start}, {end})")


def create_sector_mask(
    wind_directions: np.ndarray,
    turbine_sectors: Dict[int, List[Tuple[float, float]]],
    n_turbines: int
) -> np.ndarray:
    """
    Create boolean mask indicating when each turbine can operate.

    Args:
        wind_directions: Array of wind directions (n_timesteps,)
        turbine_sectors: Dict mapping turbine_id to allowed sectors
        n_turbines: Total number of turbines

    Returns:
        Boolean array of shape (n_timesteps, n_turbines)
        True where turbine can operate, False where stopped

    Example:
        >>> wind_dirs = np.array([45, 90, 150, 270])
        >>> sectors = {1: [(60, 120), (240, 300)]}  # Turbine 1 (index 0)
        >>> mask = create_sector_mask(wind_dirs, sectors, n_turbines=3)
        >>> mask[:, 0]  # Turbine 1 mask
        array([False,  True, False,  True])
        >>> mask[:, 1]  # Turbine 2 (no restrictions)
        array([True, True, True, True])
    """
    n_timesteps = len(wind_directions)
    mask = np.ones((n_timesteps, n_turbines), dtype=bool)  # All True by default

    # Apply sector restrictions
    for turbine_id, sectors in turbine_sectors.items():
        turbine_idx = turbine_id - 1  # Convert to 0-indexed

        if turbine_idx < 0 or turbine_idx >= n_turbines:
            raise ValueError(f"Turbine ID {turbine_id} out of range for {n_turbines} turbines")

        # Set mask to False for prohibited directions
        for t, wd in enumerate(wind_directions):
            mask[t, turbine_idx] = is_direction_in_sectors(wd, sectors)

    return mask


def get_sector_statistics(
    wind_data: pd.DataFrame,
    turbine_sectors: Dict[int, List[Tuple[float, float]]]
) -> Dict[int, Dict]:
    """
    Get detailed statistics about sector management impact.

    Args:
        wind_data: DataFrame with 'wd' column
        turbine_sectors: Dict mapping turbine_id to allowed sectors

    Returns:
        Dict with statistics per turbine:
        {
            turbine_id: {
                'availability': 0.33,  # Fraction of time available
                'curtailment': 0.67,   # Fraction of time curtailed
                'allowed_hours_per_year': 2920,
                'stopped_hours_per_year': 5840
            }
        }
    """
    availability = calculate_sector_availability(wind_data, turbine_sectors)
    hours_per_year = len(wind_data)

    stats = {}
    for turbine_id, avail in availability.items():
        stats[turbine_id] = {
            'availability': avail,
            'curtailment': 1 - avail,
            'allowed_hours_per_year': avail * hours_per_year,
            'stopped_hours_per_year': (1 - avail) * hours_per_year
        }

    return stats
