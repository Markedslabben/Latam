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

    # Parse 'time' to pandas datetime (UTC)
    df['datetime'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M')
    # Use as local datetime (or rename as needed)
    # Replace the year with 2024
    def safe_replace_year(dt, new_year):
        # If the date would become Feb 29 in a non-leap year, skip it
        try:
            return dt.replace(year=new_year)
        except ValueError:
            # This would only happen if original data had Feb 29, which it doesn't
            return pd.NaT

    #df['datetime_local'] = df['datetime_local'].apply(lambda dt: safe_replace_year(dt, 2024))
    #df = df[df['datetime_local'].notna()].reset_index(drop=True)

    # --- Wrap the first 4 hours to the end of the year ---
    #first_4 = df.iloc[:4].copy()
    #last_day = pd.Timestamp('2024-12-31')
    #hours = [20, 21, 22, 23]
    #first_4['datetime_local'] = [last_day + pd.Timedelta(hours=h) for h in hours]
   # df = pd.concat([df, first_4], ignore_index=True)
   # df = df.sort_values('datetime_local').reset_index(drop=True)
   # # Ensure the DataFrame index is consecutive integers
    df = df.reset_index(drop=True)

    # Shift the power column up by 4 rows to align with a 4-hour time shift
    df['power'] = df['power'].shift(-4)
    df['power'] = df['power'].fillna(0)
    df = df.reset_index(drop=True)

    # Add 30 minutes to the datetime to align with the price data
    df['datetime_local'] = df['datetime'] + pd.Timedelta(minutes=30)

    # Return DataFrame with 'datetime_local' and 'power'
    return df[['datetime_local', 'power']]

if __name__ == "__main__":
    # Example usage
    csv_path = '../Inputdata/PVGIS timeseries.csv'  # Adjust path as needed
    df = read_pvgis(csv_path)
    print(df.head()) 