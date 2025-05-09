import importlib
import turbine_galvian.create_turbine
import site_galvian.create_site 
importlib.reload(turbine_galvian.create_turbine)
importlib.reload(site_galvian.create_site)
from turbine_galvian.create_turbine import create_nordex_n164_turbine
from site_galvian.create_site import create_site_from_vortex
from py_wake.wind_farm_models import PropagateDownwind
from py_wake.deficit_models import NOJDeficit
import pandas as pd
import numpy as np
import xarray as xr
from PV_galvian.read_pvgis import read_pvgis

def main():
    # Coordinates lat
    #Lat=19.71814 , Lon= -71.35602     
    # Read price data 
    electricity_price = pd.read_csv("Inputdata/Electricity price 2024 grid node.csv")
    # Read pvgis data
    df_temp = read_pvgis("Inputdata/PVGIS timeseries.csv")
    
    # Get values for Feb 28 (hours 1416-1439) to duplicate for Feb 29
    feb28_values = df_temp.power[1416:1440].values
    
    # Create array with leap year by inserting Feb 29 values
    power_values = np.concatenate([
        df_temp.power[0:1440].values,    # Jan 1 - Feb 28
        feb28_values,                     # Feb 29 (copied from Feb 28) 
        df_temp.power[1440:8760].values  # Mar 1 - Dec 31
    ])
    power_values = np.array(power_values,dtype=float)
    Installed_Capacity = 120 # installed capacity kWp  solar
    df_pv = pd.DataFrame({
        'time': np.arange(0,8784),
        'PV_CF': power_values*Installed_Capacity
    })
    
    
    
    
    site = create_site_from_vortex("Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt",start="2024-01-01 00:00",end="2024-12-31 23:59")
    
    # Add 
    turbine = create_nordex_n164_turbine("Inputdata/Nordex N164.csv")
    wfm = PropagateDownwind(site, turbine, wake_deficitModel=NOJDeficit())

    # Galvian layout
    turbine_coords = pd.read_csv("output/turbine_coordinates.csv")
    x = turbine_coords["x_coord"].values
    y = turbine_coords["y_coord"].values

    # Extract time, wind direction, and wind speed arrays from site dataset
    times = site.ds['time'].values
    wd = site.ds['wind_direction'].values
    ws = site.ds['wind_speed'].values

    sim_res = wfm(x, y, wd=wd, ws=ws, time=np.arange(len(times)))
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

    # Convert integer time indices to datetime, starting from 2024-01-01 00:00
    start_time = pd.to_datetime('2024-01-01 00:00')
    ds['2time'] = ('time', [start_time + pd.Timedelta(hours=i) for i in ds['time'].values])


    sim_res_df = sim_res.to_dataframe()
    sim_res_df= pd.merge(sim_res_df, electricity_price,on='time')
    sim_res_df = pd.merge(sim_res_df,df_pv,on='time')
    # Replace hourly index with datetime
    datetimes = pd.date_range(start='2024-01-01 00:00', periods=8784, freq='H')
    tidskolonne=pd.DataFrame()
    tidskolonne['time']=np.arange(0,8784)
    tidskolonne['datetime']=datetimes
    sim_res_df=pd.merge(sim_res_df,tidskolonne,on='time')
    return sim_res_df,site



if __name__ == "__main__":
    main()
    sim_res_df,site = main()
    
