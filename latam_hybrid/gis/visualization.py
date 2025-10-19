"""
GIS visualization utilities.

Plotting and visualization helpers for maps, layouts, and planning areas.
Requires matplotlib and contextily for full functionality.
"""

from typing import Optional, List, Tuple, Union
from pathlib import Path
import numpy as np


def plot_site_map(
    planning_area,
    turbine_positions: Optional[np.ndarray] = None,
    solar_positions: Optional[np.ndarray] = None,
    figsize: Tuple[int, int] = (12, 10),
    add_basemap: bool = True,
    save_path: Optional[Union[str, Path]] = None
):
    """
    Plot site map with planning area and turbine/solar positions.

    Args:
        planning_area: SiteArea instance
        turbine_positions: Nx2 array of turbine (x, y) positions
        solar_positions: Mx2 array of solar panel (x, y) positions
        figsize: Figure size
        add_basemap: Whether to add background map (requires contextily)
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure and axes

    Example:
        >>> area = SiteArea.from_shapefile("planning_area.shp")
        >>> turbines = np.array([[x1, y1], [x2, y2]])
        >>> fig, ax = plot_site_map(area, turbine_positions=turbines)
    """
    try:
        import matplotlib.pyplot as plt
        import geopandas as gpd
    except ImportError:
        raise ImportError(
            "matplotlib and geopandas required for visualization. "
            "Install with: conda install -c conda-forge matplotlib geopandas"
        )

    fig, ax = plt.subplots(figsize=figsize)

    # Plot planning area
    gdf = planning_area.to_geopandas()
    gdf.plot(ax=ax, facecolor='lightgray', edgecolor='black', alpha=0.3)

    # Plot turbine positions
    if turbine_positions is not None:
        turbine_gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(
                turbine_positions[:, 0],
                turbine_positions[:, 1]
            ),
            crs=planning_area.crs
        )
        turbine_gdf.plot(
            ax=ax,
            marker='o',
            color='red',
            markersize=100,
            label='Wind Turbines'
        )

    # Plot solar positions
    if solar_positions is not None:
        solar_gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(
                solar_positions[:, 0],
                solar_positions[:, 1]
            ),
            crs=planning_area.crs
        )
        solar_gdf.plot(
            ax=ax,
            marker='s',
            color='blue',
            markersize=50,
            label='Solar Panels'
        )

    # Add basemap if requested
    if add_basemap:
        try:
            import contextily as ctx
            # Only add basemap if CRS is projected
            if not gdf.crs.is_geographic:
                ctx.add_basemap(ax, crs=gdf.crs.to_string(), alpha=0.5)
        except ImportError:
            pass  # Silently skip if contextily not available

    ax.set_xlabel('X (m)' if not gdf.crs.is_geographic else 'Longitude')
    ax.set_ylabel('Y (m)' if not gdf.crs.is_geographic else 'Latitude')
    ax.set_title('Site Layout')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, ax


def plot_turbine_layout(
    positions: np.ndarray,
    turbine_ids: Optional[List[str]] = None,
    rotor_diameter: Optional[float] = None,
    figsize: Tuple[int, int] = (10, 8),
    save_path: Optional[Union[str, Path]] = None
):
    """
    Plot turbine layout with optional rotor circles.

    Args:
        positions: Nx2 array of turbine (x, y) positions
        turbine_ids: Optional list of turbine IDs for labels
        rotor_diameter: Optional rotor diameter for scale circles
        figsize: Figure size
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure and axes

    Example:
        >>> positions = np.array([[0, 0], [800, 0], [1600, 0]])
        >>> fig, ax = plot_turbine_layout(
        ...     positions,
        ...     turbine_ids=['T1', 'T2', 'T3'],
        ...     rotor_diameter=164
        ... )
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle
    except ImportError:
        raise ImportError("matplotlib required")

    fig, ax = plt.subplots(figsize=figsize)

    # Plot turbine positions
    ax.scatter(
        positions[:, 0],
        positions[:, 1],
        c='red',
        s=100,
        marker='o',
        label='Turbines',
        zorder=3
    )

    # Add rotor circles if diameter provided
    if rotor_diameter is not None:
        radius = rotor_diameter / 2
        for x, y in positions:
            circle = Circle(
                (x, y),
                radius,
                fill=False,
                edgecolor='red',
                linestyle='--',
                alpha=0.3
            )
            ax.add_patch(circle)

    # Add labels if provided
    if turbine_ids is not None:
        for i, (x, y) in enumerate(positions):
            ax.annotate(
                turbine_ids[i],
                (x, y),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8
            )

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('Turbine Layout')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, ax


def plot_distance_heatmap(
    distance_matrix: np.ndarray,
    source_ids: Optional[List[str]] = None,
    target_ids: Optional[List[str]] = None,
    figsize: Tuple[int, int] = (10, 8),
    save_path: Optional[Union[str, Path]] = None
):
    """
    Plot distance matrix as heatmap.

    Args:
        distance_matrix: NxM distance matrix
        source_ids: Optional list of source point IDs
        target_ids: Optional list of target point IDs
        figsize: Figure size
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure and axes

    Example:
        >>> from latam_hybrid.gis import calculate_distance_matrix
        >>> turbines = np.array([[0, 0], [800, 0], [1600, 0]])
        >>> distances = calculate_distance_matrix(turbines, turbines)
        >>> fig, ax = plot_distance_heatmap(distances)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required")

    fig, ax = plt.subplots(figsize=figsize)

    im = ax.imshow(distance_matrix, cmap='viridis', aspect='auto')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Distance (m)', rotation=270, labelpad=20)

    # Set tick labels if IDs provided
    if source_ids is not None:
        ax.set_yticks(range(len(source_ids)))
        ax.set_yticklabels(source_ids)

    if target_ids is not None:
        ax.set_xticks(range(len(target_ids)))
        ax.set_xticklabels(target_ids, rotation=45, ha='right')

    ax.set_xlabel('Target Points')
    ax.set_ylabel('Source Points')
    ax.set_title('Distance Matrix')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, ax


def plot_wind_rose(
    wind_directions: np.ndarray,
    wind_speeds: np.ndarray,
    bins: int = 16,
    figsize: Tuple[int, int] = (10, 10),
    save_path: Optional[Union[str, Path]] = None
):
    """
    Plot wind rose diagram.

    Args:
        wind_directions: Array of wind directions (degrees, 0=North)
        wind_speeds: Array of wind speeds (m/s)
        bins: Number of direction bins (default 16 = 22.5° sectors)
        figsize: Figure size
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure and axes

    Example:
        >>> directions = np.random.uniform(0, 360, 1000)
        >>> speeds = np.random.weibull(2, 1000) * 8
        >>> fig, ax = plot_wind_rose(directions, speeds)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required")

    # Create polar plot
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='polar')

    # Calculate direction bins
    dir_bins = np.linspace(0, 360, bins + 1)
    dir_centers = (dir_bins[:-1] + dir_bins[1:]) / 2

    # Convert to radians (0° = North = π/2 in math, adjust)
    theta = np.radians(90 - dir_centers)

    # Calculate frequency in each direction bin
    frequencies = np.zeros(bins)
    for i in range(bins):
        mask = (wind_directions >= dir_bins[i]) & (wind_directions < dir_bins[i + 1])
        frequencies[i] = mask.sum()

    # Normalize to percentages
    frequencies = frequencies / len(wind_directions) * 100

    # Plot bars
    width = 2 * np.pi / bins
    bars = ax.bar(theta, frequencies, width=width, bottom=0.0, alpha=0.7)

    # Color bars by average speed in that direction
    for i, bar in enumerate(bars):
        mask = (wind_directions >= dir_bins[i]) & (wind_directions < dir_bins[i + 1])
        avg_speed = wind_speeds[mask].mean() if mask.any() else 0
        bar.set_facecolor(plt.cm.viridis(avg_speed / wind_speeds.max()))

    # Set 0° to North
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)

    # Add labels
    ax.set_title('Wind Rose', pad=20)
    ax.set_ylabel('Frequency (%)', labelpad=30)

    # Add grid
    ax.grid(True)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, ax


def plot_power_curve(
    wind_speeds: np.ndarray,
    power_output: np.ndarray,
    turbine_name: str = 'Wind Turbine',
    rated_power: Optional[float] = None,
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[Union[str, Path]] = None
):
    """
    Plot wind turbine power curve.

    Args:
        wind_speeds: Array of wind speeds (m/s)
        power_output: Array of power outputs (kW)
        turbine_name: Name of turbine for plot title
        rated_power: Optional rated power for reference line
        figsize: Figure size
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure and axes

    Example:
        >>> turbine = TurbineModel.from_csv("nordex_n164.csv")
        >>> ws = turbine.spec.power_curve['ws'].values
        >>> power = turbine.spec.power_curve['power'].values
        >>> fig, ax = plot_power_curve(ws, power, turbine.spec.name)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required")

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(wind_speeds, power_output, 'b-', linewidth=2, label='Power Curve')

    # Add rated power line if provided
    if rated_power is not None:
        ax.axhline(
            rated_power,
            color='r',
            linestyle='--',
            alpha=0.7,
            label=f'Rated Power ({rated_power} kW)'
        )

    ax.set_xlabel('Wind Speed (m/s)')
    ax.set_ylabel('Power Output (kW)')
    ax.set_title(f'Power Curve: {turbine_name}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, ax


def plot_production_timeseries(
    timestamps: np.ndarray,
    power_timeseries: np.ndarray,
    energy_type: str = 'Wind',
    figsize: Tuple[int, int] = (14, 6),
    save_path: Optional[Union[str, Path]] = None
):
    """
    Plot power production timeseries.

    Args:
        timestamps: Array of timestamps
        power_timeseries: Array of power values (kW)
        energy_type: 'Wind', 'Solar', or 'Hybrid'
        figsize: Figure size
        save_path: Optional path to save figure

    Returns:
        Matplotlib figure and axes

    Example:
        >>> result = wind_site.calculate_production()
        >>> ts = result.power_timeseries.index
        >>> power = result.power_timeseries['power_kw'].values
        >>> fig, ax = plot_production_timeseries(ts, power, 'Wind')
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required")

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(timestamps, power_timeseries, linewidth=0.5, alpha=0.7)

    ax.set_xlabel('Time')
    ax.set_ylabel('Power (kW)')
    ax.set_title(f'{energy_type} Power Production Timeseries')
    ax.grid(True, alpha=0.3)

    # Rotate x-axis labels
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig, ax


# Convenience function
def quick_site_plot(
    planning_area,
    turbine_layout=None,
    solar_positions=None,
    save_path: Optional[Union[str, Path]] = None
):
    """
    Quick one-liner for site visualization.

    Args:
        planning_area: SiteArea instance
        turbine_layout: TurbineLayout instance or positions array
        solar_positions: Solar panel positions array
        save_path: Optional save path

    Returns:
        Matplotlib figure and axes

    Example:
        >>> area = SiteArea.from_shapefile("planning_area.shp")
        >>> layout = TurbineLayout.from_csv("turbines.csv")
        >>> fig, ax = quick_site_plot(area, layout)
    """
    # Extract positions from layout if TurbineLayout instance
    turbine_positions = None
    if turbine_layout is not None:
        if hasattr(turbine_layout, 'positions'):
            turbine_positions = turbine_layout.positions
        else:
            turbine_positions = turbine_layout

    return plot_site_map(
        planning_area,
        turbine_positions=turbine_positions,
        solar_positions=solar_positions,
        save_path=save_path
    )
