"""
Shading loss calculations for hybrid wind-solar systems.

Calculates shadow impacts from wind turbines on solar PV arrays.
"""

from typing import Tuple, Optional
import numpy as np
import pandas as pd
from datetime import datetime


class ShadingCalculator:
    """
    Calculate shading losses from wind turbines on solar panels.

    Uses simplified geometric shadow projection based on sun position.
    """

    def __init__(
        self,
        latitude: float,
        longitude: float,
        timezone_offset: int = -4
    ):
        """
        Initialize shading calculator.

        Args:
            latitude: Site latitude in degrees
            longitude: Site longitude in degrees
            timezone_offset: UTC offset in hours
        """
        self.latitude = latitude
        self.longitude = longitude
        self.timezone_offset = timezone_offset

    def calculate_sun_position(
        self,
        timestamps: pd.DatetimeIndex
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate sun position (zenith and azimuth) for timestamps.

        Args:
            timestamps: DatetimeIndex of timestamps

        Returns:
            Tuple of (solar_zenith, solar_azimuth) in degrees

        Note:
            Uses pvlib if available, otherwise simplified calculation
        """
        try:
            from pvlib import solarposition

            # Calculate sun position using pvlib
            sun_pos = solarposition.get_solarposition(
                timestamps,
                self.latitude,
                self.longitude
            )

            solar_zenith = sun_pos['zenith'].values
            solar_azimuth = sun_pos['azimuth'].values

            return solar_zenith, solar_azimuth

        except ImportError:
            # Fallback to simplified calculation
            return self._simple_sun_position(timestamps)

    def _simple_sun_position(
        self,
        timestamps: pd.DatetimeIndex
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simplified sun position calculation.

        Args:
            timestamps: DatetimeIndex of timestamps

        Returns:
            Tuple of (solar_zenith, solar_azimuth) in degrees
        """
        n = len(timestamps)

        # Very simplified - just for demonstration
        # Real calculation requires considering equation of time, declination, etc.
        hour_angles = np.array([
            (ts.hour - 12) * 15 for ts in timestamps
        ])

        # Approximate zenith (simplified)
        solar_zenith = np.abs(hour_angles) + 30

        # Approximate azimuth (simplified)
        solar_azimuth = (hour_angles + 180) % 360

        return solar_zenith, solar_azimuth

    def calculate_shadow_length(
        self,
        object_height: float,
        solar_zenith: float
    ) -> float:
        """
        Calculate shadow length from object height and sun position.

        Args:
            object_height: Height of object casting shadow (m)
            solar_zenith: Solar zenith angle (degrees)

        Returns:
            Shadow length (m)
        """
        if solar_zenith >= 90:
            # Sun below horizon - very long shadow
            return 1000.0

        # Shadow length = height / tan(solar_altitude)
        solar_altitude = 90 - solar_zenith
        shadow_length = object_height / np.tan(np.radians(solar_altitude))

        return max(0, shadow_length)

    def calculate_turbine_shadow_area(
        self,
        turbine_x: float,
        turbine_y: float,
        hub_height: float,
        rotor_diameter: float,
        solar_zenith: float,
        solar_azimuth: float
    ) -> Tuple[float, float, float]:
        """
        Calculate shadow position and dimensions from a single turbine.

        Args:
            turbine_x: Turbine x-coordinate (m)
            turbine_y: Turbine y-coordinate (m)
            hub_height: Turbine hub height (m)
            rotor_diameter: Turbine rotor diameter (m)
            solar_zenith: Solar zenith angle (degrees)
            solar_azimuth: Solar azimuth angle (degrees)

        Returns:
            Tuple of (shadow_center_x, shadow_center_y, shadow_radius)
        """
        if solar_zenith >= 90:
            # Sun below horizon - no meaningful shadow
            return (turbine_x, turbine_y, 0)

        # Effective height (hub height + half rotor diameter for approximation)
        effective_height = hub_height + rotor_diameter / 2

        # Shadow length
        shadow_length = self.calculate_shadow_length(effective_height, solar_zenith)

        # Shadow direction (opposite to sun azimuth)
        shadow_azimuth = (solar_azimuth + 180) % 360

        # Shadow center position
        shadow_center_x = turbine_x + shadow_length * np.sin(np.radians(shadow_azimuth))
        shadow_center_y = turbine_y + shadow_length * np.cos(np.radians(shadow_azimuth))

        # Shadow radius (approximate as ellipse, simplified to circle)
        shadow_radius = rotor_diameter / 2

        return (shadow_center_x, shadow_center_y, shadow_radius)

    def is_panel_shaded(
        self,
        panel_x: float,
        panel_y: float,
        shadow_center_x: float,
        shadow_center_y: float,
        shadow_radius: float
    ) -> bool:
        """
        Check if a panel is within a shadow area.

        Args:
            panel_x: Panel x-coordinate (m)
            panel_y: Panel y-coordinate (m)
            shadow_center_x: Shadow center x (m)
            shadow_center_y: Shadow center y (m)
            shadow_radius: Shadow radius (m)

        Returns:
            True if panel is shaded
        """
        distance = np.sqrt(
            (panel_x - shadow_center_x)**2 +
            (panel_y - shadow_center_y)**2
        )

        return distance < shadow_radius

    def calculate_shading_factor(
        self,
        timestamps: pd.DatetimeIndex,
        turbine_positions: np.ndarray,
        turbine_height: float,
        rotor_diameter: float,
        panel_positions: np.ndarray
    ) -> pd.DataFrame:
        """
        Calculate shading factors for all panels over time.

        Args:
            timestamps: Timeseries timestamps
            turbine_positions: Nx2 array of turbine (x, y) positions
            turbine_height: Turbine hub height (m)
            rotor_diameter: Rotor diameter (m)
            panel_positions: Mx2 array of panel (x, y) positions

        Returns:
            DataFrame with shading factor (0-1) for each panel over time

        Example:
            >>> calc = ShadingCalculator(latitude=-30, longitude=-70)
            >>> shading = calc.calculate_shading_factor(
            ...     timestamps=solar_data.timeseries.index,
            ...     turbine_positions=np.array([[0, 0], [800, 0]]),
            ...     turbine_height=120,
            ...     rotor_diameter=164,
            ...     panel_positions=np.array([[400, 100]])
            ... )
        """
        n_hours = len(timestamps)
        n_panels = len(panel_positions)

        # Calculate sun position
        solar_zenith, solar_azimuth = self.calculate_sun_position(timestamps)

        # Initialize shading factors (1 = no shading, 0 = full shading)
        shading_factors = np.ones((n_hours, n_panels))

        # Calculate shading for each hour
        for hour_idx in range(n_hours):
            zenith = solar_zenith[hour_idx]
            azimuth = solar_azimuth[hour_idx]

            if zenith < 90:  # Sun above horizon
                # Check each turbine's shadow
                for turb_pos in turbine_positions:
                    shadow_x, shadow_y, shadow_r = self.calculate_turbine_shadow_area(
                        turb_pos[0], turb_pos[1],
                        turbine_height, rotor_diameter,
                        zenith, azimuth
                    )

                    # Check which panels are shaded
                    for panel_idx, panel_pos in enumerate(panel_positions):
                        if self.is_panel_shaded(
                            panel_pos[0], panel_pos[1],
                            shadow_x, shadow_y, shadow_r
                        ):
                            # Simplified: full shading = 0.5 factor
                            # Real calculation would consider partial shading
                            shading_factors[hour_idx, panel_idx] *= 0.5

        # Create DataFrame
        df = pd.DataFrame(
            shading_factors,
            index=timestamps,
            columns=[f"panel_{i}" for i in range(n_panels)]
        )

        return df

    def calculate_aggregate_shading_loss(
        self,
        timestamps: pd.DatetimeIndex,
        turbine_positions: np.ndarray,
        turbine_height: float,
        rotor_diameter: float,
        panel_positions: np.ndarray
    ) -> pd.Series:
        """
        Calculate aggregate shading factor for entire PV array.

        Args:
            timestamps: Timeseries timestamps
            turbine_positions: Nx2 array of turbine positions
            turbine_height: Hub height (m)
            rotor_diameter: Rotor diameter (m)
            panel_positions: Mx2 array of panel positions

        Returns:
            Timeseries of aggregate shading factors (0-1)
        """
        shading_df = self.calculate_shading_factor(
            timestamps,
            turbine_positions,
            turbine_height,
            rotor_diameter,
            panel_positions
        )

        # Average across all panels
        aggregate_factor = shading_df.mean(axis=1)

        return aggregate_factor


def calculate_simple_shading_loss(
    solar_timeseries: pd.DataFrame,
    turbine_distance: float,
    turbine_height: float,
    rotor_diameter: float
) -> float:
    """
    Simplified shading loss estimation based on distance.

    Args:
        solar_timeseries: Solar production timeseries
        turbine_distance: Average distance from turbines to PV (m)
        turbine_height: Turbine hub height (m)
        rotor_diameter: Rotor diameter (m)

    Returns:
        Estimated annual shading loss percentage (0-100)

    Note:
        This is a very simplified approach. Use ShadingCalculator for
        accurate hour-by-hour shading analysis.
    """
    # Rule of thumb: shading significant if distance < 5 * height
    critical_distance = 5 * turbine_height

    if turbine_distance > critical_distance:
        # Minimal shading
        return 0.5

    # Linear interpolation
    loss_percent = 10 * (1 - turbine_distance / critical_distance)

    return max(0, min(loss_percent, 15))  # Cap at 15%
