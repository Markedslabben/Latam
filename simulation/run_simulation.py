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


def main():
    site = create_site_from_vortex("Inputdata/vortex.serie.850535.6m 164m UTC-04.0 ERA5.txt")
    turbine = create_nordex_n164_turbine("Inputdata/Nordex N164.csv")
    wfm = PropagateDownwind(site, turbine, NOJDeficit(site,turbine))

    # Galvian layout
    turbine_coords = pd.read_csv("output/turbine_coordinates.csv")
    x = turbine_coords["x_coord"].values
    y = turbine_coords["y_coord"].values

    # Extract time, wind direction, and wind speed arrays from site dataset
    times = site.ds['time'].values
    wd = site.ds['wind_direction'].values
    ws = site.ds['wind_speed'].values

    sim_res = wfm(x, y, wd=wd, ws=ws, time=times)
    print("Power output per turbine:", sim_res.Power.values)

if __name__ == "__main__":
    main() 