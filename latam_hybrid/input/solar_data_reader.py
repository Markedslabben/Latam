"""
Solar data readers for PV analysis.

Supports PVGIS CSV format and prepares data for pvlib integration.
"""

from pathlib import Path
from typing import Optional, Union, Dict
import pandas as pd
import numpy as np

from ..core import SolarData, TimeZoneOffset, DataValidator, align_pvgis_time
from .loaders import FileLoader


class PVGISReader:
    """
    Reader for PVGIS (Photovoltaic Geographical Information System) data.

    PVGIS provides:
    - Hourly irradiance data
    - Temperature data
    - PV power output estimates
    - Requires timezone shift (+30 min typically)
    """

    @staticmethod
    def read_pvgis_csv(
        filepath: Union[str, Path],
        capacity_kw: float,
        skiprows: int = 10,
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4,
        shift_minutes: int = 30,
        apply_time_shift: bool = True,
        validate: bool = True
    ) -> SolarData:
        """
        Read PVGIS CSV time series file.

        Args:
            filepath: Path to PVGIS CSV file
            capacity_kw: Installed PV capacity in kW
            skiprows: Number of header rows to skip (PVGIS typically has 10)
            timezone_offset: Local timezone UTC offset
            shift_minutes: Time shift to apply (PVGIS typically needs +30min)
            apply_time_shift: Whether to apply timezone/shift adjustments
            validate: Whether to validate loaded data

        Returns:
            SolarData object with timeseries and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If data validation fails

        Example:
            >>> solar_data = PVGISReader.read_pvgis_csv(
            ...     "PVGIS_timeseries.csv",
            ...     capacity_kw=10000,
            ...     skiprows=10
            ... )
        """
        filepath = Path(filepath)

        # Load PVGIS CSV
        df = FileLoader.load_csv(
            filepath,
            skiprows=skiprows,
            parse_dates=['time'] if 'time' in pd.read_csv(filepath, nrows=1).columns else None
        )

        # PVGIS column names (may vary)
        # Common columns: time, G(i), H_sun, T2m, Int, WS10m, P
        # Required: time, P (power)
        # Optional: G(i) (irradiance), T2m (temperature)

        # Handle timestamp column
        time_col_candidates = ['time', 'Time', 'timestamp', 'Timestamp']
        time_col = None
        for col in time_col_candidates:
            if col in df.columns:
                time_col = col
                break

        # If no time column but index looks like dates, use it
        if time_col is None:
            if pd.api.types.is_datetime64_any_dtype(df.index):
                # Already has datetime index, nothing to do
                pass
            else:
                # Try to parse first column as datetime
                if len(df.columns) > 0:
                    try:
                        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
                        time_col = df.columns[0]
                    except:
                        raise ValueError(
                            f"No time column found in PVGIS file. "
                            f"Available columns: {df.columns.tolist()}"
                        )
                else:
                    raise ValueError(
                        f"No time column found in PVGIS file. "
                        f"Available columns: {df.columns.tolist()}"
                    )

        # Convert to datetime and set as index
        if time_col is not None:
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.set_index(time_col)
        # else: already has datetime index

        # Identify power column
        power_col_candidates = ['P', 'p', 'power', 'Power']
        power_col = None
        for col in power_col_candidates:
            if col in df.columns:
                power_col = col
                break

        if power_col is None:
            raise ValueError(
                f"No power column found in PVGIS file. "
                f"Available columns: {df.columns.tolist()}"
            )

        # Standardize column names
        rename_mapping = {power_col: 'P'}

        # Optional columns
        if 'G(i)' in df.columns:
            # Irradiance already standard
            pass
        elif 'irradiance' in df.columns:
            rename_mapping['irradiance'] = 'G(i)'

        if 'T2m' in df.columns:
            # Temperature already standard
            pass
        elif 'temp' in df.columns or 'temperature' in df.columns:
            temp_col = 'temp' if 'temp' in df.columns else 'temperature'
            rename_mapping[temp_col] = 'T2m'

        df = df.rename(columns=rename_mapping)

        # Apply time shift if requested
        if apply_time_shift:
            df = align_pvgis_time(
                df,
                timezone_offset=timezone_offset,
                shift_minutes=shift_minutes
            )

        # Validate
        if validate:
            validation_result = DataValidator.validate_solar_data(
                df,
                power_col='P',
                irradiance_col='G(i)' if 'G(i)' in df.columns else None
            )
            validation_result.raise_if_invalid()

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'capacity_kw': capacity_kw,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'PVGIS',
            'columns': df.columns.tolist(),
            'time_shift_applied': apply_time_shift,
            'shift_minutes': shift_minutes if apply_time_shift else 0
        }

        return SolarData(
            timeseries=df,
            capacity_kw=capacity_kw,
            timezone_offset=timezone_offset,
            shift_minutes=shift_minutes if apply_time_shift else 0,
            source="PVGIS",
            metadata=metadata
        )


class GenericSolarReader:
    """
    Generic solar data reader for CSV/Excel formats.

    For custom or standardized solar data formats.
    """

    @staticmethod
    def read_csv(
        filepath: Union[str, Path],
        capacity_kw: float,
        power_column: str = 'P',
        irradiance_column: Optional[str] = None,
        temp_column: Optional[str] = None,
        time_column: Optional[str] = None,
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4,
        validate: bool = True
    ) -> SolarData:
        """
        Read generic solar data from CSV.

        Args:
            filepath: Path to CSV file
            capacity_kw: Installed PV capacity in kW
            power_column: Power output column name
            irradiance_column: Irradiance column name (optional)
            temp_column: Temperature column name (optional)
            time_column: Timestamp column (None if index)
            timezone_offset: UTC offset
            validate: Whether to validate data

        Returns:
            SolarData object

        Example:
            >>> solar_data = GenericSolarReader.read_csv(
            ...     "pv_production.csv",
            ...     capacity_kw=5000,
            ...     power_column="AC_Power_kW"
            ... )
        """
        # Load CSV
        if time_column:
            df = FileLoader.load_csv(filepath, parse_dates=[time_column])
            df = df.set_index(time_column)
        else:
            df = FileLoader.load_csv(filepath, index_col=0, parse_dates=True)

        # Build rename mapping
        rename_mapping = {power_column: 'P'}
        if irradiance_column:
            rename_mapping[irradiance_column] = 'G(i)'
        if temp_column:
            rename_mapping[temp_column] = 'T2m'

        df = df.rename(columns=rename_mapping)

        # Ensure power column exists
        if 'P' not in df.columns:
            raise ValueError(
                f"Power column '{power_column}' not found. "
                f"Available: {df.columns.tolist()}"
            )

        # Validate
        if validate:
            validation_result = DataValidator.validate_solar_data(
                df,
                power_col='P',
                irradiance_col='G(i)' if 'G(i)' in df.columns else None
            )
            validation_result.raise_if_invalid()

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'capacity_kw': capacity_kw,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'CSV',
            'columns': df.columns.tolist()
        }

        return SolarData(
            timeseries=df,
            capacity_kw=capacity_kw,
            timezone_offset=timezone_offset,
            shift_minutes=0,
            source="CSV",
            metadata=metadata
        )

    @staticmethod
    def read_excel(
        filepath: Union[str, Path],
        capacity_kw: float,
        power_column: str = 'P',
        irradiance_column: Optional[str] = None,
        temp_column: Optional[str] = None,
        time_column: Optional[str] = None,
        sheet_name: Union[str, int] = 0,
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4,
        validate: bool = True
    ) -> SolarData:
        """
        Read generic solar data from Excel.

        Args:
            filepath: Path to Excel file
            capacity_kw: Installed PV capacity in kW
            power_column: Power output column name
            irradiance_column: Irradiance column name (optional)
            temp_column: Temperature column name (optional)
            time_column: Timestamp column (None if index)
            sheet_name: Sheet name or index
            timezone_offset: UTC offset
            validate: Whether to validate data

        Returns:
            SolarData object

        Example:
            >>> solar_data = GenericSolarReader.read_excel(
            ...     "pv_data.xlsx",
            ...     capacity_kw=5000,
            ...     sheet_name="2024"
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

        # Build rename mapping
        rename_mapping = {power_column: 'P'}
        if irradiance_column:
            rename_mapping[irradiance_column] = 'G(i)'
        if temp_column:
            rename_mapping[temp_column] = 'T2m'

        df = df.rename(columns=rename_mapping)

        # Ensure power column exists
        if 'P' not in df.columns:
            raise ValueError(
                f"Power column '{power_column}' not found. "
                f"Available: {df.columns.tolist()}"
            )

        # Validate
        if validate:
            validation_result = DataValidator.validate_solar_data(
                df,
                power_col='P',
                irradiance_col='G(i)' if 'G(i)' in df.columns else None
            )
            validation_result.raise_if_invalid()

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'sheet_name': sheet_name,
            'capacity_kw': capacity_kw,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'Excel',
            'columns': df.columns.tolist()
        }

        return SolarData(
            timeseries=df,
            capacity_kw=capacity_kw,
            timezone_offset=timezone_offset,
            shift_minutes=0,
            source="Excel",
            metadata=metadata
        )


# Convenience function
def read_solar_data(
    filepath: Union[str, Path],
    capacity_kw: float,
    source_type: str = 'auto',
    **kwargs
) -> SolarData:
    """
    Auto-detect format and read solar data.

    Args:
        filepath: Path to solar data file
        capacity_kw: Installed PV capacity in kW
        source_type: Source type ('pvgis', 'csv', 'excel', or 'auto')
        **kwargs: Additional arguments passed to specific reader

    Returns:
        SolarData object

    Example:
        >>> solar_data = read_solar_data("PVGIS_timeseries.csv", capacity_kw=10000)
        >>> solar_data = read_solar_data("pv.xlsx", capacity_kw=5000, source_type='excel')
    """
    filepath = Path(filepath)

    # Auto-detect format
    if source_type == 'auto':
        suffix = filepath.suffix.lower()
        name = filepath.name.lower()

        if 'pvgis' in name:
            source_type = 'pvgis'
        elif suffix == '.csv':
            # Check if it's PVGIS format by looking for skiprows pattern
            try:
                # PVGIS files have metadata in first ~10 rows
                first_line = open(filepath, 'r').readline()
                if 'lat' in first_line.lower() or 'lon' in first_line.lower():
                    source_type = 'pvgis'
                else:
                    source_type = 'csv'
            except:
                source_type = 'csv'
        elif suffix in ['.xlsx', '.xls']:
            source_type = 'excel'
        else:
            source_type = 'csv'

    # Read based on detected type
    if source_type == 'pvgis':
        return PVGISReader.read_pvgis_csv(filepath, capacity_kw, **kwargs)
    elif source_type == 'csv':
        return GenericSolarReader.read_csv(filepath, capacity_kw, **kwargs)
    elif source_type == 'excel':
        return GenericSolarReader.read_excel(filepath, capacity_kw, **kwargs)
    else:
        raise ValueError(f"Unknown source_type: {source_type}")
