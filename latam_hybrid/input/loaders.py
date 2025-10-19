"""
Generic file loaders for various data formats.

This module provides low-level file loading utilities used by domain-specific readers.
Supports CSV, Excel, HDF5, and text formats commonly used in energy analysis.
"""

from pathlib import Path
from typing import Optional, Union, List, Dict, Any
import pandas as pd
import numpy as np


class FileLoader:
    """
    Generic file loading utilities with validation.
    """

    @staticmethod
    def load_csv(
        filepath: Union[str, Path],
        parse_dates: Optional[Union[bool, List[str]]] = True,
        index_col: Optional[Union[int, str]] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load CSV file with robust error handling.

        Args:
            filepath: Path to CSV file
            parse_dates: Column(s) to parse as dates
            index_col: Column to use as index
            **kwargs: Additional arguments passed to pd.read_csv

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or malformed

        Example:
            >>> df = FileLoader.load_csv("data.csv", index_col=0)
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        if filepath.stat().st_size == 0:
            raise ValueError(f"CSV file is empty: {filepath}")

        try:
            df = pd.read_csv(
                filepath,
                parse_dates=parse_dates,
                index_col=index_col,
                **kwargs
            )
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file {filepath}: {e}")

        if df.empty:
            raise ValueError(f"CSV file loaded but contains no data: {filepath}")

        return df

    @staticmethod
    def load_excel(
        filepath: Union[str, Path],
        sheet_name: Union[str, int] = 0,
        parse_dates: Optional[Union[bool, List[str]]] = True,
        index_col: Optional[Union[int, str]] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load Excel file with robust error handling.

        Args:
            filepath: Path to Excel file
            sheet_name: Sheet name or index to load
            parse_dates: Column(s) to parse as dates
            index_col: Column to use as index
            **kwargs: Additional arguments passed to pd.read_excel

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty, malformed, or sheet not found

        Example:
            >>> df = FileLoader.load_excel("prices.xlsx", sheet_name="2024")
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Excel file not found: {filepath}")

        if filepath.stat().st_size == 0:
            raise ValueError(f"Excel file is empty: {filepath}")

        try:
            df = pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                parse_dates=parse_dates,
                index_col=index_col,
                engine='openpyxl',
                **kwargs
            )
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file {filepath}: {e}")

        if df.empty:
            raise ValueError(f"Excel sheet loaded but contains no data: {filepath}")

        return df

    @staticmethod
    def load_text_file(
        filepath: Union[str, Path],
        encoding: str = 'utf-8',
        skiprows: Optional[int] = None,
        delimiter: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Load text file (space/tab delimited) with robust error handling.

        Args:
            filepath: Path to text file
            encoding: File encoding
            skiprows: Number of rows to skip
            delimiter: Column delimiter (None for whitespace)
            **kwargs: Additional arguments passed to pd.read_csv

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty or malformed

        Example:
            >>> df = FileLoader.load_text_file("vortex.txt", skiprows=3, delimiter=None)
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Text file not found: {filepath}")

        if filepath.stat().st_size == 0:
            raise ValueError(f"Text file is empty: {filepath}")

        try:
            df = pd.read_csv(
                filepath,
                encoding=encoding,
                skiprows=skiprows,
                delimiter=delimiter,
                delim_whitespace=(delimiter is None),
                **kwargs
            )
        except Exception as e:
            raise ValueError(f"Failed to parse text file {filepath}: {e}")

        if df.empty:
            raise ValueError(f"Text file loaded but contains no data: {filepath}")

        return df

    @staticmethod
    def load_hdf5(
        filepath: Union[str, Path],
        key: str
    ) -> pd.DataFrame:
        """
        Load HDF5 file with robust error handling.

        Args:
            filepath: Path to HDF5 file
            key: HDF5 key/group to load

        Returns:
            DataFrame with loaded data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is empty, malformed, or key not found

        Example:
            >>> df = FileLoader.load_hdf5("data.h5", key="wind_timeseries")
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"HDF5 file not found: {filepath}")

        if filepath.stat().st_size == 0:
            raise ValueError(f"HDF5 file is empty: {filepath}")

        try:
            df = pd.read_hdf(filepath, key=key)
        except KeyError:
            raise ValueError(f"Key '{key}' not found in HDF5 file: {filepath}")
        except Exception as e:
            raise ValueError(f"Failed to parse HDF5 file {filepath}: {e}")

        if df.empty:
            raise ValueError(f"HDF5 data loaded but contains no data: {filepath}")

        return df

    @staticmethod
    def save_csv(
        df: pd.DataFrame,
        filepath: Union[str, Path],
        index: bool = True,
        **kwargs
    ) -> Path:
        """
        Save DataFrame to CSV with error handling.

        Args:
            df: DataFrame to save
            filepath: Output file path
            index: Whether to write index
            **kwargs: Additional arguments passed to pd.to_csv

        Returns:
            Path to saved file

        Example:
            >>> FileLoader.save_csv(df, "output/results.csv")
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            df.to_csv(filepath, index=index, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to save CSV file {filepath}: {e}")

        return filepath

    @staticmethod
    def save_excel(
        df: pd.DataFrame,
        filepath: Union[str, Path],
        sheet_name: str = 'Sheet1',
        index: bool = True,
        **kwargs
    ) -> Path:
        """
        Save DataFrame to Excel with error handling.

        Args:
            df: DataFrame to save
            filepath: Output file path
            sheet_name: Sheet name
            index: Whether to write index
            **kwargs: Additional arguments passed to pd.to_excel

        Returns:
            Path to saved file

        Example:
            >>> FileLoader.save_excel(df, "output/results.xlsx", sheet_name="Results")
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            df.to_excel(
                filepath,
                sheet_name=sheet_name,
                index=index,
                engine='openpyxl',
                **kwargs
            )
        except Exception as e:
            raise ValueError(f"Failed to save Excel file {filepath}: {e}")

        return filepath

    @staticmethod
    def list_excel_sheets(filepath: Union[str, Path]) -> List[str]:
        """
        List all sheet names in an Excel file.

        Args:
            filepath: Path to Excel file

        Returns:
            List of sheet names

        Example:
            >>> sheets = FileLoader.list_excel_sheets("data.xlsx")
            >>> print(sheets)  # ['2023', '2024', 'Summary']
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Excel file not found: {filepath}")

        try:
            excel_file = pd.ExcelFile(filepath, engine='openpyxl')
            return excel_file.sheet_names
        except Exception as e:
            raise ValueError(f"Failed to read Excel file {filepath}: {e}")

    @staticmethod
    def detect_delimiter(
        filepath: Union[str, Path],
        n_lines: int = 10
    ) -> str:
        """
        Auto-detect delimiter in text file.

        Args:
            filepath: Path to text file
            n_lines: Number of lines to examine

        Returns:
            Detected delimiter (or None for whitespace)

        Example:
            >>> delim = FileLoader.detect_delimiter("data.txt")
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        # Read first n lines
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [f.readline() for _ in range(n_lines)]

        # Check common delimiters
        delimiters = [',', ';', '\t', '|']
        delimiter_counts = {d: 0 for d in delimiters}

        for line in lines:
            for delim in delimiters:
                delimiter_counts[delim] += line.count(delim)

        # Find most common delimiter
        max_count = max(delimiter_counts.values())
        if max_count == 0:
            return None  # Whitespace delimited

        for delim, count in delimiter_counts.items():
            if count == max_count:
                return delim

        return None
