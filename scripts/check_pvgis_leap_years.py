import pandas as pd
import sys
import os

# Add parent directory to path to import latam_hybrid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latam_hybrid.core import get_solar_data_file

try:
    # Read the PVGIS timeseries file using path helper
    file_path = get_solar_data_file()
    print(f"Reading file: {file_path}")
    
    # Read the file, skipping metadata rows
    with open(file_path, encoding='utf-8') as f:
        for i, line in enumerate(f):
            if line.lower().startswith('time'):
                header_row = i
                break
    
    # Read only the time and power columns
    df = pd.read_csv(file_path, skiprows=header_row, usecols=['time', 'P'])
    print(f"Successfully read {len(df)} rows")
    
    # Filter out any non-time rows (metadata or comments)
    df = df[df['time'].str.match(r'^\d{8}:\d{4}$', na=False)]
    print(f"After filtering valid time rows: {len(df)} rows")
    
    # Convert time column to datetime
    df['datetime'] = pd.to_datetime(df['time'], format='%Y%m%d:%H%M')
    
    # Check for February 29th entries
    feb_29 = df[df['datetime'].dt.strftime('%m-%d') == '02-29']
    if len(feb_29) > 0:
        print("\nFound February 29th entries in these years:")
        print(feb_29['datetime'].dt.year.unique())
        print(f"\nTotal number of February 29th entries: {len(feb_29)}")
    else:
        print("\nNo February 29th entries found in the data")
    
    # Check total hours per year
    hours_per_year = df.groupby(df['datetime'].dt.year).size()
    print("\nHours per year in the data:")
    print(hours_per_year)
    
    # Check if any year has 8784 hours (leap year) or 8760 hours (non-leap year)
    print("\nYears with 8784 hours (leap year):")
    print(hours_per_year[hours_per_year == 8784].index.tolist())
    print("\nYears with 8760 hours (non-leap year):")
    print(hours_per_year[hours_per_year == 8760].index.tolist())
    
    # Print first few rows for verification
    print("\nFirst few rows of data:")
    print(df.head())
    
except Exception as e:
    print(f"Error occurred: {str(e)}", file=sys.stderr)
    raise 