import pandas as pd
from simulation.results_export import extract_results_for_csv, write_results_to_csv

def write_results_to_csv(results, output_file):
    """
    Write simulation results to a CSV file suitable for Excel pivot tables.
    Args:
        results (list of dict or pd.DataFrame): Simulation results with required columns.
        output_file (str): Path to the output CSV file.
    Columns:
        datetime| wind direction | wind speed | turbulence intensity | turbine no. | power |  WS_eff | TI_eff
        - datetime is formatted as dd.mm.yyyy HH:MM
    """
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
    df.to_csv(output_file, index=False, sep=',') 