import pandas as pd
import xarray as xr
from py_wake.site.xrsite import XRSite
import numpy as np

def create_site_from_vortex(file_path):
    """
    Create an XRSite object from a Vortex wind data file.
    Args:
        file_path (str): Path to the Vortex wind data file
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