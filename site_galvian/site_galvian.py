import pandas as pd

def read_electricity_price(file_path, include_leap_year=False, exchange_rate=59.45):
    """
    Read electricity price data from Excel file and convert to USD/MWh.
    
    Args:
        file_path (str): Path to the Excel file containing price data
        include_leap_year (bool): If False (default), remove February 29th data
        exchange_rate (float): Exchange rate from RD$ to USD (default: 59.45)
    
    Returns:
        pd.DataFrame: DataFrame with columns 'datetime' and 'price' in USD/MWh
    """
    # Read the Excel file
    df = pd.read_excel(
        file_path,
        usecols=['Fecha', 'Hora', 'Barra de Referencia Palamara 138 kV']
    )
    # Combine 'Fecha' and 'Hora' into a single datetime column
    df['datetime'] = pd.to_datetime(df['Fecha'].astype(str) + ' ' + df['Hora'].astype(str))
    # Convert price to numeric
    df['price'] = pd.to_numeric(df['Barra de Referencia Palamara 138 kV'], errors='coerce')
    # Remove February 29th if not including leap year
    if not include_leap_year:
        df = df[~((df['datetime'].dt.month == 2) & (df['datetime'].dt.day == 29))]
    # Convert price from RD$/MWh to USD/MWh
    df['price'] = df['price'] / exchange_rate
    # Return only the relevant columns
    return df[['datetime', 'price']]

