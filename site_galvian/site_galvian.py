import pandas as pd

def read_electricity_price(file_path, include_leap_year=False, exchange_rate=59.45):
    """
    Read electricity price data from Excel file and convert to USD/MWh.
    
    Args:
        file_path (str): Path to the Excel file containing price data
        include_leap_year (bool): If False (default), remove February 29th data
        exchange_rate (float): Exchange rate from RD$ to USD (default: 59.45)
    
    Returns:
        pd.DataFrame: DataFrame with columns 'time' and 'price' in USD/MWh
    """
    # Read the Excel file
    df = pd.read_excel(
        file_path,
        usecols=['Fecha', 'Barra de Referencia Palamara 138 kV'],
        parse_dates=['Barra de Referencia Palamara 138 kV']
    )
    
    # Rename columns for clarity
    df.columns = ['time', 'price']
    
    # Remove February 29th if not including leap year
    if not include_leap_year:
        df = df[~((df['time'].dt.month == 2) & (df['time'].dt.day == 29))]
    
    # Convert price from RD$/MWh to USD/MWh
    df['price'] = df['price'] / exchange_rate
    
    return df 