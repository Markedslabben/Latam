"""
Time alignment and timezone handling utilities.

This module provides unified time alignment services for wind, solar, and market data.
Handles timezone conversions, time shifts, and timeseries resampling.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class TimeAlignmentConfig:
    """
    Configuration for time alignment operations.

    Attributes:
        target_timezone_offset: Target UTC offset in hours
        shift_minutes: Additional time shift in minutes
        resampling_frequency: Target frequency for resampling (e.g., '1H', '15T')
        fill_method: Method for filling missing values ('ffill', 'bfill', 'interpolate', None)
        drop_na: Whether to drop NaN values after alignment
    """
    target_timezone_offset: int = -4  # UTC-4 for Latam region
    shift_minutes: int = 0
    resampling_frequency: Optional[str] = '1H'
    fill_method: Optional[str] = 'interpolate'
    drop_na: bool = False


class TimeAlignmentService:
    """
    Service for aligning timeseries data across different sources.

    This service handles common time alignment challenges:
    - PVGIS data often needs +30 minute shift
    - Wind data may be in different timezones
    - Market prices need alignment with generation
    - Different sampling frequencies need harmonization
    """

    @staticmethod
    def align_timezone(
        df: pd.DataFrame,
        source_offset_hours: int,
        target_offset_hours: int,
        shift_minutes: int = 0
    ) -> pd.DataFrame:
        """
        Align DataFrame timezone from source to target offset.

        Args:
            df: DataFrame with DatetimeIndex
            source_offset_hours: Source UTC offset in hours
            target_offset_hours: Target UTC offset in hours
            shift_minutes: Additional shift in minutes (can be positive or negative)

        Returns:
            DataFrame with adjusted timezone

        Example:
            >>> # PVGIS data in UTC-4, shift +30 minutes
            >>> df_aligned = TimeAlignmentService.align_timezone(
            ...     df, source_offset_hours=-4, target_offset_hours=-4, shift_minutes=30
            ... )
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")

        # Calculate total time shift
        offset_diff_hours = target_offset_hours - source_offset_hours
        total_shift = timedelta(hours=offset_diff_hours, minutes=shift_minutes)

        # Create new DataFrame with shifted index
        df_aligned = df.copy()
        df_aligned.index = df_aligned.index + total_shift

        return df_aligned

    @staticmethod
    def resample_timeseries(
        df: pd.DataFrame,
        target_frequency: str = '1H',
        aggregation_method: str = 'mean',
        fill_method: Optional[str] = 'interpolate'
    ) -> pd.DataFrame:
        """
        Resample timeseries to target frequency.

        Args:
            df: DataFrame with DatetimeIndex
            target_frequency: Target frequency string (pandas format: '1H', '15T', etc.)
            aggregation_method: Aggregation method ('mean', 'sum', 'max', 'min')
            fill_method: Method for filling gaps ('ffill', 'bfill', 'interpolate', None)

        Returns:
            Resampled DataFrame

        Example:
            >>> # Resample 10-minute data to hourly with mean aggregation
            >>> df_hourly = TimeAlignmentService.resample_timeseries(
            ...     df, target_frequency='1H', aggregation_method='mean'
            ... )
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")

        # Resample with specified aggregation
        resampler = df.resample(target_frequency)

        if aggregation_method == 'mean':
            df_resampled = resampler.mean()
        elif aggregation_method == 'sum':
            df_resampled = resampler.sum()
        elif aggregation_method == 'max':
            df_resampled = resampler.max()
        elif aggregation_method == 'min':
            df_resampled = resampler.min()
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation_method}")

        # Fill missing values if requested
        if fill_method == 'ffill':
            df_resampled = df_resampled.fillna(method='ffill')
        elif fill_method == 'bfill':
            df_resampled = df_resampled.fillna(method='bfill')
        elif fill_method == 'interpolate':
            df_resampled = df_resampled.interpolate(method='time')

        return df_resampled

    @staticmethod
    def align_multiple_timeseries(
        *dataframes: pd.DataFrame,
        method: str = 'inner',
        fill_method: Optional[str] = 'interpolate'
    ) -> List[pd.DataFrame]:
        """
        Align multiple timeseries to common index.

        Args:
            *dataframes: Variable number of DataFrames to align
            method: Join method ('inner', 'outer', 'left')
            fill_method: Method for filling missing values after alignment

        Returns:
            List of aligned DataFrames with common index

        Example:
            >>> wind_aligned, solar_aligned, price_aligned = (
            ...     TimeAlignmentService.align_multiple_timeseries(
            ...         wind_df, solar_df, price_df, method='inner'
            ...     )
            ... )
        """
        if len(dataframes) == 0:
            return []

        if len(dataframes) == 1:
            return list(dataframes)

        # Find common index based on method
        if method == 'inner':
            # Intersection of all indices
            common_index = dataframes[0].index
            for df in dataframes[1:]:
                common_index = common_index.intersection(df.index)
        elif method == 'outer':
            # Union of all indices
            common_index = dataframes[0].index
            for df in dataframes[1:]:
                common_index = common_index.union(df.index)
        elif method == 'left':
            # Use first DataFrame's index
            common_index = dataframes[0].index
        else:
            raise ValueError(f"Unknown method: {method}")

        # Reindex all DataFrames to common index
        aligned_dataframes = []
        for df in dataframes:
            df_aligned = df.reindex(common_index)

            # Fill missing values if requested
            if fill_method == 'ffill':
                df_aligned = df_aligned.fillna(method='ffill')
            elif fill_method == 'bfill':
                df_aligned = df_aligned.fillna(method='bfill')
            elif fill_method == 'interpolate':
                df_aligned = df_aligned.interpolate(method='time')

            aligned_dataframes.append(df_aligned)

        return aligned_dataframes

    @staticmethod
    def validate_hourly_timeseries(
        df: pd.DataFrame,
        expected_hours: int = 8760,
        tolerance: float = 0.01
    ) -> bool:
        """
        Validate that timeseries is hourly and complete.

        Args:
            df: DataFrame with DatetimeIndex
            expected_hours: Expected number of hours (8760 for non-leap year)
            tolerance: Tolerance for missing data (0.01 = 1%)

        Returns:
            True if valid hourly timeseries

        Raises:
            ValueError: If timeseries is not valid
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")

        # Check number of records
        n_records = len(df)
        if abs(n_records - expected_hours) / expected_hours > tolerance:
            raise ValueError(
                f"Expected ~{expected_hours} hours, got {n_records} "
                f"(difference: {abs(n_records - expected_hours)})"
            )

        # Check for duplicates
        if df.index.duplicated().any():
            n_duplicates = df.index.duplicated().sum()
            raise ValueError(f"Found {n_duplicates} duplicate timestamps")

        # Check frequency (should be close to 1 hour)
        time_diffs = df.index.to_series().diff()
        median_diff = time_diffs.median()

        if abs(median_diff - pd.Timedelta(hours=1)) > pd.Timedelta(minutes=5):
            raise ValueError(
                f"Median time difference is {median_diff}, expected 1 hour"
            )

        return True

    @staticmethod
    def check_leap_year_alignment(
        df: pd.DataFrame,
        raise_on_mismatch: bool = False
    ) -> dict:
        """
        Check if timeseries properly handles leap years.

        Args:
            df: DataFrame with DatetimeIndex
            raise_on_mismatch: Whether to raise exception on leap year issues

        Returns:
            Dictionary with leap year analysis results

        Example:
            >>> info = TimeAlignmentService.check_leap_year_alignment(df)
            >>> print(f"Contains leap year: {info['has_leap_year']}")
            >>> print(f"Expected hours: {info['expected_hours']}")
        """
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame must have DatetimeIndex")

        years = df.index.year.unique()
        is_leap_years = [pd.Timestamp(year, 2, 28).is_leap_year for year in years]

        has_leap_year = any(is_leap_years)
        expected_hours = 8784 if has_leap_year else 8760
        actual_hours = len(df)

        result = {
            'has_leap_year': has_leap_year,
            'years': years.tolist(),
            'leap_years': [year for year, is_leap in zip(years, is_leap_years) if is_leap],
            'expected_hours': expected_hours,
            'actual_hours': actual_hours,
            'hours_difference': actual_hours - expected_hours,
            'is_aligned': abs(actual_hours - expected_hours) <= 24  # Allow 1 day tolerance
        }

        if raise_on_mismatch and not result['is_aligned']:
            raise ValueError(
                f"Leap year mismatch: expected {expected_hours} hours, "
                f"got {actual_hours} hours (diff: {result['hours_difference']})"
            )

        return result

    @staticmethod
    def create_continuous_hourly_index(
        start: Union[str, datetime],
        end: Union[str, datetime],
        timezone_offset: int = -4
    ) -> pd.DatetimeIndex:
        """
        Create continuous hourly DatetimeIndex.

        Args:
            start: Start date (string or datetime)
            end: End date (string or datetime)
            timezone_offset: UTC offset in hours

        Returns:
            Continuous hourly DatetimeIndex

        Example:
            >>> index = TimeAlignmentService.create_continuous_hourly_index(
            ...     '2024-01-01', '2024-12-31 23:00', timezone_offset=-4
            ... )
        """
        if isinstance(start, str):
            start = pd.to_datetime(start)
        if isinstance(end, str):
            end = pd.to_datetime(end)

        # Create hourly index
        index = pd.date_range(start=start, end=end, freq='1H')

        # Add timezone information (as offset, not tz-aware)
        # We store as UTC but logically represent the local time
        return index

    @staticmethod
    def align_to_utc(
        df: pd.DataFrame,
        source_offset_hours: int
    ) -> pd.DataFrame:
        """
        Convert local time to UTC.

        Args:
            df: DataFrame with DatetimeIndex in local time
            source_offset_hours: Source UTC offset (e.g., -4 for UTC-4)

        Returns:
            DataFrame with UTC timestamps

        Example:
            >>> df_utc = TimeAlignmentService.align_to_utc(df, source_offset_hours=-4)
        """
        df_utc = df.copy()
        df_utc.index = df_utc.index - pd.Timedelta(hours=source_offset_hours)
        return df_utc

    @staticmethod
    def align_from_utc(
        df: pd.DataFrame,
        target_offset_hours: int
    ) -> pd.DataFrame:
        """
        Convert UTC to local time.

        Args:
            df: DataFrame with DatetimeIndex in UTC
            target_offset_hours: Target UTC offset (e.g., -4 for UTC-4)

        Returns:
            DataFrame with local timestamps

        Example:
            >>> df_local = TimeAlignmentService.align_from_utc(df, target_offset_hours=-4)
        """
        df_local = df.copy()
        df_local.index = df_local.index + pd.Timedelta(hours=target_offset_hours)
        return df_local


# ============================================================================
# Convenience Functions
# ============================================================================

def align_pvgis_time(
    df: pd.DataFrame,
    timezone_offset: int = -4,
    shift_minutes: int = 30
) -> pd.DataFrame:
    """
    Apply standard PVGIS time alignment.

    PVGIS data typically requires:
    1. Timezone shift to local time
    2. +30 minute shift to align with hourly convention

    Args:
        df: PVGIS DataFrame
        timezone_offset: Local timezone offset (default: -4 for Latam)
        shift_minutes: Time shift in minutes (default: 30)

    Returns:
        Aligned DataFrame
    """
    return TimeAlignmentService.align_timezone(
        df,
        source_offset_hours=timezone_offset,
        target_offset_hours=timezone_offset,
        shift_minutes=shift_minutes
    )


def align_vortex_time(
    df: pd.DataFrame,
    timezone_offset: int = -4
) -> pd.DataFrame:
    """
    Apply standard Vortex wind data time alignment.

    Args:
        df: Vortex DataFrame
        timezone_offset: Local timezone offset (default: -4)

    Returns:
        Aligned DataFrame
    """
    return TimeAlignmentService.align_timezone(
        df,
        source_offset_hours=0,  # Vortex typically in UTC
        target_offset_hours=timezone_offset,
        shift_minutes=0
    )
