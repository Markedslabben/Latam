import pandas as pd

def read_pvgis(csv_path):
    """
    Reads a PVGIS timeseries CSV file and returns a DataFrame with columns 'time' and 'power'.
    Args:
        csv_path (str): Path to the PVGIS timeseries CSV file.
    Returns:
        pd.DataFrame: DataFrame with columns 'time' and 'power'.
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
    return df

if __name__ == "__main__":
    # Example usage
    csv_path = '../Inputdata/PVGIS timeseries.csv'  # Adjust path as needed
    df = read_pvgis(csv_path)
    print(df.head()) 