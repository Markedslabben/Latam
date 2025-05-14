import numpy as np
import matplotlib.pyplot as plt
from scipy.special import gamma
import windrose

# Try to import windrose, fallback to matplotlib if not available
try:
    from windrose import WindroseAxes
    _has_windrose = True
    print("uses windrose")
except ImportError:
    _has_windrose = False
    print("does not use windrose")

def plot_wind_rose_from_site(site):
    """
    Plot a wind rose from a PyWake Site object (e.g., XRSite) using sector frequencies and color-coded by mean wind speed.
    Args:
        site: PyWake Site object with .ds['wd'], .ds['Sector_frequency'], .ds['Weibull_A'], .ds['Weibull_k']
    """
    wd = site.ds['wd'].values
    freq = site.ds['Sector_frequency'].values
    A = site.ds['Weibull_A'].values
    k = site.ds['Weibull_k'].values

    # Remove duplicate 360° if present
    if wd[-1] == 360:
        wd = wd[:-1]
        freq = freq[:-1]
        A = A[:-1]
        k = k[:-1]

    # Calculate mean wind speed for each sector using Weibull parameters
    mean_ws = A * gamma(1 + 1 / k)

    if _has_windrose:
        # Use windrose library for a more advanced plot
        ax = WindroseAxes.from_ax()
        # Repeat each sector according to its frequency (for windrose histogram)
        # We'll create a synthetic dataset for windrose
        n_samples = 10000
        sector_samples = np.random.choice(len(wd), size=n_samples, p=freq/freq.sum())
        wd_samples = wd[sector_samples]
        ws_samples = mean_ws[sector_samples]
        bars = ax.bar(wd_samples, ws_samples, normed=True, opening=1, edgecolor='white', bins=8, cmap=plt.cm.viridis)
        ax.set_title('Wind Rose (Weibull Sectors, colored by mean wind speed)')
        # Add colorbar in upper right
        cbar = ax.figure.colorbar(bars, ax=ax, orientation='vertical', pad=0.1, fraction=0.05, anchor=(1.0, 1.0))
        cbar.set_label('Mean wind speed (m/s)')
        print("bruker windrose")
        plt.savefig('windrose.png')
        plt.show()
        print("ferdig")
    else:
        # Fallback to simple polar plot
        width = np.deg2rad(site.ds.attrs.get('sector_width', 30.0))
        angles = np.deg2rad(wd)
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        bars = ax.bar(angles, freq, width=width, bottom=0.0, align='center', edgecolor='k', color=plt.cm.viridis((mean_ws-mean_ws.min())/(mean_ws.max()-mean_ws.min())))
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_title('Wind Rose (Weibull Sectors, colored by mean wind speed)')
        sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=mean_ws.min(), vmax=mean_ws.max()))
        sm.set_array([])
        # Place colorbar in upper right
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.1, fraction=0.05, anchor=(1.0, 1.0))
        cbar.set_label('Mean wind speed (m/s)')
        print("bruker matplotlib")
        plt.show()

def plot_wbl_site(site, ws_range=None):
    """
    Plot Weibull distributions for each wind direction sector in a PyWake Site object.
    Args:
        site: PyWake Site object with .ds['wd'], .ds['Weibull_A'], .ds['Weibull_k']
        ws_range: Optional, tuple (min_ws, max_ws) for wind speed range
    """
    wd = site.ds['wd'].values
    A = site.ds['Weibull_A'].values
    k = site.ds['Weibull_k'].values
    n_sectors = len(wd)
    colors = plt.cm.viridis(np.linspace(0, 1, n_sectors))

    # Remove duplicate 360° if present
    if wd[-1] == 360:
        wd = wd[:-1]
        A = A[:-1]
        k = k[:-1]
        n_sectors -= 1
        colors = colors[:-1]

    # Wind speed range
    if ws_range is None:
        min_A = np.nanmin(A)
        max_A = np.nanmax(A)
        ws = np.linspace(0, max_A * 3, 200)
    else:
        ws = np.linspace(ws_range[0], ws_range[1], 200)

    plt.figure(figsize=(10, 6))
    for i in range(n_sectors):
        if np.isnan(A[i]) or np.isnan(k[i]):
            continue
        pdf = (k[i] / A[i]) * (ws / A[i]) ** (k[i] - 1) * np.exp(-(ws / A[i]) ** k[i])
        mean_ws = A[i] * gamma(1 + 1 / k[i])
        label = f"{int(wd[i])}°: A={A[i]:.2f}, k={k[i]:.2f}, mean={mean_ws:.2f}"
        plt.plot(ws, pdf, color=colors[i], label=label)
        # Annotate mean wind speed
        plt.axvline(mean_ws, color=colors[i], linestyle='--', alpha=0.5)
        plt.text(mean_ws, max(pdf)*0.8, f"{mean_ws:.2f}", color=colors[i], fontsize=8, rotation=90, va='bottom', ha='right')

    plt.xlabel('Wind speed (m/s)')
    plt.ylabel('Probability density')
    plt.title('Weibull Distributions per Wind Direction Sector')
    plt.legend(fontsize=8, loc='upper right', ncol=2)
    plt.tight_layout()
    plt.show()

def plot_wind_speed_histogram(site, n_bins=20, n_samples=10000):
    """
    Plot a histogram of wind speeds from a PyWake Site object.
    Args:
        site: PyWake Site object (XRSite or Weibull/distribution site)
        n_bins: Number of bins for the histogram (default: 20)
        n_samples: Number of synthetic samples for Weibull/distribution sites
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import weibull_min
    from scipy.special import gamma

    # Try to get time series wind speeds
    if 'wind_speed' in site.ds:
        ws = site.ds['wind_speed'].values
    # Otherwise, synthesize from Weibull parameters and sector frequency
    elif 'Weibull_A' in site.ds and 'Weibull_k' in site.ds and 'Sector_frequency' in site.ds:
        A = site.ds['Weibull_A'].values
        k = site.ds['Weibull_k'].values
        freq = site.ds['Sector_frequency'].values
        wd = site.ds['wd'].values
        # Remove duplicate 360° if present
        if wd[-1] == 360:
            A = A[:-1]
            k = k[:-1]
            freq = freq[:-1]
        # Generate synthetic wind speed samples
        ws = np.array([])
        for i in range(len(A)):
            n = int(n_samples * freq[i] / freq.sum())
            if n > 0 and not (np.isnan(A[i]) or np.isnan(k[i])):
                ws = np.concatenate([ws, weibull_min.rvs(c=k[i], scale=A[i], size=n)])
    else:
        raise ValueError("Site object does not contain wind speed or Weibull parameters.")

    plt.figure(figsize=(8, 5))
    plt.hist(ws, bins=n_bins, color='skyblue', edgecolor='k', alpha=0.8, density=True)
    plt.xlabel('Wind speed (m/s)')
    plt.ylabel('Probability density')
    plt.title('Wind Speed Distribution (Histogram)')
    plt.tight_layout()
    plt.show()

def plot_production_profiles(sim_res_df):
    """
    Plot yearly, seasonal, and diurnal production profiles from a DataFrame with 'Power' and 'datetime' columns.
    Args:
        sim_res_df: DataFrame with at least 'Power' and 'datetime' columns (hourly data, multiple years)
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    # Ensure datetime is a pandas datetime
    if not np.issubdtype(sim_res_df['datetime'].dtype, np.datetime64):
        sim_res_df['datetime'] = pd.to_datetime(sim_res_df['datetime'])

    # Add year and month columns to avoid duplicate column names
    sim_res_df['year'] = sim_res_df['datetime'].dt.year
    sim_res_df['month'] = sim_res_df['datetime'].dt.month

    # Yearly production (sum per year)
    all_years = np.arange(2014, 2025)  # 2014 to 2024 inclusive
    yearly = sim_res_df.groupby('year')['Power'].sum().reindex(all_years, fill_value=0)

    # Seasonal profile (mean monthly sum over all years)
    monthly = sim_res_df.groupby(['year', 'month'])['Power'].sum().reset_index()
    monthly_avg = monthly.groupby('month')['Power'].mean()

    # Diurnal profile (mean hourly sum over all years)
    sim_res_df['hour'] = sim_res_df['datetime'].dt.hour
    diurnal = sim_res_df.groupby(['hour'])['Power'].mean()

    # Font sizes (increased by 30%)
    base_title = 18
    base_label = 16
    base_tick = 14
    title_size = int(base_title * 1.3)  # 23
    label_size = int(base_label * 1.3)  # 20
    tick_size = int(base_tick * 1.3)    # 18

    # Plotting
    fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=False)
    font = {'size': label_size}
    plt.rc('font', **font)

    # Yearly
    axs[0].bar(yearly.index, yearly.values/1e6, color='steelblue')
    axs[0].set_title('Yearly Production', fontsize=title_size)
    axs[0].set_ylabel('Energy (GWh)', fontsize=label_size)
    axs[0].set_xlabel('Year', fontsize=label_size)
    axs[0].set_xticks(all_years)
    axs[0].set_xticklabels(all_years, rotation=45, fontsize=tick_size)
    axs[0].tick_params(axis='both', labelsize=tick_size)

    # Seasonal
    axs[1].plot(range(1, 13), monthly_avg.values/1e6, marker='o', color='darkorange')
    axs[1].set_title('Seasonal Profile (Monthly Average)', fontsize=title_size)
    axs[1].set_ylabel('Energy (GWh)', fontsize=label_size)
    axs[1].set_xlabel('Month', fontsize=label_size)
    axs[1].set_xticks(range(1, 13))
    axs[1].set_xticklabels(range(1, 13), fontsize=tick_size)
    axs[1].tick_params(axis='both', labelsize=tick_size)

    # Diurnal
    axs[2].plot(diurnal.index, diurnal.values, marker='o', color='forestgreen')
    axs[2].set_title('Diurnal Profile (Hourly Average)', fontsize=title_size)
    axs[2].set_ylabel('Power (W)', fontsize=label_size)
    axs[2].set_xlabel('Hour of Day', fontsize=label_size)
    axs[2].set_xticks(range(0, 24))
    axs[2].set_xticklabels(range(0, 24), fontsize=tick_size)
    axs[2].tick_params(axis='both', labelsize=tick_size)

    plt.tight_layout()
    #plt.show() 
    return yearly, monthly_avg, diurnal

def plot_turbine_production(sim_res, sim_res_wake, n_years=11):
    """
    Plot a stacked bar chart of yearly average production per turbine:
    - Lower bar: production with wake loss (MWh/yr)
    - Upper bar: difference (no wake - with wake) (MWh/yr)
    Args:
        sim_res: SimulationResult without wake loss (NoWakeDeficit)
        sim_res_wake: SimulationResult with wake loss (e.g., BastankhahGaussianDeficit)
        n_years: Number of years in the simulation (for averaging)
    """
    # Total energy per turbine (Wh)
    energy_no_wake = np.sum(sim_res.Power.values, axis=1) / n_years
    energy_with_wake = np.sum(sim_res_wake.Power.values, axis=1) / n_years
    # Convert to MWh
    energy_no_wake_MWh = energy_no_wake / 1e6
    energy_with_wake_MWh = energy_with_wake / 1e6
    # Difference (wake loss)
    wake_loss_MWh = energy_no_wake_MWh - energy_with_wake_MWh
    n_turbines = len(energy_no_wake_MWh)
    x = np.arange(n_turbines)
    plt.figure(figsize=(12, 6))
    plt.bar(x, energy_with_wake_MWh, label='With Wake Loss', color='tab:blue')
    plt.bar(x, wake_loss_MWh, bottom=energy_with_wake_MWh, label='Wake Loss', color='tab:orange')
    plt.xlabel('Turbine')
    plt.ylabel('Yearly Average Production (MWh/yr)')
    plt.title('Yearly Average Production per Turbine (Stacked: With Wake + Wake Loss)')
    plt.xticks(x, [f'Turbine {i+1}' for i in x], rotation=45)
    plt.legend()
    #plt.tight_layout()
    plt.show()
    

def plot_all_profiles(sim_res_df):
    """
    Plot seasonal and diurnal profiles for wind production, PV production, and electricity prices.
    Args:
        sim_res_df: DataFrame with 'Power', 'PV_CF', 'price', and 'datetime' columns
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    # Ensure datetime is a pandas datetime
    if not np.issubdtype(sim_res_df['datetime'].dtype, np.datetime64):
        sim_res_df['datetime'] = pd.to_datetime(sim_res_df['datetime'])

    # Add month and hour columns
    sim_res_df['month'] = sim_res_df['datetime'].dt.month
    sim_res_df['hour'] = sim_res_df['datetime'].dt.hour

    # Seasonal profiles (mean monthly values over all years)
    monthly_wind = sim_res_df.groupby('month')['Power'].mean() #so far so good
    monthly_pv = sim_res_df.groupby('month')['PV_CF'].mean()
    monthly_price = sim_res_df.groupby('month')['price'].mean()

    # Diurnal profiles (mean hourly values over all years)
    diurnal_wind = sim_res_df.groupby('hour')['Power'].mean()
    diurnal_pv = sim_res_df.groupby('hour')['PV_CF'].mean()
    diurnal_price = sim_res_df.groupby('hour')['price'].mean()

    # Font sizes
    base_title = 18
    base_label = 16
    base_tick = 14
    title_size = int(base_title * 1.3)
    label_size = int(base_label * 1.3)
    tick_size = int(base_tick * 1.3)

    # Plotting
    fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=False)
    font = {'size': label_size}
    plt.rc('font', **font)

    # Seasonal profiles
    ax1 = axs[0]
    # Plot power data on left axis
    ax1.plot(range(1, 13), monthly_wind.values/1e6, marker='o', color='steelblue', label='Wind Power')
    ax1.plot(range(1, 13), monthly_pv.values/1e6, marker='s', color='darkorange', label='PV Power')
    ax1.set_title('Seasonal Profiles (Monthly Average)', fontsize=title_size)
    ax1.set_ylabel('Power (MW)', fontsize=label_size)
    ax1.set_xlabel('Month', fontsize=label_size)
    ax1.set_xticks(range(1, 13))
    ax1.set_xticklabels(range(1, 13), fontsize=tick_size)
    ax1.tick_params(axis='both', labelsize=tick_size)
    ax1.legend(fontsize=label_size, loc='upper left')

    # Create second y-axis for prices
    #ax1_twin = ax1.twinx()
    #ax1_twin.plot(range(1, 13), monthly_price.values, marker='^', color='forestgreen', label='Electricity Price')
    #ax1_twin.set_ylabel('Price (USD/MWh)', fontsize=label_size, color='forestgreen')
    #ax1_twin.tick_params(axis='y', labelcolor='forestgreen', labelsize=tick_size)
    #ax1_twin.legend(fontsize=label_size, loc='upper right')

    # Diurnal profiles
    ax2 = axs[1]
    # Plot power data on left axis
    ax2.plot(diurnal_wind.index, diurnal_wind.values/1e6, marker='o', color='steelblue', label='Wind Power')
    ax2.plot(diurnal_pv.index, diurnal_pv.values/1e6, marker='s', color='darkorange', label='PV Power')
    ax2.set_title('Diurnal Profiles (Hourly Average)', fontsize=title_size)
    ax2.set_ylabel('Power (MW)', fontsize=label_size)
    ax2.set_xlabel('Hour of Day', fontsize=label_size)
    ax2.set_xticks(range(0, 24))
    ax2.set_xticklabels(range(0, 24), fontsize=tick_size)
    ax2.tick_params(axis='both', labelsize=tick_size)
    ax2.legend(fontsize=label_size, loc='upper left')

    # Create second y-axis for prices
    #ax2_twin = ax2.twinx()
    #ax2_twin.plot(diurnal_price.index, diurnal_price.values, marker='^', color='forestgreen', label='Electricity Price')
    #ax2_twin.set_ylabel('Price (USD/MWh)', fontsize=label_size, color='forestgreen')
    #ax2_twin.tick_params(axis='y', labelcolor='forestgreen', labelsize=tick_size)
    #ax2_twin.legend(fontsize=label_size, loc='upper right')

    plt.tight_layout()
    return monthly_wind, monthly_pv, monthly_price, diurnal_wind, diurnal_pv, diurnal_price
    
