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
from simulation.results_export import write_results_to_csv


def main():
    site = create_site_from_vortex("Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt",start="2024-01-01",end="2024-12-31")
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
            "TI": ("time", 1/ws+0.04)
        },
        coords={
            "time": np.arange(len(times)),
            "turbine": np.arange(power.shape[1])
        }
    )

    return sim_res

if __name__ == "__main__":
    main()
    sim_res = main()

# Example usage:
write_results_to_csv(sim_res, "my_results.csv")