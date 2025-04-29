"""
Functions for calculating shading losses from wind turbine towers.
"""

import numpy as np
import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib import clearsky, atmosphere, solarposition

def calculate_tower_shadow(latitude, longitude, altitude, times,
                         tower_height, tower_diameter_base, tower_diameter_top, 
                         tower_location, pv_location,
                         dni_extra=1364.0, model='ineichen'):
    """
    Calculate the shading loss from a wind turbine tower on a PV array.
    
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
        
    Returns
    -------
    pd.DataFrame
        DataFrame containing:
        - shadow_length: Length of tower shadow in meters
        - shadow_width: Width of tower shadow in meters
        - is_shaded: Boolean indicating if PV point is shaded
        - shading_loss: Fraction of irradiance lost due to shading (0-1)
        - ghi: Global horizontal irradiance (W/m^2)
        - dni: Direct normal irradiance (W/m^2) 
        - dhi: Diffuse horizontal irradiance (W/m^2)
    """
    # Create location object
    site = Location(latitude, longitude, altitude=altitude)
    
    # Calculate solar position
    solar_position = site.get_solarposition(times)
    
    # Get clear sky data
    clear_sky = site.get_clearsky(times, model=model, dni_extra=dni_extra)
    
    # Calculate shadow dimensions
    zenith = solar_position['apparent_zenith']
    azimuth = solar_position['azimuth']
    
    # Convert to radians and flip azimuth by 180° for shadow direction
    zenith_rad = np.radians(zenith)
    shadow_azimuth = (azimuth + 180) % 360  # Shadow is opposite to sun direction
    azimuth_rad = np.radians(shadow_azimuth)
    
    # Calculate shadow length
    shadow_length = tower_height * np.tan(zenith_rad)
    
    # Calculate effective tower diameter at PV point based on distance
    pv_vector = np.array([
        pv_location[0] - tower_location[0],
        pv_location[1] - tower_location[1]
    ])[:, np.newaxis]
    
    # Shadow vectors for each time
    shadow_vectors = np.vstack([
        shadow_length * np.sin(azimuth_rad),  # East component
        shadow_length * np.cos(azimuth_rad)   # North component
    ])
    
    # Calculate shadow unit vectors
    shadow_lengths = np.sqrt(np.sum(shadow_vectors**2, axis=0))
    shadow_unit = shadow_vectors / shadow_lengths
    
    # Project PV vector onto shadow lines
    projection_lengths = np.sum(pv_vector * shadow_unit, axis=0)
    
    # Calculate perpendicular distances
    perp_vectors = pv_vector - (projection_lengths * shadow_unit)
    perp_distances = np.sqrt(np.sum(perp_vectors**2, axis=0))
    
    # Calculate effective tower diameter at shadow intersection point
    # Linear interpolation based on projection distance along shadow
    diameter_slope = (tower_diameter_top - tower_diameter_base) / tower_height
    effective_diameter = np.where(
        projection_lengths > 0,
        tower_diameter_base + diameter_slope * (projection_lengths / np.tan(zenith_rad)),
        tower_diameter_base
    )
    
    # Calculate shadow width (perpendicular to shadow direction)
    shadow_width = effective_diameter * np.cos(zenith_rad)
    
    # Point is shaded if:
    # 1. Projection length is positive and less than shadow length
    # 2. Perpendicular distance is less than half shadow width
    is_shaded = ((projection_lengths > 0) & 
                 (projection_lengths < shadow_length) &
                 (perp_distances < shadow_width/2))
    
    # Calculate shading loss
    # Assume complete blocking of direct radiation when shaded
    shading_loss = np.where(is_shaded,
                           clear_sky['dni'] / (clear_sky['ghi'] + 1e-6),
                           0)
    
    # Create results DataFrame
    results = pd.DataFrame({
        'shadow_length': shadow_length,
        'shadow_width': shadow_width,
        'is_shaded': is_shaded,
        'shading_loss': shading_loss,
        'ghi': clear_sky['ghi'],
        'dni': clear_sky['dni'],
        'dhi': clear_sky['dhi']
    }, index=times)
    
    return results

def calculate_annual_shading_loss(latitude, longitude, altitude,
                                tower_height, tower_diameter_base, tower_diameter_top,
                                tower_location, pv_location,
                                year=None, freq='h'):
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
    results = calculate_tower_shadow(
        latitude, longitude, altitude, times,
        tower_height, tower_diameter_base, tower_diameter_top,
        tower_location, pv_location
    )
    
    # Calculate annual energy loss fraction
    total_insolation = results['ghi'].sum()
    shaded_energy_loss = (results['ghi'] * results['shading_loss']).sum()
    annual_loss_fraction = shaded_energy_loss / total_insolation
    
    return results, annual_loss_fraction 