"""Path utilities for accessing package data and resources."""

import os
from pathlib import Path
from typing import Optional


def get_package_root() -> Path:
    """
    Get the root directory of the latam_hybrid package.

    Returns:
        Path: Absolute path to latam_hybrid package directory

    Examples:
        >>> root = get_package_root()
        >>> print(root)
        /path/to/latam_hybrid
    """
    # This file is in latam_hybrid/core/paths.py
    # Go up two levels to get to latam_hybrid/
    return Path(__file__).parent.parent.resolve()


def get_data_dir() -> Path:
    """
    Get the Inputdata directory within the package.

    Returns:
        Path: Absolute path to Inputdata directory

    Examples:
        >>> data_dir = get_data_dir()
        >>> print(data_dir)
        /path/to/latam_hybrid/Inputdata
    """
    return get_package_root() / "Inputdata"


def get_data_file(filename: str, subdir: Optional[str] = None) -> Path:
    """
    Get absolute path to a data file in the Inputdata directory.

    Args:
        filename: Name of the data file
        subdir: Optional subdirectory within Inputdata (e.g., 'GISdata')

    Returns:
        Path: Absolute path to the data file

    Raises:
        FileNotFoundError: If the file does not exist

    Examples:
        >>> # Get wind data file
        >>> wind_file = get_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

        >>> # Get GIS file
        >>> gis_file = get_data_file("Planningarea.gpkg", subdir="GISdata")

        >>> # Get turbine file
        >>> turbine_file = get_data_file("Nordex N164.csv")
    """
    data_dir = get_data_dir()

    if subdir:
        file_path = data_dir / subdir / filename
    else:
        file_path = data_dir / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {file_path}\n"
            f"Looking in: {data_dir}"
        )

    return file_path


def get_wind_data_file(filename: str) -> Path:
    """
    Get path to wind data file in Inputdata directory.

    Args:
        filename: Name of wind data file (e.g., "vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")

    Returns:
        Path: Absolute path to wind data file

    Examples:
        >>> wind_file = get_wind_data_file("vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt")
    """
    return get_data_file(filename)


def get_solar_data_file(filename: str = "PVGIS timeseries.csv") -> Path:
    """
    Get path to solar data file in Inputdata directory.

    Args:
        filename: Name of solar data file (default: "PVGIS timeseries.csv")

    Returns:
        Path: Absolute path to solar data file

    Examples:
        >>> solar_file = get_solar_data_file()
    """
    return get_data_file(filename)


def get_turbine_file(filename: str = "Nordex N164.csv") -> Path:
    """
    Get path to turbine specification file in Inputdata directory.

    Args:
        filename: Name of turbine file (default: "Nordex N164.csv")

    Returns:
        Path: Absolute path to turbine file

    Examples:
        >>> turbine_file = get_turbine_file()
    """
    return get_data_file(filename)


def get_layout_file(filename: str) -> Path:
    """
    Get path to turbine layout file in Inputdata directory.

    Args:
        filename: Name of layout file (e.g., "Turbine_layout_13.csv")

    Returns:
        Path: Absolute path to layout file

    Examples:
        >>> layout_file = get_layout_file("Turbine_layout_13.csv")
    """
    return get_data_file(filename)


def get_gis_file(filename: str) -> Path:
    """
    Get path to GIS file in Inputdata/GISdata directory.

    Args:
        filename: Name of GIS file (e.g., "Planningarea.gpkg")

    Returns:
        Path: Absolute path to GIS file

    Examples:
        >>> gis_file = get_gis_file("Planningarea.gpkg")
    """
    return get_data_file(filename, subdir="GISdata")


def get_price_file(filename: str = "Electricity price 2024 grid node.csv") -> Path:
    """
    Get path to electricity price file in Inputdata directory.

    Args:
        filename: Name of price file (default: "Electricity price 2024 grid node.csv")

    Returns:
        Path: Absolute path to price file

    Examples:
        >>> price_file = get_price_file()
    """
    return get_data_file(filename)


def list_data_files(subdir: Optional[str] = None, pattern: str = "*") -> list[Path]:
    """
    List all files in the Inputdata directory or subdirectory.

    Args:
        subdir: Optional subdirectory within Inputdata
        pattern: Glob pattern to filter files (default: "*")

    Returns:
        list[Path]: List of file paths matching the pattern

    Examples:
        >>> # List all files in Inputdata
        >>> files = list_data_files()

        >>> # List all CSV files
        >>> csv_files = list_data_files(pattern="*.csv")

        >>> # List all GIS files
        >>> gis_files = list_data_files(subdir="GISdata", pattern="*.gpkg")
    """
    data_dir = get_data_dir()

    if subdir:
        search_dir = data_dir / subdir
    else:
        search_dir = data_dir

    if not search_dir.exists():
        return []

    return sorted(search_dir.glob(pattern))


# Convenience constants
PACKAGE_ROOT = get_package_root()
DATA_DIR = get_data_dir()
GIS_DATA_DIR = DATA_DIR / "GISdata"
