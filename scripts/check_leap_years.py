import pandas as pd
import sys

try:
    # Read the Vortex data file
    file_path = "Inputdata/vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
    print(f"Reading file: {file_path}")
    
    df = pd.read_csv(
        file_path,
        sep=r"\s+",  # Use regex separator for whitespace
        skiprows=4,
        usecols=[0, 1],  # YYYYMMDD, HHMM
        names=["date", "hour"],
        encoding='utf-8'
    )
    
    print(f"Successfully read {len(df)} rows")
    
    # Convert date to datetime
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + df['hour'].astype(str).str.zfill(4), 
                                   format='%Y%m%d%H%M')
    
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