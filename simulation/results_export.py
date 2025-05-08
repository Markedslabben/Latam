import pandas as pd

def export_simulation_results_to_dataframe(sim_res, site, times):
    """
    Extracts simulation results and returns a DataFrame suitable for Excel pivot tables.
    Args:
        sim_res: Simulation result object (from py_wake)
        site: Site object used in the simulation
        times: Array of datetime or time indices
    Returns:
        pd.DataFrame: DataFrame with columns:
            datetime| wind direction | wind speed | turbulence intensity | turbine no. | power |  WS_eff | TI_eff
            - datetime is formatted as dd.mm.yyyy HH:MM
    """
    wind_speed = site.ds['wind_speed'].values
    wind_direction = site.ds['wind_direction'].values
    turbulence_intensity = site.ds['TI'].values
    # Try to get actual datetimes if available, else fallback to times
    datetimes = site.ds['datetime'].values if 'datetime' in site.ds else times
    power = sim_res.Power.values  # shape: (time, turbine)
    # WS_eff and TI_eff may not always be present
    WS_eff = getattr(sim_res, 'WS_eff', None)
    TI_eff = getattr(sim_res, 'TI_eff', None)

    results = []
    for t_idx, dt in enumerate(datetimes):
        for turb_idx in range(power.shape[1]):
            row = {
                'datetime': pd.to_datetime(dt),
                'wind direction': wind_direction[t_idx],
                'wind speed': wind_speed[t_idx],
                'turbulence intensity': turbulence_intensity[t_idx],
                'turbine no.': turb_idx + 1,
                'power': power[t_idx, turb_idx],
                'WS_eff': WS_eff[t_idx, turb_idx] if WS_eff is not None else None,
                'TI_eff': TI_eff[t_idx, turb_idx] if TI_eff is not None else None,
            }
            results.append(row)

    df = pd.DataFrame(results)
    df['datetime'] = pd.to_datetime(df['datetime']).dt.strftime('%d.%m.%Y %H:%M')
    columns = [
        'datetime',
        'wind direction',
        'wind speed',
        'turbulence intensity',
        'turbine no.',
        'power',
        'WS_eff',
        'TI_eff'
    ]
    df = df[columns]
    return df 