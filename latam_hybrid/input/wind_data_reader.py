"""
Wind data readers for various meteorological data sources.

Supports Vortex time series format and prepares data for pywake integration.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

from ..core import WindData, TimeZoneOffset, DataValidator, TimeAlignmentService
from .loaders import FileLoader


class VortexWindReader:
    """
    Reader for Vortex wind time series data.

    Vortex typically provides:
    - Text files with wind speed (ws) and direction (wd)
    - Multiple height levels
    - UTC timestamps
    - Metadata in header rows
    """

    @staticmethod
    def read_vortex_timeseries(
        filepath: Union[str, Path],
        height: float = 100.0,
        skiprows: int = 0,
        column_mapping: Optional[Dict[str, str]] = None,
        timezone_offset: int = TimeZoneOffset.UTC,
        validate: bool = True
    ) -> WindData:
        """
        Read Vortex wind time series file.

        Args:
            filepath: Path to Vortex data file
            height: Measurement height in meters
            skiprows: Number of header rows to skip
            column_mapping: Map file columns to standard names
                          Default: {'ws': 'ws', 'wd': 'wd', 'time': 'time'}
            timezone_offset: UTC offset of timestamps in file
            validate: Whether to validate loaded data

        Returns:
            WindData object with timeseries and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If data validation fails

        Example:
            >>> wind_data = VortexWindReader.read_vortex_timeseries(
            ...     "vortex.serie.100m.txt",
            ...     height=100.0,
            ...     skiprows=3
            ... )
        """
        filepath = Path(filepath)

        # Default column mapping
        if column_mapping is None:
            column_mapping = {
                'time': 'time',
                'ws': 'ws',
                'wd': 'wd'
            }

        # Load file (Vortex typically whitespace-delimited)
        df = FileLoader.load_text_file(
            filepath,
            skiprows=skiprows,
            delimiter=None  # Whitespace
        )

        # Rename columns if needed
        if column_mapping:
            # Try to map columns
            reverse_mapping = {v: k for k, v in column_mapping.items()}
            df = df.rename(columns=reverse_mapping)

        # Ensure required columns exist
        required_cols = ['ws', 'wd']
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"Vortex file missing required columns: {missing_cols}. "
                f"Available columns: {df.columns.tolist()}"
            )

        # Handle timestamp column
        if 'time' in df.columns:
            # Convert to datetime
            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')
        elif not isinstance(df.index, pd.DatetimeIndex):
            # Try to parse index as datetime
            try:
                df.index = pd.to_datetime(df.index)
            except Exception:
                raise ValueError(
                    "No valid timestamp column found. Vortex data must have "
                    "datetime index or 'time' column."
                )

        # Ensure only required columns
        df = df[required_cols]

        # Validate data if requested
        if validate:
            validation_result = DataValidator.validate_wind_data(df)
            validation_result.raise_if_invalid()

        # Extract metadata
        metadata = {
            'filepath': str(filepath),
            'height': height,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'Vortex'
        }

        # Create WindData object
        wind_data = WindData(
            timeseries=df,
            height=height,
            timezone_offset=timezone_offset,
            source="Vortex",
            metadata=metadata
        )

        return wind_data

    @staticmethod
    def read_vortex_multiple_heights(
        filepath_pattern: str,
        heights: list[float],
        **kwargs
    ) -> Dict[float, WindData]:
        """
        Read Vortex files for multiple heights.

        Args:
            filepath_pattern: Path pattern with {height} placeholder
                            Example: "vortex.serie.{height}m.txt"
            heights: List of heights to read
            **kwargs: Additional arguments passed to read_vortex_timeseries

        Returns:
            Dictionary mapping heights to WindData objects

        Example:
            >>> wind_data_dict = VortexWindReader.read_vortex_multiple_heights(
            ...     "data/vortex.serie.{height}m.txt",
            ...     heights=[80, 100, 120]
            ... )
            >>> ws_100m = wind_data_dict[100].timeseries['ws']
        """
        wind_data = {}

        for height in heights:
            filepath = filepath_pattern.format(height=int(height))
            wind_data[height] = VortexWindReader.read_vortex_timeseries(
                filepath,
                height=height,
                **kwargs
            )

        return wind_data


class GenericWindReader:
    """
    Generic wind data reader for CSV/Excel formats.

    For custom or standardized wind data formats.
    """

    @staticmethod
    def read_csv(
        filepath: Union[str, Path],
        ws_column: str = 'ws',
        wd_column: str = 'wd',
        time_column: Optional[str] = None,
        height: float = 100.0,
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4,
        validate: bool = True
    ) -> WindData:
        """
        Read generic wind data from CSV.

        Args:
            filepath: Path to CSV file
            ws_column: Wind speed column name
            wd_column: Wind direction column name
            time_column: Timestamp column name (None if index)
            height: Measurement height in meters
            timezone_offset: UTC offset
            validate: Whether to validate data

        Returns:
            WindData object

        Example:
            >>> wind_data = GenericWindReader.read_csv(
            ...     "wind_measurements.csv",
            ...     ws_column="wind_speed_ms",
            ...     wd_column="wind_direction_deg"
            ... )
        """
        # Load CSV
        if time_column:
            df = FileLoader.load_csv(filepath, parse_dates=[time_column])
            df = df.set_index(time_column)
        else:
            df = FileLoader.load_csv(filepath, index_col=0, parse_dates=True)

        # Rename columns to standard names
        df = df.rename(columns={
            ws_column: 'ws',
            wd_column: 'wd'
        })

        # Ensure required columns
        if 'ws' not in df.columns or 'wd' not in df.columns:
            raise ValueError(
                f"Columns '{ws_column}' and/or '{wd_column}' not found in CSV. "
                f"Available: {df.columns.tolist()}"
            )

        # Keep only required columns
        df = df[['ws', 'wd']]

        # Validate
        if validate:
            validation_result = DataValidator.validate_wind_data(df)
            validation_result.raise_if_invalid()

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'height': height,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'CSV'
        }

        return WindData(
            timeseries=df,
            height=height,
            timezone_offset=timezone_offset,
            source="CSV",
            metadata=metadata
        )

    @staticmethod
    def read_excel(
        filepath: Union[str, Path],
        ws_column: str = 'ws',
        wd_column: str = 'wd',
        time_column: Optional[str] = None,
        sheet_name: Union[str, int] = 0,
        height: float = 100.0,
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4,
        validate: bool = True
    ) -> WindData:
        """
        Read generic wind data from Excel.

        Args:
            filepath: Path to Excel file
            ws_column: Wind speed column name
            wd_column: Wind direction column name
            time_column: Timestamp column name (None if index)
            sheet_name: Sheet name or index
            height: Measurement height in meters
            timezone_offset: UTC offset
            validate: Whether to validate data

        Returns:
            WindData object

        Example:
            >>> wind_data = GenericWindReader.read_excel(
            ...     "wind_data.xlsx",
            ...     sheet_name="2024",
            ...     ws_column="WS",
            ...     wd_column="WD"
            ... )
        """
        # Load Excel
        if time_column:
            df = FileLoader.load_excel(
                filepath,
                sheet_name=sheet_name,
                parse_dates=[time_column]
            )
            df = df.set_index(time_column)
        else:
            df = FileLoader.load_excel(
                filepath,
                sheet_name=sheet_name,
                index_col=0,
                parse_dates=True
            )

        # Rename columns
        df = df.rename(columns={
            ws_column: 'ws',
            wd_column: 'wd'
        })

        # Ensure required columns
        if 'ws' not in df.columns or 'wd' not in df.columns:
            raise ValueError(
                f"Columns '{ws_column}' and/or '{wd_column}' not found. "
                f"Available: {df.columns.tolist()}"
            )

        # Keep only required columns
        df = df[['ws', 'wd']]

        # Validate
        if validate:
            validation_result = DataValidator.validate_wind_data(df)
            validation_result.raise_if_invalid()

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'sheet_name': sheet_name,
            'height': height,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'Excel'
        }

        return WindData(
            timeseries=df,
            height=height,
            timezone_offset=timezone_offset,
            source="Excel",
            metadata=metadata
        )


# Convenience function
def read_wind_data(
    filepath: Union[str, Path],
    source_type: str = 'auto',
    **kwargs
) -> WindData:
    """
    Auto-detect format and read wind data.

    Args:
        filepath: Path to wind data file
        source_type: Source type ('vortex', 'csv', 'excel', or 'auto')
        **kwargs: Additional arguments passed to specific reader

    Returns:
        WindData object

    Example:
        >>> wind_data = read_wind_data("vortex.serie.100m.txt")  # Auto-detects Vortex
        >>> wind_data = read_wind_data("data.csv", source_type='csv')
    """
    filepath = Path(filepath)

    # Auto-detect format
    if source_type == 'auto':
        suffix = filepath.suffix.lower()
        name = filepath.name.lower()

        if 'vortex' in name or 'serie' in name:
            source_type = 'vortex'
        elif suffix == '.csv':
            source_type = 'csv'
        elif suffix in ['.xlsx', '.xls']:
            source_type = 'excel'
        else:
            # Default to text file (Vortex-like)
            source_type = 'vortex'

    # Read based on detected type
    if source_type == 'vortex':
        return VortexWindReader.read_vortex_timeseries(filepath, **kwargs)
    elif source_type == 'csv':
        return GenericWindReader.read_csv(filepath, **kwargs)
    elif source_type == 'excel':
        return GenericWindReader.read_excel(filepath, **kwargs)
    else:
        raise ValueError(f"Unknown source_type: {source_type}")
