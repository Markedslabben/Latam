import pandas as pd
from py_wake.wind_turbines import WindTurbine
from py_wake.wind_turbines.power_ct_functions import PowerCtTabular

# Read power curve data from CSV
df = pd.read_csv("Inputdata/Nordex N164.csv", header=None, names=["wind_speed", "power_kw", "ct"], sep=",|\t", engine="python")

# Clean up whitespace and convert to float
df = df.apply(lambda col: col.astype(str).str.replace(" ", "").astype(float))

wind_speeds = df["wind_speed"].values
power = df["power_kw"].values * 1000  # convert kW to W
ct = df["ct"].values

Gavilan_turbine = WindTurbine(name='Gavilan', 
diameter=164,
hub_height=163,
powerCtFunction=PowerCtTabular(wind_speeds, power,'kW', ct))

print(Gavilan_turbine)