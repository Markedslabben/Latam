import pandas as pd
import xarray as xr
from py_wake.site.xrsite import XRSite

# Path to your Vortex wind data file
file_path = "Inputdata/vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt"

def main():
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
    # Here, we use a dummy array of ones (all time steps equally likely)
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

    print("Dataset structure (including P):")
    print(ds)

    site = XRSite(ds, interp_method='nearest')
    print("XRSite object created successfully!")
    print(site)

    # Test: Query wind speed and direction at two example turbine locations and two time steps
    x = [0, 100]  # example x coordinates (meters)
    y = [0, 100]  # example y coordinates (meters)
    h = [163, 163]  # hub heights (meters)
    times = [0, 1]  # first and second time step

    ws = site.ws(x, y, h, time=times)
    wd = site.wd(x, y, h, time=times)

    print("\nTest query results:")
    print("Wind speeds at x, y, h, time:")
    print(ws)
    print("Wind directions at x, y, h, time:")
    print(wd)

if __name__ == "__main__":
    main() 