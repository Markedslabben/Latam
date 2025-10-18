import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the data
file_path = r"C:\Users\klaus\klauspython\Latam\Inputdata\vortex.serie.850689.10y 164m UTC-04.0 ERA5.txt"
df = pd.read_csv(
    file_path,
    sep=r"\s+",
    skiprows=4,
    usecols=[0, 1, 2, 3],  # YYYYMMDD, HHMM, M(m/s), D(deg)
    names=["date", "hour", "wind_speed", "wind_direction"]
)

# Pad hour to 4 digits (e.g., 100 -> 0100)
df['hour'] = df['hour'].astype(str).str.zfill(4)
df['date'] = df['date'].astype(str)

# 2. Parse datetime and extract year
df['datetime'] = pd.to_datetime(df['date'] + df['hour'], format='%Y%m%d%H%M')
df['year'] = df['datetime'].dt.year

# 3. Calculate average wind speed per year
yearly_avg = df.groupby('year')['wind_speed'].mean()

# 4. Calculate 10-year overall average and 2024 deviation
overall_avg = df['wind_speed'].mean()
mean_2024 = yearly_avg.loc[2024]
percent_deviation = 100 * (mean_2024 - overall_avg) / overall_avg

# 5. Print result
print(f"2024 wind speed is {percent_deviation:.2f}% {'above' if percent_deviation > 0 else 'below'} the 10-year average.")

# 6. Plot
plt.figure(figsize=(10,6))
bars = plt.bar(yearly_avg.index, yearly_avg.values, color=['#1f77b4' if y != 2024 else '#ff7f0e' for y in yearly_avg.index])
plt.axhline(overall_avg, color='red', linestyle='--', label='10-year average')

# Annotate 2024 bar
plt.text(2024, mean_2024, f"{percent_deviation:.2f}%", ha='center', va='bottom', color='#ff7f0e', fontweight='bold')

plt.xlabel('Year')
plt.ylabel('Average Wind Speed (m/s)')
plt.title('Average Wind Speed per Year (2014–2024)')
plt.legend()
plt.tight_layout()
plt.show()