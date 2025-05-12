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