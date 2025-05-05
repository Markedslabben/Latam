import pandas as pd
import xarray as xr
from py_wake.site.xrsite import XRSite

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

    # Set datetime as index
    df = df.set_index("datetime")

    # For time series, XRSite requires a 'P' variable (probability/time weight)
    P = [1.0] * len(df)

    # Create xarray Dataset for XRSite
    ds = xr.Dataset(
        {
            "wind_speed": ("time", df["wind_speed"].values),
            "wind_direction": ("time", df["wind_direction"].values),
            "P": ("time", P)
        },
        coords={"time": df.index}
    )

    site = XRSite(ds, interp_method='nearest')
    return site 