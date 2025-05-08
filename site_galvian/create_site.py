import pandas as pd
import xarray as xr
from py_wake.site.xrsite import XRSite
import numpy as np

def create_site_from_vortex(file_path, start=None, end=None):
    """
    Create an XRSite object from a Vortex wind data file, with optional time period selection.
    Args:
        file_path (str): Path to the Vortex wind data file
        start (str or None): Optional start datetime (e.g., '2020-01-01' or '2020-01-01 00:00')
        end (str or None): Optional end datetime (e.g., '2020-12-31' or '2020-12-31 23:59')
    Returns:
        XRSite: Configured XRSite object
    """
    # Read the data, skipping the first 4 header lines
    df = pd.read_csv(
        file_path,
        sep=r"\s+",  # Use regex separator for whitespace (raw string)
        skiprows=4,
        usecols=[0, 1, 2, 3],  # YYYYMMDD, HHMM, M(m/s), D(deg)
        names=["date", "hour", "wind_speed", "wind_direction"]
    )

    # Combine date and hour into a datetime
    df["datetime"] = pd.to_datetime(
        df["date"].astype(str) + df["hour"].astype(str).str.zfill(4),
        format="%Y%m%d%H%M"
    )

    # Filter by time period if start/end are provided
    if start is not None:
        df = df[df["datetime"] >= pd.to_datetime(start)]
    if end is not None:
        df = df[df["datetime"] <= pd.to_datetime(end)]

    # For time series, XRSite requires a 'P' variable (probability/time weight)
    P = [1.0] * len(df)

    # Use integer indices for the 'time' coordinate
    time_idx = np.arange(len(df))
    ws = df["wind_speed"].values
    wd = df["wind_direction"].values
    ti = [1/x+0.04 for x in ws]

    # Create xarray Dataset for XRSite
    ds = xr.Dataset(
        {
            "wind_speed": ("time", ws),
            "wind_direction": ("time", wd),
            "P": ("time", P),
            "TI": ("time", ti),  # Using IEC 61400 simplified TI model TI = a/U+b
            "datetime": ("time", time_idx)  # Store actual datetimes as a variable
        },
        coords={"time": time_idx}
    )

    site = XRSite(ds, interp_method='nearest')
    return site

def write_results_to_csv(results, output_file):
    """
    Write simulation results to a CSV file suitable for Excel pivot tables.
    Args:
        results (list of dict or pd.DataFrame): Simulation results with required columns.
        output_file (str): Path to the output CSV file.
    Columns:
        datetime| wind direction | wind speed | turbulence intensity | turbine no. | power |  WS_eff | TI_eff
        - datetime is formatted as dd.mm.yyyy HH:MM
    """
    # Convert to DataFrame if needed
    df = pd.DataFrame(results)
    # Format the datetime column
    df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%d.%m.%Y %H:%M')
    # Ensure column order
    columns = [
        'datetime',
        'wind direction',
        'wind speed',
        'turbulence intensity',
        'turbine no.',
        'power',
        'WS_eff',
        'TI_eff'
    ]
    df = df[columns]
    # Write to CSV
    df.to_csv(output_file, index=False, sep=',') 