import importlib
import turbine_galvian.create_turbine 
import site_galvian.create_site 
from turbine_galvian.create_turbine import create_nordex_n164_turbine
from site_galvian.create_site import create_site_from_vortex, read_electricity_price, create_wind_distribution, create_weibull_site
from py_wake.wind_farm_models import PropagateDownwind
from py_wake.deficit_models import NOJDeficit
from py_wake.deficit_models import BastankhahGaussianDeficit
from py_wake.deficit_models import NoWakeDeficit
import pandas as pd
import numpy as np
import xarray as xr
from PV_galvian.read_pvgis import read_pvgis
import calendar
importlib.reload(turbine_galvian.create_turbine)
importlib.reload(site_galvian.create_site)
import matplotlib.pyplot as plt

def main(start_year=2014,end_year=2024):
    # Coordinates lat
    #Lat=19.71814 , Lon= -71.35602     
    
    # Read price data using the new function
    # (Assume the Excel file is the new source)
    electricity_price = read_electricity_price(
        "Inputdata/20250505 Spotmarket Prices_2024.xlsx",
        include_leap_year=False,
        exchange_rate=59.45
    )
    
    # Read pvgis data
    Installed_Capacity = 120e-6 # Convert from W (PVgi) to  MWp and then 120 installed capacity MWp solar
    df_temp = read_pvgis("Inputdata/PVGIS timeseries.csv") # In W
    # Ensure 'power' column is numeric and drop non-numeric rows
    df_temp['power'] = pd.to_numeric(df_temp['power'], errors='coerce')
    df_temp = df_temp.dropna(subset=['power'])
    power_values = df_temp.power.values*Installed_Capacity
    df_pv = pd.DataFrame({
        'time': np.arange(len(power_values)),
        'PV_CF': power_values 
    })
    
    # Read wind data (time_site)
    include_leap_year = False  # Set this flag as needed for the simulation
    time_site = create_site_from_vortex("Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt",start=f"{start_year}-01-01 00:00",end=f"{end_year}-12-31 23:59", include_leap_year=include_leap_year)
    

    # Add 
    turbine = create_nordex_n164_turbine("Inputdata/Nordex N164.csv")
    # Galvian layout
    turbine_coords = pd.read_csv("Inputdata/turbine_layout_13.csv")
    x = turbine_coords["x_coord"].values
    y = turbine_coords["y_coord"].values
    
    # Choose time series or weibull based simulation
    # Use BastankhahGaussianDeficit for wakes and NoWakeDeficit for no wakes.  
    wfm = PropagateDownwind(time_site, turbine, wake_deficitModel=NoWakeDeficit())
    # Extract time, wind direction, and wind speed arrays from time_site dataset
    times = time_site.ds['time'].values
    wd = time_site.ds['wind_direction'].values
    ws = time_site.ds['wind_speed'].values
    sim_res = wfm(x, y, wd=wd, ws=ws, time=times)    
    print("Power output per turbine:", sim_res.Power.values)
    print("sim_res.Power.values.shape:", sim_res.Power.values.shape)
    print("Number of time steps:", len(times))
    print("Number of turbines:", len(x))

    power = sim_res.Power.values
    # If the first dimension is not time, transpose
    if power.shape[0] != len(times):
        print("Transposing power array to match (time, turbine) shape.")
        power = power.T

    # Create a new xarray Dataset with integer 'time' and additional 'datetime' coordinate
    start_time = pd.to_datetime(f'{start_year}-01-01 00:00')
    datetimes = [start_time + pd.Timedelta(hours=i) for i in range(len(times))]
    ds = xr.Dataset(
        {
            "wind_speed": ("time", ws),
            "wind_direction": ("time", wd),
            "P": (("time", "turbine"), power),
            "TI": ("time", 1/ws+0.04),
        },
        coords={
            "time": np.arange(len(times)),  # integer index for PyWake compatibility
            "turbine": np.arange(power.shape[1]),
            "datetime": ("time", datetimes),  # add as a separate coordinate
        }
    )
    # Remove any redundant or duplicate 'time' coordinate assignments
    # Do not assign 'time_index' or overwrite 'time' with datetimes

    sim_res_df = sim_res.to_dataframe()
    # Ensure 'time' is a column, not just an index
    if 'time' not in sim_res_df.columns and 'time' in sim_res_df.index.names:
        sim_res_df = sim_res_df.reset_index()

    # Ensure sim_res_df has a datetime column for merging
    if 'datetime' not in sim_res_df.columns:
        if 'date' in sim_res_df.columns and 'hour' in sim_res_df.columns:
            sim_res_df['datetime'] = pd.to_datetime(sim_res_df['date'].astype(str) + ' ' + sim_res_df['hour'].astype(str))
        else:
            # If you have a time index, reconstruct datetime from start_time and time index
            if 'time' in sim_res_df.columns:
                sim_res_df['datetime'] = [start_time + pd.Timedelta(hours=int(i)) for i in sim_res_df['time']]
            else:
                raise ValueError("sim_res_df must have a 'datetime' column or enough info to construct it.")

    # Now merge on datetime
    sim_res_df['hour_of_year'] = sim_res_df['datetime'].dt.dayofyear * 24 + sim_res_df['datetime'].dt.hour
    electricity_price['hour_of_year'] = electricity_price['datetime'].dt.dayofyear * 24 + electricity_price['datetime'].dt.hour

    sim_res_df = pd.merge(sim_res_df, electricity_price[['hour_of_year', 'price']], on='hour_of_year', how='left')
    
    # (1) Add hour_of_year to sim_res_df if needed (for PV merge)
    if 'hour_of_year' not in sim_res_df.columns:
        sim_res_df['hour_of_year'] = sim_res_df['time'] % 8760  # or use correct hours in year

    # (2) Merge PV data
    df_pv['hour_of_year'] = df_pv['time']
    sim_res_df = pd.merge(sim_res_df, df_pv.drop('time', axis=1), on='hour_of_year', how='left')

    # (3) Now it's safe to drop hour_of_year
    sim_res_df = sim_res_df.drop('hour_of_year', axis=1)

    # Replace hourly index with datetime
    n_timesteps = sim_res_df['time'].max() + 1
    datetimes = pd.date_range(start=f'{start_year}-01-01 00:00', periods=n_timesteps, freq='H')
    tidskolonne = pd.DataFrame({'time': np.arange(n_timesteps), 'datetime': datetimes})
    sim_res_df = pd.merge(sim_res_df, tidskolonne, on='time', how='left')
    sim_res_df = sim_res_df[['datetime_x','time','Power','PV_CF','price','wt','WS_eff','TI_eff','CT','WD','TI','WS']]

    n_turbines = sim_res_df['wt'].nunique() if 'wt' in sim_res_df.columns else (sim_res_df['turbine'].nunique() if 'turbine' in sim_res_df.columns else 1)

    n_years = sim_res_df['datetime_x'].dt.year.nunique()

    return sim_res_df, time_site, sim_res    
    
    

if __name__ == "__main__":
    main()
    sim_res_df, time_site, sim_res = main()
    
    n_years = sim_res_df['datetime_x'].dt.year.nunique()
    n_turbines = sim_res_df['wt'].nunique() if 'wt' in sim_res_df.columns else (sim_res_df['turbine'].nunique() if 'turbine' in sim_res_df.columns else 1)

def calculate_and_save_production_table(sim_res_df_nowake, sim_res_df_wake, output_csv_path):
    import pandas as pd
    import numpy as np
    # --- PARAMETERS ---
    allowed_sectors = [(60, 120), (240, 300)]
    wake_loss_sectors = [(70, 120), (240, 300)]
    rated_power_MW = 7
    n_turbines = 13
    n_years = sim_res_df_nowake['datetime_x'].dt.year.nunique()

    def sector_mask(df, sector_list, wd_col='WD'):
        if wd_col not in df.columns:
            wd_col = 'wind_direction'
        mask = np.zeros(len(df), dtype=bool)
        for s, e in sector_list:
            if s < e:
                mask |= (df[wd_col] >= s) & (df[wd_col] < e)
            else:
                mask |= (df[wd_col] >= s) | (df[wd_col] < e)
        return mask

    # 1. Energy production with all losses (GWh/yr, sector management)
    mask_allowed = sector_mask(sim_res_df_wake, allowed_sectors)
    prod_allowed = sim_res_df_wake.loc[mask_allowed, 'Power'].sum() / 1e9 / n_years  # GWh/yr

    # 2. Full load hours (with all losses and sector management)
    flh_allowed = prod_allowed * 1e3 / (n_turbines * rated_power_MW)  # MWh to kWh, then divide by installed MW

    # 3. Capacity factor (%)
    cf_allowed = prod_allowed * 1e6 / (n_turbines * rated_power_MW * 8760) * 100  # GWh to Wh

    # 4. Wake loss % (in sectors 70-120 and 240-300)
    mask_wake_loss = sector_mask(sim_res_df_wake, wake_loss_sectors)
    prod_nowake_wake = sim_res_df_nowake.loc[mask_wake_loss, 'Power'].sum()
    prod_wake_wake = sim_res_df_wake.loc[mask_wake_loss, 'Power'].sum()
    wake_loss_percent = 100 * (prod_nowake_wake - prod_wake_wake) / prod_nowake_wake if prod_nowake_wake > 0 else np.nan

    # 5. Sector management loss % (no sector management vs with sector management, both with wake)
    total_prod_wake = sim_res_df_wake['Power'].sum() / n_years  # W*hr/yr
    prod_allowed_wake = sim_res_df_wake.loc[mask_allowed, 'Power'].sum() / n_years
    sector_mgmt_loss_percent = 100 * (total_prod_wake - prod_allowed_wake) / total_prod_wake if total_prod_wake > 0 else np.nan

    # --- Make Table ---
    table = pd.DataFrame({
        "Metric": [
            "Annual Production (GWh/yr, all losses, sector mgmt)",
            "Full Load Hours (h/yr)",
            "Capacity Factor (%)",
            "Wake Loss (%) (sectors 70-120, 240-300)",
            "Sector Mgmt Loss (%)"
        ],
        "Value": [
            f"{prod_allowed:.2f}",
            f"{flh_allowed:.0f}",
            f"{cf_allowed:.2f}",
            f"{wake_loss_percent:.2f}",
            f"{sector_mgmt_loss_percent:.2f}"
        ]
    })
    table.to_csv(output_csv_path, index=False)
    print(f"Saved production summary table to {output_csv_path}")
