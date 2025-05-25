import pandas as pd
import re

def read_pvgis(csv_path):
    """
    Reads a PVGIS timeseries CSV file and returns a DataFrame with columns 'time' and 'power'.
    Args:
        csv_path (str): Path to the PVGIS timeseries CSV file.
    Returns:
        pd.DataFrame: DataFrame with columns 'time' and 'power'.
    
    Note:
        PVGIS input files ignore leap years (no Feb 29th; 8760 hours per year) and are probably in UTC+0 timezone.
    """
    # Find the header row (the one that starts with 'time')
    with open(csv_path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.lower().startswith('time'):
                header_row = i
                break
    # Read the CSV, skipping the metadata rows
    df = pd.read_csv(csv_path, skiprows=header_row)
    # Select only the 'time' and 'P' columns, and rename for clarity
    df = df[['time', 'P']].rename(columns={'P': 'power'})
    # Only keep rows where 'time' matches the pattern YYYYMMDD:HHMM
    mask = df['time'].astype(str).str.match(r'^\d{8}:\d{4}$', na=False)
    # Only keep rows where 'power' is numeric (not NaN, not a string)
    df['power'] = pd.to_numeric(df['power'], errors='coerce')
    mask = mask & df['power'].notna()
    df = df[mask].reset_index(drop=True)
    return df

if __name__ == "__main__":
    # Example usage
    csv_path = '../Inputdata/PVGIS timeseries.csv'  # Adjust path as needed
    df = read_pvgis(csv_path)
    print(df.head()) 