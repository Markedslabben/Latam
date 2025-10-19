"""
Market data readers for electricity prices and economic data.

Supports Excel and CSV formats for spot market prices.
"""

from pathlib import Path
from typing import Optional, Union, Dict
import pandas as pd
import numpy as np

from ..core import MarketData, TimeZoneOffset, DataValidator
from .loaders import FileLoader


class ElectricityPriceReader:
    """
    Reader for electricity spot market price data.

    Supports various price data formats from energy markets.
    """

    @staticmethod
    def read_excel(
        filepath: Union[str, Path],
        price_column: str = 'price',
        time_column: Optional[str] = None,
        sheet_name: Union[str, int] = 0,
        currency: str = "USD",
        exchange_rate: float = 1.0,
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4,
        skiprows: Optional[int] = None,
        validate: bool = True
    ) -> MarketData:
        """
        Read electricity price data from Excel.

        Args:
            filepath: Path to Excel file
            price_column: Price column name (currency/MWh or currency/kWh)
            time_column: Timestamp column (None if index)
            sheet_name: Sheet name or index
            currency: Currency code (USD, EUR, CLP, etc.)
            exchange_rate: Exchange rate to USD (if needed)
            timezone_offset: UTC offset
            skiprows: Number of header rows to skip
            validate: Whether to validate data

        Returns:
            MarketData object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If validation fails

        Example:
            >>> prices = ElectricityPriceReader.read_excel(
            ...     "Spotmarket Prices 2024.xlsx",
            ...     sheet_name="Hourly",
            ...     price_column="Price_USD_MWh"
            ... )
        """
        filepath = Path(filepath)

        # Load Excel
        if time_column:
            df = FileLoader.load_excel(
                filepath,
                sheet_name=sheet_name,
                parse_dates=[time_column],
                skiprows=skiprows
            )
            df = df.set_index(time_column)
        else:
            df = FileLoader.load_excel(
                filepath,
                sheet_name=sheet_name,
                index_col=0,
                parse_dates=True,
                skiprows=skiprows
            )

        # Rename price column to standard name
        df = df.rename(columns={price_column: 'price'})

        # Ensure price column exists
        if 'price' not in df.columns:
            raise ValueError(
                f"Price column '{price_column}' not found. "
                f"Available columns: {df.columns.tolist()}"
            )

        # Keep only price column
        df = df[['price']]

        # Convert MWh to kWh if prices seem too high (heuristic)
        median_price = df['price'].median()
        if median_price > 1000:  # Likely USD/MWh, convert to USD/kWh
            df['price'] = df['price'] / 1000

        # Validate
        if validate:
            # Check for negative prices
            if (df['price'] < 0).any():
                n_negative = (df['price'] < 0).sum()
                print(f"Warning: {n_negative} negative price values found (may be valid in some markets)")

            # Check for unrealistic prices
            if (df['price'] > 1).any():  # > 1 USD/kWh is very high
                n_high = (df['price'] > 1).sum()
                print(f"Warning: {n_high} price values > 1 USD/kWh (unusually high)")

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'sheet_name': sheet_name,
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'Excel',
            'price_stats': {
                'min': float(df['price'].min()),
                'max': float(df['price'].max()),
                'mean': float(df['price'].mean()),
                'median': float(df['price'].median())
            }
        }

        return MarketData(
            timeseries=df,
            currency=currency,
            exchange_rate=exchange_rate,
            timezone_offset=timezone_offset,
            metadata=metadata
        )

    @staticmethod
    def read_csv(
        filepath: Union[str, Path],
        price_column: str = 'price',
        time_column: Optional[str] = None,
        currency: str = "USD",
        exchange_rate: float = 1.0,
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4,
        skiprows: Optional[int] = None,
        validate: bool = True
    ) -> MarketData:
        """
        Read electricity price data from CSV.

        Args:
            filepath: Path to CSV file
            price_column: Price column name
            time_column: Timestamp column (None if index)
            currency: Currency code
            exchange_rate: Exchange rate to USD
            timezone_offset: UTC offset
            skiprows: Number of header rows to skip
            validate: Whether to validate data

        Returns:
            MarketData object

        Example:
            >>> prices = ElectricityPriceReader.read_csv(
            ...     "prices_2024.csv",
            ...     price_column="EUR_per_MWh",
            ...     currency="EUR",
            ...     exchange_rate=1.1
            ... )
        """
        filepath = Path(filepath)

        # Load CSV
        if time_column:
            df = FileLoader.load_csv(
                filepath,
                parse_dates=[time_column],
                skiprows=skiprows
            )
            df = df.set_index(time_column)
        else:
            df = FileLoader.load_csv(
                filepath,
                index_col=0,
                parse_dates=True,
                skiprows=skiprows
            )

        # Rename price column
        df = df.rename(columns={price_column: 'price'})

        # Ensure price column exists
        if 'price' not in df.columns:
            raise ValueError(
                f"Price column '{price_column}' not found. "
                f"Available columns: {df.columns.tolist()}"
            )

        # Keep only price column
        df = df[['price']]

        # Convert MWh to kWh if needed
        median_price = df['price'].median()
        if median_price > 1000:
            df['price'] = df['price'] / 1000

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'CSV',
            'price_stats': {
                'min': float(df['price'].min()),
                'max': float(df['price'].max()),
                'mean': float(df['price'].mean()),
                'median': float(df['price'].median())
            }
        }

        return MarketData(
            timeseries=df,
            currency=currency,
            exchange_rate=exchange_rate,
            timezone_offset=timezone_offset,
            metadata=metadata
        )

    @staticmethod
    def create_flat_price(
        start_date: str,
        end_date: str,
        price_per_kwh: float,
        frequency: str = '1h',
        currency: str = "USD",
        timezone_offset: int = TimeZoneOffset.UTC_MINUS_4
    ) -> MarketData:
        """
        Create flat (constant) price timeseries.

        Useful for simplified economic analysis or baseline scenarios.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            price_per_kwh: Constant price in currency/kWh
            frequency: Time frequency ('1h', '15min', etc.)
            currency: Currency code
            timezone_offset: UTC offset

        Returns:
            MarketData object

        Example:
            >>> prices = ElectricityPriceReader.create_flat_price(
            ...     "2024-01-01", "2024-12-31 23:00",
            ...     price_per_kwh=0.05,  # 50 USD/MWh
            ...     currency="USD"
            ... )
        """
        # Create date range
        index = pd.date_range(start=start_date, end=end_date, freq=frequency)

        # Create constant price
        df = pd.DataFrame({
            'price': price_per_kwh
        }, index=index)

        # Metadata
        metadata = {
            'n_records': len(df),
            'date_range': (df.index.min(), df.index.max()),
            'source_format': 'Generated (flat price)',
            'price_stats': {
                'min': price_per_kwh,
                'max': price_per_kwh,
                'mean': price_per_kwh,
                'median': price_per_kwh
            }
        }

        return MarketData(
            timeseries=df,
            currency=currency,
            exchange_rate=1.0,
            timezone_offset=timezone_offset,
            metadata=metadata
        )


# Convenience function
def read_electricity_prices(
    filepath: Union[str, Path],
    source_type: str = 'auto',
    **kwargs
) -> MarketData:
    """
    Auto-detect format and read electricity price data.

    Args:
        filepath: Path to price data file
        source_type: Source type ('csv', 'excel', or 'auto')
        **kwargs: Additional arguments passed to specific reader

    Returns:
        MarketData object

    Example:
        >>> prices = read_electricity_prices("Spotmarket Prices 2024.xlsx")
        >>> prices = read_electricity_prices("prices.csv", source_type='csv')
    """
    filepath = Path(filepath)

    # Auto-detect format
    if source_type == 'auto':
        suffix = filepath.suffix.lower()
        if suffix in ['.xlsx', '.xls']:
            source_type = 'excel'
        elif suffix == '.csv':
            source_type = 'csv'
        else:
            raise ValueError(f"Cannot auto-detect format for file: {filepath}")

    # Read based on detected type
    if source_type == 'csv':
        return ElectricityPriceReader.read_csv(filepath, **kwargs)
    elif source_type == 'excel':
        return ElectricityPriceReader.read_excel(filepath, **kwargs)
    else:
        raise ValueError(f"Unknown source_type: {source_type}")
