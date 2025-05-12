import numpy as np
import matplotlib.pyplot as plt

def plot_wind_rose_from_site(site):
    """
    Plot a wind rose from a PyWake Site object (e.g., XRSite) using sector frequencies.
    Args:
        site: PyWake Site object with .ds['wd'] and .ds['Sector_frequency']
    """
    wd = site.ds['wd'].values
    freq = site.ds['Sector_frequency'].values

    # Remove duplicate 360° if present
    if wd[-1] == 360:
        wd = wd[:-1]
        freq = freq[:-1]

    # Get sector width from attributes or default to 30°
    width = np.deg2rad(site.ds.attrs.get('sector_width', 30.0))
    angles = np.deg2rad(wd)

    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    bars = ax.bar(angles, freq, width=width, bottom=0.0, align='center', edgecolor='k')
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_title('Wind Rose (Weibull Sectors)')
    plt.show() 