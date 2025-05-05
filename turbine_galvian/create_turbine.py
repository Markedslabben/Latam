import numpy as np
import pandas as pd
from py_wake.wind_turbines import WindTurbine
from py_wake.wind_turbines.power_ct_functions import PowerCtTabular
from py_wake.deficit_models.noj import NOJ

def create_nordex_n164_turbine(csv_path="Inputdata/Nordex N164.csv"):
    """
    Create a PyWake WindTurbine object for the Nordex N164 using data from a CSV file.
    Args:
        csv_path (str): Path to the CSV file with columns: wind speed (m/s), power (kW), ct (dmnl)
    Returns:
        WindTurbine: Configured PyWake WindTurbine object
    """
    # Read CSV (comma as decimal separator, handle whitespace)
    df = pd.read_csv(csv_path, header=None, names=["wind_speed", "power_kw", "ct"], sep=",|\t", engine="python")
    # Clean up whitespace and convert to float
    df = df.apply(lambda col: col.astype(str).str.replace(" ", "").astype(float))

    wind_speeds = df["wind_speed"].values
    power = df["power_kw"].values * 1000  # convert kW to W
    ct = df["ct"].values

    # Create power/Ct function with linear interpolation
    power_ct_function = PowerCtTabular(
        wind_speeds,
        power,'kW',
        ct
    )

    # Create WindTurbine object
    turbine = WindTurbine(
        name="Nordex N164",
        diameter=164,
        hub_height=163,
        powerCtFunction=power_ct_function
    )
    return turbine

def create_turbine_from_csv(csv_path, name, diameter, hub_height):
    """
    Create a PyWake WindTurbine object from a CSV file with wind speed, power (kW), and ct (dmnl).
    Args:
        csv_path (str): Path to the CSV file
        name (str): Turbine name
        diameter (float): Rotor diameter (m)
        hub_height (float): Hub height (m)
        interpolation_kind (str): Interpolation method for power/Ct curves (default: 'linear')
    Returns:
        WindTurbine: Configured PyWake WindTurbine object
    """
    df = pd.read_csv(csv_path, header=None, names=["wind_speed", "power_kw", "ct"], sep=",|\t", engine="python")
    df = df.apply(lambda col: col.astype(str).str.replace(" ", "").astype(float))
    wind_speeds = df["wind_speed"].values
    power = df["power_kw"].values * 1000  # convert kW to W
    ct = df["ct"].values

    return WindTurbine(
        name=name,
        diameter=diameter,
        hub_height=hub_height,
        powerCtFunction=PowerCtTabular(wind_speeds, power, ct)
    ) 