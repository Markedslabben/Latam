import importlib
import turbine_galvian.create_turbine 
import site_galvian.create_site 
from turbine_galvian.create_turbine import create_nordex_n164_turbine
from site_galvian.create_site import create_site_from_vortex
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

def main(start_year=2024,end_year=2024):
    # Coordinates lat
    #Lat=19.71814 , Lon= -71.35602     
    
    # Read price data 
    Exchange_rate = 59.45 # RD$ per USD
    electricity_price = pd.read_csv("Inputdata/Electricity price 2024 grid node.csv") # In RD$
    electricity_price['price'] = electricity_price['price']/Exchange_rate # Convert to USD
    

    # Read pvgis data
    Installed_Capacity = 120e6 # Convert from W (PVgi) to 120 MWp installed capacity kWp solar
    df_temp = read_pvgis("Inputdata/PVGIS timeseries.csv")
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
    turbine_coords = pd.read_csv("Inputdata/turbine_layout_14.csv")
    x = turbine_coords["x_coord"].values
    y = turbine_coords["y_coord"].values
    
    # Choose time series or weibull based simulation
    # Use BastankhahGaussianDeficit for wakes and NoWakeDeficit for no wakes.  
    wfm = PropagateDownwind(time_site, turbine, wake_deficitModel=BastankhahGaussianDeficit())
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

    # Create a new xarray Dataset with integer indices for time and turbine
    # This is for exporting results to excel and for analyses of profitability
    ds = xr.Dataset(
        {
            "wind_speed": ("time", ws),
            "wind_direction": ("time", wd),
            "P": (("time", "turbine"), power),
            "TI": ("time", 1/ws+0.04),
        },
        coords={
            "time": np.arange(len(times)),
            "turbine": np.arange(power.shape[1])
        }
    )

    # Convert integer time indices to datetime, starting from start_year-01-01 00:00
    start_time = pd.to_datetime(f'{start_year}-01-01 00:00')
    ds['2time'] = ('time', [start_time + pd.Timedelta(hours=i) for i in ds['time'].values])
    #import IPython; IPython.embed()
    sim_res_df = sim_res.to_dataframe()
    # Ensure 'time' is a column, not just an index
    if 'time' not in sim_res_df.columns and 'time' in sim_res_df.index.names:
        sim_res_df = sim_res_df.reset_index()
    # Repeat electricity price for every year by merging on hour_of_year
    hours_in_year = len(electricity_price)
    sim_res_df['hour_of_year'] = sim_res_df['time'] % hours_in_year
    electricity_price['hour_of_year'] = electricity_price['time']
    sim_res_df = pd.merge(sim_res_df, electricity_price.drop('time', axis=1), on='hour_of_year', how='left')
    
    # Repeat PV data for every year by merging on hour_of_year
    df_pv['hour_of_year'] = df_pv['time']
    sim_res_df = pd.merge(sim_res_df, df_pv.drop('time', axis=1), on='hour_of_year', how='left')
    
    sim_res_df = sim_res_df.drop('hour_of_year', axis=1)
    # Replace hourly index with datetime
    n_timesteps = sim_res_df['time'].max() + 1
    datetimes = pd.date_range(start=f'{start_year}-01-01 00:00', periods=n_timesteps, freq='H')
    tidskolonne = pd.DataFrame({'time': np.arange(n_timesteps), 'datetime': datetimes})
    sim_res_df = pd.merge(sim_res_df, tidskolonne, on='time', how='left')
    return sim_res_df, time_site, sim_res    
    
    

if __name__ == "__main__":
    main()
    sim_res_df, time_site, sim_res = main()
    
