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

# --- Consistent Color Palette for All Plots ---
PALETTE = {
    'sky_blue':    '#4DADEC',  # Primary brand color
    'navy_blue':   '#0A3D62',  # Deep contrast
    'slate_grey':  '#707B7C',  # Neutral tone
    'moss_green':  '#68A357',  # Earth-aligned accent
    'sunset_orange': '#E67E22',# Complementary accent
    'violet':      '#8E44AD',  # Triadic pop
    'soft_red':    '#C0392B',  # Critical/warning
}

def plot_wind_rose_from_site(site, n_sectors=None):
    """
    Plot a wind rose from a PyWake Site object (e.g., XRSite or WeibullSite) using sector frequencies and color-coded by mean wind speed.
    Args:
        site: PyWake Site object with .ds['wd'], .ds['Sector_frequency'], .ds['Weibull_A'], .ds['Weibull_k']
        n_sectors: Optional, number of wind direction sectors to plot (default: use site sectors)
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

    # If n_sectors is specified and different from site, re-bin
    if n_sectors is not None and n_sectors != len(wd):
        # Re-bin frequencies and mean_ws to new sectors
        sector_edges = np.linspace(0, 360, n_sectors+1)
        sector_centers = (sector_edges[:-1] + sector_edges[1:]) / 2
        # Assign each original sector to new sector
        inds = np.digitize(wd, sector_edges, right=False) - 1
        inds[inds == n_sectors] = 0  # wrap 360 to 0
        freq_new = np.zeros(n_sectors)
        mean_ws_new = np.zeros(n_sectors)
        for i in range(n_sectors):
            mask = inds == i
            if np.any(mask):
                freq_new[i] = freq[mask].sum()
                mean_ws_new[i] = np.average(A[mask] * gamma(1 + 1 / k[mask]), weights=freq[mask])
            else:
                freq_new[i] = 0
                mean_ws_new[i] = 0
        freq = freq_new
        mean_ws = mean_ws_new
        wd = sector_centers
    else:
        n_sectors = len(wd)
        sector_edges = np.linspace(0, 360, n_sectors+1)
        mean_ws = A * gamma(1 + 1 / k)

    # Plot
    width = 2 * np.pi / n_sectors
    angles = np.deg2rad(sector_edges[:-1])
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    bars = ax.bar(
        angles, freq, width=width, bottom=0.0, align='edge',
        edgecolor='k', color=PALETTE['sky_blue']
    )
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_title('Wind Rose (Weibull Sectors, colored by mean wind speed)')
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=mean_ws.min(), vmax=mean_ws.max()))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.1, fraction=0.05, anchor=(1.0, 1.0))
    cbar.set_label('Mean wind speed (m/s)')
    ax.set_xticks(np.deg2rad(sector_edges[:-1]))
    ax.set_xticklabels([f'{int(e)}°' for e in sector_edges[:-1]])
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
    colors = PALETTE['sky_blue']

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
        plt.plot(ws, pdf, color=colors, label=label)
        # Annotate mean wind speed
        plt.axvline(mean_ws, color=colors, linestyle='--', alpha=0.5)
        plt.text(mean_ws, max(pdf)*0.8, f"{mean_ws:.2f}", color=colors, fontsize=8, rotation=90, va='bottom', ha='right')

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
    plt.hist(ws, bins=n_bins, color=PALETTE['sky_blue'], edgecolor='k', alpha=0.8, density=True)
    plt.xlabel('Wind speed (m/s)')
    plt.ylabel('Probability density')
    plt.title('Wind Speed Distribution (Histogram)')
    plt.tight_layout()
    plt.show()

def plot_production_profiles(sim_res_df):
    """
    Plot yearly, seasonal, and diurnal production profiles from a DataFrame with 'Power' and 'datetime_x' columns.
    Args:
        sim_res_df: DataFrame with at least 'Power' and 'datetime_x' columns (hourly data, multiple years)
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    # Ensure datetime is a pandas datetime
    if not np.issubdtype(sim_res_df['datetime_x'].dtype, np.datetime64):
        sim_res_df['datetime_x'] = pd.to_datetime(sim_res_df['datetime_x'])

    # Add year and month columns to avoid duplicate column names
    sim_res_df['year'] = sim_res_df['datetime_x'].dt.year
    sim_res_df['month'] = sim_res_df['datetime_x'].dt.month

    # Dynamically determine number of years
    n_years = sim_res_df['year'].nunique()

    # Yearly production (sum per year)
    all_years = np.sort(sim_res_df['year'].unique())
    yearly = sim_res_df.groupby('year')['Power'].sum().reindex(all_years, fill_value=0)

    # Seasonal profile (mean monthly sum over all years)
    monthly = sim_res_df.groupby(['year', 'month'])['Power'].sum().reset_index()
    monthly_avg = monthly.groupby('month')['Power'].mean()

    # Diurnal profile (mean hourly sum over all years)
    sim_res_df['hour'] = sim_res_df['datetime_x'].dt.hour
    diurnal = sim_res_df.groupby(['hour'])['Power'].mean()/(n_years*365*24) # converted to MW

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
    axs[0].bar(yearly.index, yearly.values/1e9, color=PALETTE['sky_blue']) #1e9 for GWh
    axs[0].set_title('Yearly Production', fontsize=title_size)
    axs[0].set_ylabel('Energy (GWh)', fontsize=label_size)
    axs[0].set_xlabel('Year', fontsize=label_size)
    axs[0].set_xticks(all_years)
    axs[0].set_xticklabels(all_years, rotation=45, fontsize=tick_size)
    axs[0].tick_params(axis='both', labelsize=tick_size)

    # Seasonal
    axs[1].plot(range(1, 13), monthly_avg.values/1e9, marker='o', color=PALETTE['sky_blue']) #1e9 for GWh
    axs[1].set_title('Seasonal Profile (Monthly Average)', fontsize=title_size)
    axs[1].set_ylabel('Energy (GWh/mo)', fontsize=label_size)
    axs[1].set_xlabel('Month', fontsize=label_size)
    axs[1].set_xticks(range(1, 13))
    axs[1].set_xticklabels(range(1, 13), fontsize=tick_size)
    axs[1].tick_params(axis='both', labelsize=tick_size)

    # Diurnal
    axs[2].plot(diurnal.index, diurnal.values, marker='o', color=PALETTE['sky_blue'])
    axs[2].set_title('Diurnal Profile (Hourly Average)', fontsize=title_size)
    axs[2].set_ylabel('Power (MW)', fontsize=label_size)
    axs[2].set_xlabel('Hour of Day', fontsize=label_size)
    axs[2].set_xticks(range(0, 24))
    axs[2].set_xticklabels(range(0, 24), fontsize=tick_size)
    axs[2].tick_params(axis='both', labelsize=tick_size)

    plt.tight_layout()
    #plt.show() 
    return yearly, monthly_avg, diurnal

def plot_turbine_production(sim_res, sim_res_wake, n_years=11, allowed_sectors=None):
    """
    Plot a stacked bar chart of yearly average production per turbine:
    - Lower bar: production including wake loss and sector management loss (allowed sectors, with wake)
    - Middle bar: production including wake loss (all sectors, with wake) minus lower bar
    - Top bar: production with no wake loss and no sector management (all sectors, no wake) minus middle bar
    Args:
        sim_res: SimulationResult without wake loss (NoWakeDeficit)
        sim_res_wake: SimulationResult with wake loss (BastankhahGaussianDeficit)
        n_years: Number of years in the simulation
        allowed_sectors: List of [s1,e1,...] sector boundaries in degrees (default: [60,120,240,300])
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    # Use color palette
    global PALETTE
    # Convert sim results to DataFrames
    if hasattr(sim_res_wake, "to_dataframe"):
        df_wake = sim_res_wake.to_dataframe().reset_index()
    else:
        df_wake = sim_res_wake.copy()
    if hasattr(sim_res, "to_dataframe"):
        df_no_wake = sim_res.to_dataframe().reset_index()
    else:
        df_no_wake = sim_res.copy()
    # Determine turbine and wind direction columns
    if 'turbine' in df_wake.columns:
        turb_col = 'turbine'
    elif 'wt' in df_wake.columns:
        turb_col = 'wt'
    else:
        raise KeyError("No turbine column found in DataFrame (expected 'turbine' or 'wt').")
    if 'WD' in df_wake.columns:
        wd_col = 'WD'
    elif 'wind_direction' in df_wake.columns:
        wd_col = 'wind_direction'
    else:
        raise KeyError("No wind direction column found in DataFrame (expected 'WD' or 'wind_direction').")
    # Default allowed sectors
    if allowed_sectors is None:
        allowed_sectors = [60,120,240,300]
    # Helper: mask for allowed sectors
    def sector_mask(wd):
        mask = np.zeros_like(wd, dtype=bool)
        for i in range(0, len(allowed_sectors), 2):
            s, e = allowed_sectors[i], allowed_sectors[i+1]
            if s < e:
                mask |= (wd >= s) & (wd < e)
            else:
                mask |= (wd >= s) | (wd < e)
        return mask
    # Masks for allowed sectors
    mask_wake = sector_mask(df_wake[wd_col].values)
    mask_no_wake = sector_mask(df_no_wake[wd_col].values)
    # --- Calculate production values ---
    # A: Production with both wake loss and sector management loss (allowed sectors, with wake)
    P_allowed_wake = df_wake[mask_wake].groupby(turb_col)['Power'].sum().reindex(range(df_wake[turb_col].nunique()), fill_value=0).values / n_years
    # B: Production with wake loss (all sectors, with wake)
    P_all_wake = df_wake.groupby(turb_col)['Power'].sum().reindex(range(df_wake[turb_col].nunique()), fill_value=0).values / n_years
    # C: Production with no wake loss and no sector management (all sectors, no wake)
    P_all_no_wake = df_no_wake.groupby(turb_col)['Power'].sum().reindex(range(df_no_wake[turb_col].nunique()), fill_value=0).values / n_years
    # --- Stack bars ---
    lower = P_allowed_wake / 1e6
    middle = (P_all_wake - P_allowed_wake) / 1e6
    top = (P_all_no_wake - P_all_wake) / 1e6
    # --- Plot ---
    ind = np.arange(len(lower))
    plt.figure(figsize=(12,6))
    p1 = plt.bar(ind, lower, color=PALETTE['sky_blue'], label='Production with all losses')
    p2 = plt.bar(ind, middle, bottom=lower, color=PALETTE['moss_green'], label='Sector mgmt loss')
    p3 = plt.bar(ind, top, bottom=lower+middle, color=PALETTE['sunset_orange'], label='Wake loss')
    plt.xlabel('Turbine')
    plt.ylabel('Yearly average production [MWh/yr]')
    plt.title('Yearly average production per turbine (stacked)')
    plt.xticks(ind, [str(i+1) for i in ind])
    plt.legend(handles=[p1, p2, p3], loc='center left', bbox_to_anchor=(1, 0.5))
    plt.grid(axis='y', color=PALETTE['slate_grey'], alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_all_profiles(sim_res_df):
    """
    Plot seasonal and diurnal profiles for wind production, PV production, and electricity prices.
    Args:
        sim_res_df: DataFrame with 'Power', 'PV_CF', 'price', and 'datetime_x' columns
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np

    # Ensure datetime is a pandas datetime
    if not np.issubdtype(sim_res_df['datetime_x'].dtype, np.datetime64):
        sim_res_df['datetime_x'] = pd.to_datetime(sim_res_df['datetime_x'])

    # Add month and hour columns
    sim_res_df['month'] = sim_res_df['datetime_x'].dt.month
    sim_res_df['hour'] = sim_res_df['datetime_x'].dt.hour

    # Dynamically determine number of years and turbines
    n_years = sim_res_df['datetime_x'].dt.year.nunique()
    if 'wt' in sim_res_df.columns:
        n_turbines = sim_res_df['wt'].nunique()
    elif 'turbine' in sim_res_df.columns:
        n_turbines = sim_res_df['turbine'].nunique()
    else:
        n_turbines = 1  # fallback if not present

    # Seasonal profiles (mean monthly values over all years)
    monthly_wind = sim_res_df.groupby('month')['Power'].sum()/1e9/n_years #monthly values (avg per year)
    monthly_pv = sim_res_df.groupby('month')['PV_CF'].sum()/n_turbines/n_years #GWh avg per turbine per year
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
    ax1.plot(range(1, 13), monthly_wind.values, marker='o', color=PALETTE['sky_blue'], label='Wind Power')
    ax1.plot(range(1, 13), monthly_pv.values, marker='s', color=PALETTE['moss_green'], label='PV Power')
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
    ax2.plot(diurnal_wind.index, diurnal_wind.values, marker='o', color=PALETTE['sky_blue'], label='Wind Power')
    ax2.plot(diurnal_pv.index, diurnal_pv.values, marker='s', color=PALETTE['moss_green'], label='PV Power')
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
    

def plot_energy_rose(sim_res, n_sectors=12):
    """
    Plot an energy rose from a sim_res dataset or DataFrame.
    Shows average power (MW) per wind direction sector as a polar bar chart.
    Args:
        sim_res: xarray Dataset or DataFrame with 'WD' (wind direction, deg) and 'Power' (W)
        n_sectors: Number of wind direction sectors (default: 12)
    """
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd

    # Convert to DataFrame if needed
    if hasattr(sim_res, "to_dataframe"):
        df = sim_res.to_dataframe().reset_index()
    else:
        df = sim_res.copy()

    # Use 'WD' or 'wind_direction' as wind direction column
    wd_col = 'WD' if 'WD' in df.columns else 'wind_direction'
    if wd_col not in df.columns or 'Power' not in df.columns:
        raise ValueError("sim_res must have 'WD' or 'wind_direction' and 'Power' columns")

    # Bin wind directions
    sector_edges = np.linspace(0, 360, n_sectors+1)
    sector_centers = (sector_edges[:-1] + sector_edges[1:]) / 2
    df['sector'] = pd.cut(df[wd_col], bins=sector_edges, labels=sector_centers, right=False, include_lowest=True)

    # Sum power across turbines if present
    if 'turbine' in df.columns:
        df = df.groupby(['time', 'sector'])['Power'].sum().reset_index()

    # Average power per sector (convert to MW)
    avg_power_MW = df.groupby('sector')['Power'].mean() / 1e6

    # Prepare for polar plot
    angles = np.deg2rad(avg_power_MW.index.astype(float))
    values = avg_power_MW.values
    width = 2 * np.pi / n_sectors

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    bars = ax.bar(
        angles, values, width=width, bottom=0.0, align='center',
        edgecolor='k', color=PALETTE['sky_blue'],
        label='Avg Power (MW)'
    )
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_title(f'Energy Rose (Average Power per Sector, MW, {n_sectors} sectors)')
    ax.set_xticks(np.deg2rad(sector_edges[:-1]))
    ax.set_xticklabels([f'{int(e)}°' for e in sector_edges[:-1]])
    plt.show()
    

def plot_wind_direction_vs_mean_power(sim_res_df, bin_width=1, allowed_intervals=None):
    """
    Plot a histogram of wind direction (x-axis) vs mean power (y-axis, MW) using fine wind direction bins.
    Optionally, highlight bins within allowed_intervals in green and others in light red.
    Args:
        sim_res_df: DataFrame with 'WD' or 'wind_direction' and 'Power' (in W)
        bin_width: Width of wind direction bins in degrees (default: 1)
        allowed_intervals: Optional, list of intervals [s1, e1, s2, e2, ...] (degrees) for allowed sectors
    """
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    import matplotlib.patches as mpatches

    # Use 'WD' or 'wind_direction' as wind direction column
    wd_col = 'WD' if 'WD' in sim_res_df.columns else 'wind_direction'
    if wd_col not in sim_res_df.columns or 'Power' not in sim_res_df.columns:
        raise ValueError("sim_res_df must have 'WD' or 'wind_direction' and 'Power' columns")

    # Bin wind directions
    bins = np.arange(0, 361, bin_width)
    sim_res_df['wd_bin'] = pd.cut(sim_res_df[wd_col], bins=bins, right=False, include_lowest=True)
    bin_centers = bins[:-1] + bin_width/2

    # Mean power per bin (convert to MW)
    mean_power = sim_res_df.groupby('wd_bin')['Power'].mean() / 1e6

    # Determine allowed bins
    allowed_mask = np.ones(len(bin_centers), dtype=bool)  # default: all allowed
    if allowed_intervals is not None:
        allowed_mask[:] = False
        for i in range(0, len(allowed_intervals), 2):
            s = allowed_intervals[i]
            e = allowed_intervals[i+1]
            if s < e:
                allowed_mask |= (bin_centers >= s) & (bin_centers < e)
            else:
                # Handle wrap-around (e.g., 350 to 20)
                allowed_mask |= (bin_centers >= s) | (bin_centers < e)

    # Set bar colors
    colors = np.where(allowed_mask, PALETTE['moss_green'], PALETTE['soft_red'])

    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(bin_centers, mean_power.values, width=bin_width, align='center', color=colors, alpha=0.8)
    plt.xlabel('Wind Direction (deg)')
    plt.ylabel('Mean Power (MW)')
    plt.title(f'Mean Power vs Wind Direction (bin width: {bin_width} deg)')
    plt.xlim(0, 360)
    if allowed_intervals is not None:
        green_patch = mpatches.Patch(color=PALETTE['moss_green'], label='Allowed sector')
        red_patch = mpatches.Patch(color=PALETTE['soft_red'], label='Not allowed sector')
        plt.legend(handles=[green_patch, red_patch], loc='upper right')
    plt.tight_layout()
    plt.show()
    

def production_loss_with_sector_management(sim_res_df, allowed_intervals):
    """
    Calculate the percentage production loss if only production from specified wind direction intervals is allowed.
    Args:
        sim_res_df: DataFrame with 'WD' or 'wind_direction' and 'Power' (in W)
        allowed_intervals: List of intervals [s1, e1, s2, e2, ...] (degrees), where each (si, ei) is an allowed range
    Returns:
        percent_loss: Percentage of production lost
        allowed_production: Total production in allowed sectors
        total_production: Total production (all directions)
    """
    wd_col = 'WD' if 'WD' in sim_res_df.columns else 'wind_direction'
    total_production = sim_res_df['Power'].sum()
    allowed_mask = np.zeros(len(sim_res_df), dtype=bool)
    for i in range(0, len(allowed_intervals), 2):
        s = allowed_intervals[i]
        e = allowed_intervals[i+1]
        if s < e:
            allowed_mask |= (sim_res_df[wd_col] >= s) & (sim_res_df[wd_col] < e)
        else:
            # Handle wrap-around (e.g., 350 to 20)
            allowed_mask |= (sim_res_df[wd_col] >= s) | (sim_res_df[wd_col] < e)
    # Dynamically determine number of years
    n_years = sim_res_df['datetime_x'].dt.year.nunique() if 'datetime_x' in sim_res_df.columns else 1
    allowed_production = sim_res_df.loc[allowed_mask, 'Power'].sum()/n_years/1e9
    percent_loss = 100 * (1 - allowed_production / total_production)
    print(f"Production loss with sector management: {percent_loss:.2f}%")
    return percent_loss
    

def plot_wake_maps(
    turbine_coords_file,
    turbine_file,
    site_file,
    wd_ws_list,
    n_sectors=12,
    planningarea_shp_path="Inputdata/GISdata/planningarea.shp"
):
    """
    Plot wake maps for a wind farm for different wind directions and wind speeds.
    Args:
        turbine_coords_file: Path to CSV file with turbine coordinates (columns: x_coord, y_coord)
        turbine_file: Path to turbine data file (e.g., Nordex N164 CSV)
        site_file: Path to wind site data file (e.g., Vortex time series)
        wd_ws_list: List of (wind direction, wind speed) tuples to plot, e.g. [(90, 8), (180, 10)]
        n_sectors: Number of wind direction sectors for Weibull distribution (default: 12)
        planningarea_shp_path: Optional path to planning area shapefile to overlay (boundary in red)
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    from turbine_galvian.create_turbine import create_nordex_n164_turbine
    from site_galvian.create_site import create_site_from_vortex, create_wind_distribution, create_weibull_site
    from py_wake.wind_farm_models import PropagateDownwind
    from py_wake.deficit_models import BastankhahGaussianDeficit
    if planningarea_shp_path is not None:
        import geopandas as gpd

    # Load turbine coordinates
    turbine_coords = pd.read_csv(turbine_coords_file)
    x = turbine_coords["x_coord"].values
    y = turbine_coords["y_coord"].values

    # Load turbine model
    turbine = create_nordex_n164_turbine(turbine_file)

    # Create wind distribution and WeibullSite
    time_site = create_site_from_vortex(site_file, start="2014-01-01 00:00", end="2024-12-31 23:59", include_leap_year=False)
    freq, A, k, wd_centers, TI, weibull_fits = create_wind_distribution(time_site, n_sectors=n_sectors)
    weibull_site = create_weibull_site(freq, A, k, wd_centers, TI)

    # Set up wind farm model
    wfm = PropagateDownwind(weibull_site, turbine, wake_deficitModel=BastankhahGaussianDeficit())

    # Plot wake maps for each (wd, ws)
    for wd, ws in wd_ws_list:
        sim_res = wfm(x, y, wd=wd, ws=ws)
        flow_map = sim_res.flow_map()
        fig, ax = plt.subplots()
        flow_map.plot_wake_map(ax=ax)
        if planningarea_shp_path is not None:
            planning_area = gpd.read_file(planningarea_shp_path)
            planning_area.boundary.plot(ax=ax, color='red', linewidth=2, label='Planning Area')
            ax.legend()
        # Overlay turbine numbers starting from 1
        label_offset = 80  # Adjust as needed for your plot scale
        for i, (xi, yi) in enumerate(zip(x, y)):
            ax.text(
                xi + label_offset, yi, str(i+1),
                color='black', fontsize=10, ha='left', va='center', fontweight='bold'
            )
        plt.title(f"Wake map: WD={wd}deg, WS={ws} m/s")
        plt.show()
    
