import importlib
import turbine_galvian.create_turbine
import site_galvian.create_site
from turbine_galvian.create_turbine import create_nordex_n164_turbine
from site_galvian.create_site import create_site_from_vortex, create_wind_distribution, create_weibull_site
from py_wake.wind_farm_models import PropagateDownwind
from py_wake.deficit_models import BastankhahGaussianDeficit
import pandas as pd
import numpy as np
import xarray as xr

importlib.reload(turbine_galvian.create_turbine)
importlib.reload(site_galvian.create_site)

def main(start_year=2014, end_year=2024, n_sectors=12, include_leap_year=False):
    # 1. Create time series site from Vortex data
    time_site = create_site_from_vortex(
        "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt",
        start=f"{start_year}-01-01 00:00",
        end=f"{start_year}-12-31 23:59",
        include_leap_year=include_leap_year
    )

    # 2. Create Weibull parameters and sector frequencies from time series site
    freq, A, k, wd_centers, TI , weibull_fits= create_wind_distribution(time_site, n_sectors=n_sectors)

    # 3. Create WeibullSite
    weibull_site = create_weibull_site(freq, A, k, wd_centers,TI)

    # 4. Load turbine model
    turbine = create_nordex_n164_turbine("Inputdata/Nordex N164.csv")

    # 5. Load turbine layout
    turbine_coords = pd.read_csv("Inputdata/turbine_layout_14.csv")
    x = turbine_coords["x_coord"].values
    y = turbine_coords["y_coord"].values

    # 6. Set up wind farm model with WeibullSite
    wfm = PropagateDownwind(weibull_site, turbine, wake_deficitModel=BastankhahGaussianDeficit())

    # 7. Run wind farm simulation (using wind distribution, not time series)
    sim_res = wfm(x, y)

    # 8. Print or return results for further analysis/plotting
    #print("Annual energy production per turbine (Weibull):", sim_res.AEP().values)
   # print("Total AEP (Weibull):", sim_res.AEP().sum().values)
   # print("Weibull parameters per sector:")
   # print("freq:", freq)
  #  print("A:", A)
  #  print("k:", k)
  #  print("wd_centers:", wd_centers)
  #  print("TI:", TI)
    return sim_res, weibull_site,wfm

if __name__ == "__main__":
    sim_res, weibull_site,wfm = main() 

