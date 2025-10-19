import pandas as pd
import numpy as np
from py_wake.wind_turbines import WindTurbine
from py_wake.wind_farm_models.engineering_models import PropagateDownwind
from py_wake.superposition_models import SquaredSum
from py_wake.deficit_models.gaussian import IEA37SimpleBastankhahGaussianDeficit
from py_wake.site import TimeSeriesSite
import os
from py_wake.wind_turbines.power_ct_functions import PowerCtTabular
from py_wake.site.xrsite import XRSite
import xarray as xr

# --- 1. Read Power Curve ---
power_curve_path = 'Inputdata/Nordex N164.csv'
if not os.path.exists(power_curve_path):
    raise FileNotFoundError(f"Power curve file not found: {power_curve_path}")
pc_df = pd.read_csv(power_curve_path, sep=',', header=None, names=['ws', 'power_kW'])
pc_df = pc_df.dropna()
try:
    pc_df['ws'] = pd.to_numeric(pc_df['ws'], errors='raise')
    pc_df['power_kW'] = pd.to_numeric(pc_df['power_kW'], errors='raise')
except Exception as e:
    raise ValueError(f"Error parsing power curve file: {e}")
print(pc_df.head())
print(pc_df.dtypes)

# Use PowerCtTabular for power and Ct curves
default_ct = 0.8  # Use real Ct if available
power_ct_func = PowerCtTabular(
    ws=pc_df['ws'].values,
    power=pc_df['power_kW'].values,
    ct=np.full_like(pc_df['ws'].values, default_ct, dtype=float),
    power_unit='kW'
)

nordex_n164 = WindTurbine(
    name='Nordex N164',
    diameter=164,
    hub_height=163,
    powerCtFunction=power_ct_func
)

# --- 2. Read Turbine Coordinates ---
turbine_coord_path = 'output/turbine_coordinates.csv'
if not os.path.exists(turbine_coord_path):
    raise FileNotFoundError(f"Turbine coordinates file not found: {turbine_coord_path}")
turbine_df = pd.read_csv(turbine_coord_path)
if not {'x_coord', 'y_coord'}.issubset(turbine_df.columns):
    raise ValueError("Turbine coordinates file must have 'x_coord' and 'y_coord' columns.")
x = turbine_df['x_coord'].values
y = turbine_df['y_coord'].values
n_turbines = len(x)

# --- 3. Read Wind Speed and Direction Time Series ---
def read_vortex_timeseries(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Wind time series file not found: {filepath}")
    with open(filepath) as f:
        for i, line in enumerate(f):
            if line.strip().startswith('YYYYMMDD'):
                header_line = i
                break
        else:
            raise ValueError("Could not find header line in wind time series file.")
    df = pd.read_csv(filepath, sep='\s+', skiprows=header_line+1,
                     names=['date', 'hour', 'ws', 'wd', 'T', 'De', 'PRE', 'RiNumber', 'RH', 'RMOL'])
    return df

ws_df = read_vortex_timeseries('Inputdata/vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt')
wind_speeds = ws_df['ws'].values  # m/s
wind_dirs = ws_df['wd'].values    # deg

# --- 4. Set Up Wake Model ---
import xarray as xr
xr_ds = xr.Dataset({
    'WS': (('time',), wind_speeds),
    'WD': (('time',), wind_dirs),
    'TI': (('time',), np.full_like(wind_speeds, 0.1)),
    'time': (('time',), np.arange(len(wind_speeds)))
})
site = XRSite(xr_ds)
wf_model = PropagateDownwind(site, nordex_n164, IEA37SimpleBastankhahGaussianDeficit(), SquaredSum())

# --- 5. Calculate Hourly Power and Per-Turbine Output (Vectorized Time Series) ---
sim_res = wf_model(
    x, y,
    time=True
)

# Power output per turbine per timestep (kW)
hourly_turbine_power = sim_res.Power  # shape: (n_timesteps, n_turbines)
hourly_power = hourly_turbine_power.sum(axis=1)  # total farm power per hour

total_energy = hourly_power.sum()  # kWh (since each entry is for 1 hour)

# --- 6. Save Results ---
output_df = ws_df[['date', 'hour', 'ws', 'wd']].copy()
output_df['farm_power_kW'] = hourly_power
for i in range(n_turbines):
    output_df[f'turbine_{i+1}_kW'] = hourly_turbine_power[:, i]
output_df.to_csv('output/hourly_farm_and_turbine_power.csv', index=False)

print(f'Total energy produced (Gaussian wake, all hours): {total_energy/1e6:.2f} GWh')
print('Per-turbine and farm hourly output saved to output/hourly_farm_and_turbine_power.csv') 