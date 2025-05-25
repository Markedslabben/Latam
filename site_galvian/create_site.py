import pandas as pd
import xarray as xr
from py_wake.site.xrsite import XRSite
import numpy as np
import scipy.stats


def create_site_from_vortex(file_path, start=None, end=None, include_leap_year=False):
    """
    Create an XRSite object from a Vortex wind data file, with optional time period selection and leap year handling.
    Args:
        file_path (str): Path to the Vortex wind data file
        start (str or None): Optional start datetime (e.g., '2020-01-01' or '2020-01-01 00:00')
        end (str or None): Optional end datetime (e.g., '2020-12-31' or '2020-12-31 23:59')
        include_leap_year (bool): If False (default), ignore Feb 29th data in leap years.
    Returns:
        XRSite: Configured XRSite object
    
    Note:
        Vortex input files contain leap years (i.e., 8784 hours for leap years such as 2016, 2020, 2024).
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

    # Remove Feb 29th if include_leap_year is False
    if not include_leap_year:
        df = df[~((df["datetime"].dt.month == 2) & (df["datetime"].dt.day == 29))]

    # For time series, XRSite requires a 'P' variable (probability/time weight)
    P = [1.0] * len(df)

    # Use integer indices for the 'time' coordinate
    time_idx = np.arange(len(df))
    ws = df["wind_speed"].values
    wd = df["wind_direction"].values
    # Turbulence model from IEC 61400-1 NTM sigma = I_ref(0.75*V_hub+b), b=5.6, I_ref=0.12
    ti = [0.12*(0.75+5.6/x) for x in ws]

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

    time_site = XRSite(ds, interp_method='nearest')
    return time_site


def create_wind_distribution(time_site, n_sectors=12):
    """
    Convert time series wind data to Weibull parameters and sector frequencies.

    Args:
        time_site (XRSite): XRSite object containing time series wind data
        n_sectors (int, optional): Number of wind direction sectors (default: 12, i.e., 30-degree bins)
    Returns:
        freq (np.ndarray): Frequency of each wind direction sector
        A (np.ndarray): Weibull scale parameter for each sector
        k (np.ndarray): Weibull shape parameter for each sector
        wd_centers (np.ndarray): Center wind direction of each sector
        TI (np.ndarray): Turbulence intensity for each sector
        weibull_fits (list): List of scipy.stats.rv_frozen Weibull fit objects for each sector
    """
    ws = time_site.ds.wind_speed.values
    wd = time_site.ds.wind_direction.values
    wd_bins = np.linspace(0, 360, n_sectors + 1)
    wd_centers = (wd_bins[:-1] + wd_bins[1:]) / 2
    A = np.zeros(n_sectors)
    k = np.zeros(n_sectors)
    freq = np.zeros(n_sectors)
    TI = np.zeros(n_sectors)
    weibull_fits = []
    wd_digitized = np.digitize(wd, wd_bins, right=False) - 1
    wd_digitized[wd_digitized == n_sectors] = 0  # wrap 360° to sector 0
    for i in range(n_sectors):
        mask = wd_digitized == i
        ws_bin = ws[mask]
        freq[i] = np.sum(mask) / len(ws)
        if len(ws_bin) > 0:
            c, loc, scale = scipy.stats.weibull_min.fit(ws_bin, floc=0)
            A[i] = scale
            k[i] = c
            ws_mean = np.mean(ws_bin)
            TI[i] = 0.12*(0.75+5.6/ws_mean) #IEC 61400-1 NTM sigma = I_ref(0.75*V_hub+b), b=5.6
            weibull_fit = scipy.stats.weibull_min(c, loc=0, scale=scale)
        else:
            A[i] = np.nan
            k[i] = np.nan
            TI[i] = 0.1
            weibull_fit = None
            print(f'Warning: No wind data in sector {i} ({wd_bins[i]}-{wd_bins[i+1]} deg); setting TI to 0.1')
        weibull_fits.append(weibull_fit)
    print('TI per sector:', TI)
    return freq, A, k, wd_centers, TI, weibull_fits

def create_weibull_site(freq, A, k, wd_centers,TI):
    """
    Create a WeibullSite from frequency, Weibull parameters, and wind direction centers.
    Args:
        freq (np.ndarray): Frequency of each wind direction sector
        A (np.ndarray): Weibull scale parameter for each sector
        k (np.ndarray): Weibull shape parameter for each sector
        wd_centers (np.ndarray): Center wind direction of each sector
    Returns:
        WeibullSite: Site object using direction-dependent Weibull wind distribution
    """
    #weibull_site = XRSite(p_wd=freq, A=A, k=k, wd=wd_centers)
    wd_bins = np.linspace(0, 360, len(freq),endpoint=False)
    weibull_site = XRSite(ds=xr.Dataset(data_vars={'Sector_frequency': ('wd', freq), 'Weibull_A': ('wd', A), 
                                                   'Weibull_k': ('wd', k), 'TI': ('wd',TI)},coords={'wd': wd_bins}))
    return weibull_site

def read_electricity_price(file_path, include_leap_year=False, exchange_rate=59.45):
    """
    Read electricity price data from Excel file and convert to USD/MWh.
    
    Args:
        file_path (str): Path to the Excel file containing price data
        include_leap_year (bool): If False (default), remove February 29th data
        exchange_rate (float): Exchange rate from RD$ to USD (default: 59.45)
    
    Returns:
        pd.DataFrame: DataFrame with columns 'time' and 'price' in USD/MWh
    """
    # Read the Excel file
    df = pd.read_excel(
        file_path,
        usecols=['Fecha datetime', 'Barra de Referencia Palamara 138 kV'])
        
    # Rename columns for clarity
    df = df.rename(columns={"Fecha datetime": "datetime"})
    df = df.rename(columns={"Barra de Referencia Palamara 138 kV": "price"})
    df['datetime'] = pd.to_datetime(df['datetime']) # Convert datetime to datetime64
    df=df[['datetime','price']] #Reorder columns
    
    # Remove February 29th if not including leap year
    if not include_leap_year:
        df = df[~((df['datetime'].dt.month == 2) & (df['datetime'].dt.day == 29))]
    df = df.reset_index(drop=True)
    df = df.dropna()
    
    return df 