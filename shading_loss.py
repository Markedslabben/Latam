"""
Functions for calculating shading losses from wind turbine towers.
"""

import numpy as np
import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib import clearsky, atmosphere, solarposition

def calculate_turbine_shading(latitude, longitude, altitude, times,
                         tower_height, tower_diameter_base, tower_diameter_top, 
                         tower_location, pv_location,
                         dni_extra=1364.0, model='ineichen',
                         include_rotor_disk=False, rotor_diameter=None, hub_height=None):
    """
    Calculate the shading loss from a wind turbine (tower and optionally rotor disk) on a PV array.
    
    Parameters
    ----------
    latitude : float
        Latitude of the site in degrees
    longitude : float
        Longitude of the site in degrees
    altitude : float
        Altitude of the site in meters
    times : pd.DatetimeIndex
        Times to calculate shading for
    tower_height : float
        Height of the turbine tower in meters
    tower_diameter_base : float
        Diameter of the turbine tower at the base in meters
    tower_diameter_top : float
        Diameter of the turbine tower at the top in meters
    tower_location : tuple of float
        (x, y) coordinates of tower base in meters
    pv_location : tuple of float
        (x, y) coordinates of PV array point in meters
    dni_extra : float, default 1364.0
        Extraterrestrial irradiance in W/m^2
    model : str, default 'ineichen'
        Clear sky model to use ('ineichen' or 'simplified_solis')
    include_rotor_disk : bool, default False
        Whether to include rotor disk shading
    rotor_diameter : float, optional
        Diameter of the rotor disk in meters (required if include_rotor_disk)
    hub_height : float, optional
        Height of the rotor disk center (defaults to tower_height if not given)
    
    Returns
    -------
    pd.DataFrame
        DataFrame containing:
        - shadow_length: Length of tower shadow in meters
        - shadow_width: Width of tower shadow in meters
        - is_shaded: Boolean indicating if PV point is shaded (by tower or rotor)
        - shading_loss: Fraction of irradiance lost due to shading (0-1)
        - is_shaded_tower: Boolean for tower shading
        - is_shaded_rotor: Boolean for rotor disk shading
        - ghi: Global horizontal irradiance (W/m^2)
        - dni: Direct normal irradiance (W/m^2) 
        - dhi: Diffuse horizontal irradiance (W/m^2)
    """
    site = Location(latitude, longitude, altitude=altitude)
    solar_position = site.get_solarposition(times)
    clear_sky = site.get_clearsky(times, model=model, dni_extra=dni_extra)
    zenith = solar_position['apparent_zenith']
    azimuth = solar_position['azimuth']
    zenith_rad = np.radians(zenith)
    shadow_azimuth = (azimuth + 180) % 360
    azimuth_rad = np.radians(shadow_azimuth)
    shadow_length = tower_height * np.tan(zenith_rad)
    pv_vector = np.array([
        pv_location[0] - tower_location[0],
        pv_location[1] - tower_location[1]
    ])[:, np.newaxis]
    shadow_vectors = np.vstack([
        shadow_length * np.sin(azimuth_rad),
        shadow_length * np.cos(azimuth_rad)
    ])
    shadow_lengths = np.sqrt(np.sum(shadow_vectors**2, axis=0))
    shadow_unit = shadow_vectors / shadow_lengths
    projection_lengths = np.sum(pv_vector * shadow_unit, axis=0)
    perp_vectors = pv_vector - (projection_lengths * shadow_unit)
    perp_distances = np.sqrt(np.sum(perp_vectors**2, axis=0))
    diameter_slope = (tower_diameter_top - tower_diameter_base) / tower_height
    effective_diameter = np.where(
        projection_lengths > 0,
        tower_diameter_base + diameter_slope * (projection_lengths / np.tan(zenith_rad)),
        tower_diameter_base
    )
    shadow_width = effective_diameter * np.cos(zenith_rad)
    is_shaded_tower = ((projection_lengths > 0) & 
                 (projection_lengths < shadow_length) &
                 (perp_distances < shadow_width/2))
    is_shaded_rotor = np.zeros_like(is_shaded_tower, dtype=bool)
    if include_rotor_disk:
        if rotor_diameter is None:
            raise ValueError("rotor_diameter must be specified if include_rotor_disk is True")
        if hub_height is None:
            hub_height = tower_height
        # Project PV point into zy plane at hub height (rotor normal points east)
        # Sun must be behind disk (i.e., sun azimuth between 90-270 deg)
        sun_az = azimuth.values if hasattr(azimuth, 'values') else azimuth
        sun_zen = zenith.values if hasattr(zenith, 'values') else zenith
        # Only consider times when sun is in front of disk (90 < az < 270)
        mask = (sun_az > 90) & (sun_az < 270) & (sun_zen < 90)
        # PV point in zy plane relative to disk center
        pv_y = pv_location[1] - tower_location[1]
        pv_z = 0 - hub_height  # PV assumed at ground level (z=0)
        rotor_radius = rotor_diameter / 2
        # For each time, calculate shadow projection in zy plane
        # Project sun vector onto zy plane
        sun_vec_y = np.sin(np.radians(sun_az))
        sun_vec_z = -np.cos(np.radians(sun_zen))  # negative because z is up
        # For each time, find intersection of sun vector with rotor plane at x=0
        # (since disk normal is +x)
        # The shadow of the disk is a circle in zy at x=0, so check if PV is inside
        # For each time, if mask is True, check if sqrt((pv_y)^2 + (pv_z)^2) < rotor_radius
        dist_to_center = np.sqrt((pv_y)**2 + (pv_z)**2)
        is_shaded_rotor[mask] = dist_to_center < rotor_radius
    is_shaded = is_shaded_tower | is_shaded_rotor
    shading_loss = np.where(is_shaded,
                           clear_sky['dni'] / (clear_sky['ghi'] + 1e-6),
                           0)
    results = pd.DataFrame({
        'shadow_length': shadow_length,
        'shadow_width': shadow_width,
        'is_shaded': is_shaded,
        'shading_loss': shading_loss,
        'is_shaded_tower': is_shaded_tower,
        'is_shaded_rotor': is_shaded_rotor,
        'ghi': clear_sky['ghi'],
        'dni': clear_sky['dni'],
        'dhi': clear_sky['dhi']
    }, index=times)
    return results

def calculate_annual_shading_loss(latitude, longitude, altitude,
                                tower_height, tower_diameter_base, tower_diameter_top,
                                tower_location, pv_location,
                                year=None, freq='h', **kwargs):
    """
    Calculate annual shading losses from a wind turbine tower.
    
    Parameters
    ----------
    latitude : float
        Latitude of the site in degrees
    longitude : float
        Longitude of the site in degrees  
    altitude : float
        Altitude of the site in meters
    tower_height : float
        Height of the turbine tower in meters
    tower_diameter_base : float
        Diameter of the turbine tower at the base in meters
    tower_diameter_top : float
        Diameter of the turbine tower at the top in meters
    tower_location : tuple of float
        (x, y) coordinates of tower base in meters
    pv_location : tuple of float
        (x, y) coordinates of PV array point in meters
    year : int, optional
        Year to calculate for. If None, uses current year.
    freq : str, default 'h'
        Frequency of time series
    **kwargs : dict
        Additional keyword arguments for calculate_turbine_shading
        
    Returns
    -------
    pd.DataFrame
        DataFrame containing hourly shading results for the year
    float
        Annual energy loss fraction due to shading
    """
    if year is None:
        year = pd.Timestamp.now().year
        
    # Create annual DatetimeIndex
    times = pd.date_range(f'{year}-01-01', f'{year}-12-31 23:59:59',
                         freq=freq, tz='UTC')
    
    # Calculate shading for all times
    results = calculate_turbine_shading(
        latitude, longitude, altitude, times,
        tower_height, tower_diameter_base, tower_diameter_top,
        tower_location, pv_location, **kwargs
    )
    
    # Calculate annual energy loss fraction
    total_insolation = results['ghi'].sum()
    shaded_energy_loss = (results['ghi'] * results['shading_loss']).sum()
    annual_loss_fraction = shaded_energy_loss / total_insolation
    
    return results, annual_loss_fraction 