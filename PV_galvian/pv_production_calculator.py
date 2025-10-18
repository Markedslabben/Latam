import pandas as pd
import numpy as np
try:
    import pvlib
    from pvlib.iotools import get_pvgis_tmy
    from pvlib.pvsystem import retrieve_sam, calcparams_cec, singlediode
    from pvlib.solarposition import get_solarposition
    from pvlib.irradiance import get_total_irradiance
    from pvlib.temperature import sapm_cell
except ImportError:
    pvlib = None
    get_pvgis_tmy = None
    retrieve_sam = None
    calcparams_cec = None
    singlediode = None
    get_solarposition = None
    get_total_irradiance = None
    sapm_cell = None


def fetch_pvgis_tmy(latitude, longitude, startyear=2020, endyear=2020, timezone='Etc/GMT+4'):
    """
    Fetch TMY data from PVGIS for the given location using pvlib.
    Returns a DataFrame with hourly data or raises an error if unavailable.
    """
    if pvlib is None or get_pvgis_tmy is None:
        raise ImportError("pvlib is not installed. Please install pvlib to use this function.")
    try:
        tmy, meta = get_pvgis_tmy(latitude, longitude, map_variables=True, startyear=startyear, endyear=endyear, outputformat='csv', timezone=timezone)
        print(f"Fetched TMY data: {tmy.shape[0]} rows, columns: {list(tmy.columns)}")
        return tmy
    except Exception as e:
        print(f"Error fetching PVGIS TMY data: {e}")
        raise


def process_tmy_data(tmy):
    """
    Process and validate TMY DataFrame. Extract GHI, DNI, DHI, and temperature. Convert time index to datetime.
    Returns a DataFrame with columns: ['time', 'GHI', 'DNI', 'DHI', 'T2m']
    """
    required_cols = ['G(h)', 'Gb(n)', 'Gd(h)', 'T2m']
    col_map = {'G(h)': 'GHI', 'Gb(n)': 'DNI', 'Gd(h)': 'DHI', 'T2m': 'T2m'}
    missing = [col for col in required_cols if col not in tmy.columns]
    if missing:
        raise ValueError(f"Missing required columns in TMY data: {missing}")
    df = tmy[required_cols].rename(columns=col_map).copy()
    # Try to get time index
    if hasattr(tmy.index, 'tz'):
        df['time'] = tmy.index.tz_convert('UTC').tz_localize(None)
    else:
        df['time'] = pd.to_datetime(tmy.index)
    # Reorder columns
    df = df[['time', 'GHI', 'DNI', 'DHI', 'T2m']]
    print(f"Processed TMY data: {df.shape[0]} rows, columns: {list(df.columns)}")
    print(df.describe())
    return df


def select_pv_module(module_type='LONGi_LR5_72HPH_540M'):
    """
    Select a PV module from the CEC database using pvlib. Defaults to Longi Hi-MO 5m (LR5-72HPH-540M).
    Returns a Series of module parameters.
    """
    if pvlib is None or retrieve_sam is None:
        raise ImportError("pvlib is not installed. Please install pvlib to use this function.")
    try:
        cec_modules = retrieve_sam('CECMod')
        if module_type not in cec_modules:
            raise ValueError(f"Module '{module_type}' not found in CEC database.")
        module = cec_modules[module_type]
        print(f"Selected PV module: {module_type}")
        print(module[['STC', 'Vmp', 'Imp', 'Voc', 'Isc', 'alpha_sc', 'beta_oc', 'gamma_r', 'Technology']])
        return module
    except Exception as e:
        print(f"Error selecting PV module: {e}")
        raise


def calculate_solar_position(df, latitude, longitude, timezone='UTC'):
    """
    Calculate solar position (zenith, azimuth) for each timestamp in df using pvlib.
    Adds 'zenith' and 'azimuth' columns to the DataFrame.
    """
    if pvlib is None or get_solarposition is None:
        raise ImportError("pvlib is not installed. Please install pvlib to use this function.")
    times = pd.DatetimeIndex(df['time']).tz_localize('UTC').tz_convert(timezone)
    solpos = get_solarposition(times, latitude, longitude)
    df['zenith'] = solpos['zenith'].values
    df['azimuth'] = solpos['azimuth'].values
    print(f"Solar position calculated: zenith (min, max) = ({df['zenith'].min():.2f}, {df['zenith'].max():.2f}), azimuth (min, max) = ({df['azimuth'].min():.2f}, {df['azimuth'].max():.2f})")
    return df


def calculate_poa_irradiance(df, azimuth, tilt, albedo=0.2, model='hay'):
    """
    Calculate plane-of-array (POA) irradiance for each hour using pvlib's get_total_irradiance.
    Adds 'POA' column to the DataFrame.
    """
    if pvlib is None or get_total_irradiance is None:
        raise ImportError("pvlib is not installed. Please install pvlib to use this function.")
    poa = get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=azimuth,
        solar_zenith=df['zenith'],
        solar_azimuth=df['azimuth'],
        dni=df['DNI'],
        ghi=df['GHI'],
        dhi=df['DHI'],
        albedo=albedo,
        model=model
    )
    df['POA'] = poa['poa_global']
    print(f"POA irradiance calculated: POA (min, max, mean) = ({df['POA'].min():.2f}, {df['POA'].max():.2f}, {df['POA'].mean():.2f})")
    return df


def calculate_cell_temperature(df, module, wind_speed=1.0):
    """
    Calculate PV cell temperature using pvlib's SAPM model.
    Adds 'Tcell' column to the DataFrame.
    """
    if pvlib is None or sapm_cell is None:
        raise ImportError("pvlib is not installed. Please install pvlib to use this function.")
    # Use module parameters if available, else use typical values
    noct = module.get('NOCT', 45)  # Nominal Operating Cell Temp (°C)
    # SAPM model parameters (default values if not in module)
    a = module.get('a', -3.56)
    b = module.get('b', -0.075)
    deltaT = module.get('deltaT', 3)
    # Use SAPM cell temperature model
    df['Tcell'] = sapm_cell(
        poa_global=df['POA'],
        temp_air=df['T2m'],
        wind_speed=wind_speed,
        a=a,
        b=b,
        deltaT=deltaT
    )
    print(f"Cell temperature calculated: Tcell (min, max, mean) = ({df['Tcell'].min():.2f}, {df['Tcell'].max():.2f}, {df['Tcell'].mean():.2f})")
    return df


def calculate_power_output(df, module, inverter_efficiency=0.97):
    """
    Calculate DC and AC power output using pvlib's single diode model and a simple inverter efficiency.
    Adds 'Pdc' and 'Pac' columns to the DataFrame. Normalizes to 1 kWp.
    """
    if pvlib is None or calcparams_cec is None or singlediode is None:
        raise ImportError("pvlib is not installed. Please install pvlib to use this function.")
    # Extract module parameters for CEC model
    params = calcparams_cec(
        effective_irradiance=df['POA'],
        temp_cell=df['Tcell'],
        alpha_sc=module['alpha_sc'],
        a_ref=module['a_ref'],
        I_L_ref=module['I_L_ref'],
        I_o_ref=module['I_o_ref'],
        R_sh_ref=module['R_sh_ref'],
        R_s=module['R_s'],
        Adjust=module.get('Adjust', 0)
    )
    # Calculate single diode output
    diode = singlediode(*params, ivcurve_pnts=None)
    df['Pdc'] = diode['p_mp']
    # Normalize to 1 kWp
    stc_power = module['STC']
    df['Pdc'] = df['Pdc'] / stc_power * 1000  # kW per kWp
    # AC power with simple inverter efficiency
    df['Pac'] = df['Pdc'] * inverter_efficiency
    # Energy in kWh for each hour (since data is hourly)
    df['kWh/kWp'] = df['Pac']  # Already per hour, per kWp
    print(f"Power output calculated: Pac (min, max, mean) = ({df['Pac'].min():.3f}, {df['Pac'].max():.3f}, {df['Pac'].mean():.3f})")
    return df


def calculate_pv_production(latitude, longitude, azimuth, tilt, module_type='LONGi_LR5_72HPH_540M',
                            start='2024-01-01 00:00', end='2024-12-31 23:59',
                            timezone='UTC'):
    """
    Calculate hourly PV production for a 1 kWp solar PV system at a specified location using pvlib and PVGIS.

    Parameters:
        latitude (float): Latitude of the site in degrees
        longitude (float): Longitude of the site in degrees
        azimuth (float): Azimuth angle of the PV array (degrees, 180=south)
        tilt (float): Tilt angle of the PV array (degrees)
        module_type (str): PV module type or identifier (default: 'LONGi_LR5_72HPH_540M')
        start (str): Start datetime (default: '2024-01-01 00:00')
        end (str): End datetime (default: '2024-12-31 23:59')
        timezone (str): Timezone for the calculation (default: 'UTC')

    Returns:
        pd.DataFrame: DataFrame with columns ['time', 'kWh/kWp']
    """
    # Input validation
    if not (-90 <= latitude <= 90):
        raise ValueError('Latitude must be between -90 and 90 degrees.')
    if not (-180 <= longitude <= 180):
        raise ValueError('Longitude must be between -180 and 180 degrees.')
    if not (0 <= azimuth <= 360):
        raise ValueError('Azimuth must be between 0 and 360 degrees.')
    if not (0 <= tilt <= 90):
        raise ValueError('Tilt must be between 0 and 90 degrees.')
    # Additional validation for module_type, start, end, timezone can be added here

    print(f"Inputs validated: lat={latitude}, lon={longitude}, az={azimuth}, tilt={tilt}, module={module_type}")
    print(f"Calculation period: {start} to {end} ({timezone})")

    # Try to fetch TMY data from PVGIS
    try:
        tmy = fetch_pvgis_tmy(latitude, longitude, timezone=timezone)
        print(f"TMY data fetched successfully. DataFrame shape: {tmy.shape}")
    except ImportError as e:
        print(e)
        return pd.DataFrame(columns=['time', 'kWh/kWp'])
    except Exception as e:
        print(f"Failed to fetch TMY data: {e}")
        return pd.DataFrame(columns=['time', 'kWh/kWp'])

    # Process and validate TMY data
    try:
        df = process_tmy_data(tmy)
    except Exception as e:
        print(f"Error processing TMY data: {e}")
        return pd.DataFrame(columns=['time', 'kWh/kWp'])

    # Select PV module
    try:
        module = select_pv_module(module_type)
    except ImportError as e:
        print(e)
        return pd.DataFrame(columns=['time', 'kWh/kWp'])
    except Exception as e:
        print(f"Failed to select PV module: {e}")
        return pd.DataFrame(columns=['time', 'kWh/kWp'])

    # Calculate solar position
    try:
        df = calculate_solar_position(df, latitude, longitude, timezone=timezone)
    except ImportError as e:
        print(e)
        return pd.DataFrame(columns=['time', 'kWh/kWp'])
    except Exception as e:
        print(f"Failed to calculate solar position: {e}")
        return pd.DataFrame(columns=['time', 'kWh/kWp'])

    # Calculate POA irradiance
    try:
        df = calculate_poa_irradiance(df, azimuth, tilt)
    except ImportError as e:
        print(e)
        return pd.DataFrame(columns=['time', 'kWh/kWp'])
    except Exception as e:
        print(f"Failed to calculate POA irradiance: {e}")
        return pd.DataFrame(columns=['time', 'kWh/kWp'])

    # Calculate cell temperature
    try:
        df = calculate_cell_temperature(df, module)
    except ImportError as e:
        print(e)
        return pd.DataFrame(columns=['time', 'kWh/kWp'])
    except Exception as e:
        print(f"Failed to calculate cell temperature: {e}")
        return pd.DataFrame(columns=['time', 'kWh/kWp'])

    # Calculate power output
    try:
        df = calculate_power_output(df, module)
    except ImportError as e:
        print(e)
        return pd.DataFrame(columns=['time', 'kWh/kWp'])
    except Exception as e:
        print(f"Failed to calculate power output: {e}")
        return pd.DataFrame(columns=['time', 'kWh/kWp'])

    # Return DataFrame with time and kWh/kWp columns
    return df[['time', 'kWh/kWp']]


if __name__ == "__main__":
    # Example test run (will only validate inputs and print info)
    df = calculate_pv_production(19.71814, -71.35602 , 180, 12)
    print(df.head()) 