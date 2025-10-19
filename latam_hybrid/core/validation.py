"""
Input validation utilities for data quality assurance.

This module provides validation functions for all input data types,
ensuring data integrity before processing.
"""

from typing import Optional, List, Tuple, Union
from pathlib import Path
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """
    Result of a validation check.

    Attributes:
        is_valid: Whether validation passed
        errors: List of error messages
        warnings: List of warning messages
        metadata: Additional validation metadata
    """
    is_valid: bool
    errors: List[str]
    warnings: List[str] = None
    metadata: dict = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid

    def raise_if_invalid(self):
        """Raise ValueError if validation failed."""
        if not self.is_valid:
            error_msg = "\n".join(self.errors)
            raise ValueError(f"Validation failed:\n{error_msg}")


class DataValidator:
    """
    Comprehensive data validation utilities.
    """

    @staticmethod
    def validate_file_exists(file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate that file exists and is readable.

        Args:
            file_path: Path to file

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        path = Path(file_path)

        if not path.exists():
            errors.append(f"File does not exist: {path}")
        elif not path.is_file():
            errors.append(f"Path is not a file: {path}")
        elif not path.stat().st_size > 0:
            warnings.append(f"File is empty: {path}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_dataframe_structure(
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        expected_dtypes: Optional[dict] = None,
        min_rows: int = 1
    ) -> ValidationResult:
        """
        Validate DataFrame structure and content.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            expected_dtypes: Dict mapping column names to expected dtypes
            min_rows: Minimum number of rows required

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # Check if DataFrame is empty
        if df.empty:
            errors.append("DataFrame is empty")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Check minimum rows
        if len(df) < min_rows:
            errors.append(f"DataFrame has {len(df)} rows, minimum {min_rows} required")

        # Check required columns
        if required_columns:
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")

        # Check data types
        if expected_dtypes:
            for col, expected_dtype in expected_dtypes.items():
                if col in df.columns:
                    actual_dtype = df[col].dtype
                    if not pd.api.types.is_dtype_equal(actual_dtype, expected_dtype):
                        warnings.append(
                            f"Column '{col}' has dtype {actual_dtype}, "
                            f"expected {expected_dtype}"
                        )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={'n_rows': len(df), 'n_cols': len(df.columns)}
        )

    @staticmethod
    def validate_timeseries(
        df: pd.DataFrame,
        expected_frequency: Optional[str] = None,
        check_gaps: bool = True,
        check_duplicates: bool = True,
        max_gap_tolerance: int = 2
    ) -> ValidationResult:
        """
        Validate timeseries DataFrame.

        Args:
            df: DataFrame with DatetimeIndex
            expected_frequency: Expected frequency ('1H', '15T', etc.)
            check_gaps: Whether to check for gaps in timeseries
            check_duplicates: Whether to check for duplicate timestamps
            max_gap_tolerance: Maximum number of consecutive gaps allowed

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        metadata = {}

        # Check index type
        if not isinstance(df.index, pd.DatetimeIndex):
            errors.append("DataFrame must have DatetimeIndex")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Check for duplicates
        if check_duplicates:
            n_duplicates = df.index.duplicated().sum()
            if n_duplicates > 0:
                errors.append(f"Found {n_duplicates} duplicate timestamps")
                metadata['n_duplicates'] = n_duplicates

        # Check for gaps
        if check_gaps and expected_frequency:
            time_diffs = df.index.to_series().diff()
            expected_diff = pd.Timedelta(expected_frequency)

            gaps = time_diffs[time_diffs > expected_diff * (1 + 0.1)]  # 10% tolerance
            n_gaps = len(gaps)

            if n_gaps > 0:
                if n_gaps > max_gap_tolerance:
                    errors.append(f"Found {n_gaps} gaps in timeseries")
                else:
                    warnings.append(f"Found {n_gaps} gaps in timeseries (within tolerance)")

                metadata['n_gaps'] = n_gaps
                metadata['max_gap'] = time_diffs.max()

        # Check frequency consistency
        if expected_frequency:
            inferred_freq = pd.infer_freq(df.index)
            if inferred_freq != expected_frequency:
                warnings.append(
                    f"Inferred frequency '{inferred_freq}' differs from "
                    f"expected '{expected_frequency}'"
                )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )

    @staticmethod
    def validate_numeric_range(
        values: Union[pd.Series, np.ndarray],
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        allow_nan: bool = False,
        name: str = "values"
    ) -> ValidationResult:
        """
        Validate numeric values are within expected range.

        Args:
            values: Numeric values to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_nan: Whether NaN values are acceptable
            name: Name of the field being validated (for error messages)

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        metadata = {}

        # Convert to array if Series
        if isinstance(values, pd.Series):
            values = values.values

        # Check for NaN values
        n_nan = np.isnan(values).sum()
        if n_nan > 0:
            if not allow_nan:
                errors.append(f"{name}: Found {n_nan} NaN values")
            else:
                warnings.append(f"{name}: Found {n_nan} NaN values")
            metadata['n_nan'] = n_nan

        # Get non-NaN values
        valid_values = values[~np.isnan(values)]

        if len(valid_values) == 0:
            errors.append(f"{name}: No valid (non-NaN) values found")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Check range
        actual_min = valid_values.min()
        actual_max = valid_values.max()

        if min_value is not None and actual_min < min_value:
            errors.append(
                f"{name}: Minimum value {actual_min} is below allowed minimum {min_value}"
            )

        if max_value is not None and actual_max > max_value:
            errors.append(
                f"{name}: Maximum value {actual_max} exceeds allowed maximum {max_value}"
            )

        metadata.update({
            'min': actual_min,
            'max': actual_max,
            'mean': valid_values.mean(),
            'std': valid_values.std()
        })

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )

    @staticmethod
    def validate_wind_data(
        df: pd.DataFrame,
        ws_col: str = 'ws',
        wd_col: str = 'wd'
    ) -> ValidationResult:
        """
        Validate wind data DataFrame.

        Args:
            df: Wind data DataFrame
            ws_col: Wind speed column name
            wd_col: Wind direction column name

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # Check structure
        structure_result = DataValidator.validate_dataframe_structure(
            df,
            required_columns=[ws_col, wd_col],
            min_rows=8760  # At least one year
        )
        errors.extend(structure_result.errors)
        warnings.extend(structure_result.warnings)

        if not structure_result.is_valid:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate wind speed (0-50 m/s reasonable range)
        ws_result = DataValidator.validate_numeric_range(
            df[ws_col],
            min_value=0,
            max_value=50,
            allow_nan=False,
            name="Wind speed"
        )
        errors.extend(ws_result.errors)
        warnings.extend(ws_result.warnings)

        # Validate wind direction (0-360 degrees)
        wd_result = DataValidator.validate_numeric_range(
            df[wd_col],
            min_value=0,
            max_value=360,
            allow_nan=False,
            name="Wind direction"
        )
        errors.extend(wd_result.errors)
        warnings.extend(wd_result.warnings)

        # Check for calm winds (potential data quality issue)
        calm_count = (df[ws_col] == 0).sum()
        if calm_count > len(df) * 0.05:  # More than 5% calm
            warnings.append(
                f"High proportion of calm winds: {calm_count}/{len(df)} "
                f"({100 * calm_count / len(df):.1f}%)"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_solar_data(
        df: pd.DataFrame,
        power_col: str = 'P',
        irradiance_col: Optional[str] = 'G(i)'
    ) -> ValidationResult:
        """
        Validate solar data DataFrame.

        Args:
            df: Solar data DataFrame
            power_col: Power output column name
            irradiance_col: Irradiance column name (optional)

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        required_cols = [power_col]
        if irradiance_col:
            required_cols.append(irradiance_col)

        # Check structure
        structure_result = DataValidator.validate_dataframe_structure(
            df,
            required_columns=required_cols,
            min_rows=8760
        )
        errors.extend(structure_result.errors)
        warnings.extend(structure_result.warnings)

        if not structure_result.is_valid:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate power (non-negative)
        power_result = DataValidator.validate_numeric_range(
            df[power_col],
            min_value=0,
            allow_nan=False,
            name="PV power"
        )
        errors.extend(power_result.errors)
        warnings.extend(power_result.warnings)

        # Validate irradiance if present
        if irradiance_col and irradiance_col in df.columns:
            irradiance_result = DataValidator.validate_numeric_range(
                df[irradiance_col],
                min_value=0,
                max_value=1500,  # W/m² reasonable max
                allow_nan=False,
                name="Irradiance"
            )
            errors.extend(irradiance_result.errors)
            warnings.extend(irradiance_result.warnings)

        # Check for nighttime hours (power = 0)
        zero_power_count = (df[power_col] == 0).sum()
        nighttime_fraction = zero_power_count / len(df)

        if nighttime_fraction < 0.3 or nighttime_fraction > 0.7:
            warnings.append(
                f"Unusual nighttime fraction: {nighttime_fraction:.1%} "
                f"(expected ~40-60% for typical locations)"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    @staticmethod
    def validate_coordinates(
        coordinates: np.ndarray,
        crs: str = "EPSG:4326",
        check_bounds: bool = True
    ) -> ValidationResult:
        """
        Validate coordinate array.

        Args:
            coordinates: Nx2 array of coordinates
            crs: Coordinate Reference System
            check_bounds: Whether to check if coordinates are in reasonable bounds

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        # Check shape
        if coordinates.ndim != 2 or coordinates.shape[1] != 2:
            errors.append(f"Coordinates must be Nx2 array, got shape {coordinates.shape}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Check for NaN
        if np.isnan(coordinates).any():
            errors.append("Coordinates contain NaN values")

        # Check bounds for lat/lon
        if check_bounds and crs == "EPSG:4326":
            lons = coordinates[:, 0]
            lats = coordinates[:, 1]

            if not (-180 <= lons.min() and lons.max() <= 180):
                errors.append(f"Longitude out of bounds: [{lons.min()}, {lons.max()}]")

            if not (-90 <= lats.min() and lats.max() <= 90):
                errors.append(f"Latitude out of bounds: [{lats.min()}, {lats.max()}]")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={'n_points': len(coordinates)}
        )
