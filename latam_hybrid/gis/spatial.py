"""
Spatial analysis utilities.

Common spatial operations for distance calculations, coordinate transformations,
and geometric relationships.
"""

from typing import Tuple, Union, Optional
import numpy as np


def calculate_distance_matrix(
    coords1: np.ndarray,
    coords2: Optional[np.ndarray] = None,
    method: str = 'euclidean'
) -> np.ndarray:
    """
    Calculate distance matrix between two sets of coordinates.

    Args:
        coords1: Nx2 array of (x, y) coordinates
        coords2: Mx2 array of (x, y) coordinates (uses coords1 if None)
        method: 'euclidean' or 'haversine'

    Returns:
        NxM distance matrix

    Example:
        >>> turbines = np.array([[0, 0], [800, 0], [1600, 0]])
        >>> panels = np.array([[400, 200], [1200, 200]])
        >>> distances = calculate_distance_matrix(turbines, panels)
    """
    if coords2 is None:
        coords2 = coords1

    if method == 'euclidean':
        return _euclidean_distance_matrix(coords1, coords2)
    elif method == 'haversine':
        return _haversine_distance_matrix(coords1, coords2)
    else:
        raise ValueError(f"Unknown method: {method}")


def _euclidean_distance_matrix(
    coords1: np.ndarray,
    coords2: np.ndarray
) -> np.ndarray:
    """Calculate Euclidean distance matrix."""
    n1 = len(coords1)
    n2 = len(coords2)

    distances = np.zeros((n1, n2))

    for i in range(n1):
        for j in range(n2):
            dx = coords1[i, 0] - coords2[j, 0]
            dy = coords1[i, 1] - coords2[j, 1]
            distances[i, j] = np.sqrt(dx**2 + dy**2)

    return distances


def _haversine_distance_matrix(
    coords1: np.ndarray,
    coords2: np.ndarray
) -> np.ndarray:
    """
    Calculate Haversine distance matrix (for lat/lon coordinates).

    Assumes coords are in (lon, lat) format.
    Returns distances in meters.
    """
    n1 = len(coords1)
    n2 = len(coords2)

    distances = np.zeros((n1, n2))

    for i in range(n1):
        for j in range(n2):
            distances[i, j] = haversine_distance(
                coords1[i, 0], coords1[i, 1],
                coords2[j, 0], coords2[j, 1]
            )

    return distances


def haversine_distance(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float
) -> float:
    """
    Calculate distance between two points on Earth (Haversine formula).

    Args:
        lon1: Longitude of point 1 (degrees)
        lat1: Latitude of point 1 (degrees)
        lon2: Longitude of point 2 (degrees)
        lat2: Latitude of point 2 (degrees)

    Returns:
        Distance in meters

    Example:
        >>> dist = haversine_distance(-70.0, -30.0, -70.1, -30.1)
    """
    # Earth radius in meters
    R = 6371000

    # Convert to radians
    lon1_rad = np.radians(lon1)
    lat1_rad = np.radians(lat1)
    lon2_rad = np.radians(lon2)
    lat2_rad = np.radians(lat2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

    distance = R * c

    return distance


def find_nearest_points(
    source_points: np.ndarray,
    target_points: np.ndarray,
    max_distance: Optional[float] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Find nearest target point for each source point.

    Args:
        source_points: Nx2 array of source coordinates
        target_points: Mx2 array of target coordinates
        max_distance: Maximum allowed distance (None = no limit)

    Returns:
        Tuple of (nearest_indices, nearest_distances)

    Example:
        >>> turbines = np.array([[0, 0], [800, 0]])
        >>> panels = np.array([[100, 100], [700, 100]])
        >>> indices, distances = find_nearest_points(turbines, panels)
    """
    dist_matrix = calculate_distance_matrix(source_points, target_points)

    nearest_indices = np.argmin(dist_matrix, axis=1)
    nearest_distances = np.min(dist_matrix, axis=1)

    if max_distance is not None:
        # Filter out points beyond max distance
        valid = nearest_distances <= max_distance
        nearest_indices[~valid] = -1
        nearest_distances[~valid] = np.inf

    return nearest_indices, nearest_distances


def calculate_bearing(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float
) -> float:
    """
    Calculate bearing (azimuth) from point 1 to point 2.

    Args:
        lon1: Longitude of point 1 (degrees)
        lat1: Latitude of point 1 (degrees)
        lon2: Longitude of point 2 (degrees)
        lat2: Latitude of point 2 (degrees)

    Returns:
        Bearing in degrees (0-360, where 0=North, 90=East)

    Example:
        >>> bearing = calculate_bearing(-70.0, -30.0, -70.1, -30.1)
    """
    # Convert to radians
    lon1_rad = np.radians(lon1)
    lat1_rad = np.radians(lat1)
    lon2_rad = np.radians(lon2)
    lat2_rad = np.radians(lat2)

    dlon = lon2_rad - lon1_rad

    x = np.sin(dlon) * np.cos(lat2_rad)
    y = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)

    bearing_rad = np.arctan2(x, y)
    bearing_deg = np.degrees(bearing_rad)

    # Normalize to 0-360
    return (bearing_deg + 360) % 360


def convert_crs(
    x: Union[float, np.ndarray],
    y: Union[float, np.ndarray],
    source_crs: str,
    target_crs: str
) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
    """
    Convert coordinates between coordinate reference systems.

    Args:
        x: X-coordinate(s) or longitude(s)
        y: Y-coordinate(s) or latitude(s)
        source_crs: Source CRS (e.g., "EPSG:4326")
        target_crs: Target CRS (e.g., "EPSG:32719")

    Returns:
        Tuple of (x_transformed, y_transformed)

    Raises:
        ImportError: If pyproj not available

    Example:
        >>> # Convert lat/lon to UTM
        >>> x_utm, y_utm = convert_crs(
        ...     -70.5, -30.2,
        ...     "EPSG:4326", "EPSG:32719"
        ... )
    """
    try:
        from pyproj import Transformer
    except ImportError:
        raise ImportError(
            "pyproj required for CRS transformations. "
            "Install with: conda install -c conda-forge pyproj"
        )

    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)

    x_transformed, y_transformed = transformer.transform(x, y)

    return x_transformed, y_transformed


def calculate_polygon_area(
    vertices: np.ndarray,
    crs: str = "EPSG:4326"
) -> float:
    """
    Calculate area of polygon defined by vertices.

    Args:
        vertices: Nx2 array of (x, y) coordinates (closed polygon)
        crs: Coordinate reference system

    Returns:
        Area in square meters

    Example:
        >>> vertices = np.array([[0, 0], [1000, 0], [1000, 1000], [0, 1000], [0, 0]])
        >>> area = calculate_polygon_area(vertices, crs="EPSG:32719")
    """
    try:
        from shapely.geometry import Polygon
        import geopandas as gpd
    except ImportError:
        raise ImportError("shapely and geopandas required")

    # Create polygon
    polygon = Polygon(vertices)

    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame({'geometry': [polygon]}, crs=crs)

    # Calculate area
    if gdf.crs.is_geographic:
        # Convert to equal-area projection for accurate area
        gdf = gdf.to_crs('EPSG:6933')

    return gdf.area.iloc[0]


def point_in_polygon(
    x: float,
    y: float,
    polygon_vertices: np.ndarray
) -> bool:
    """
    Check if point is inside polygon (ray casting algorithm).

    Args:
        x: Point x-coordinate
        y: Point y-coordinate
        polygon_vertices: Nx2 array of polygon vertices

    Returns:
        True if point is inside polygon

    Example:
        >>> vertices = np.array([[0, 0], [1000, 0], [1000, 1000], [0, 1000]])
        >>> is_inside = point_in_polygon(500, 500, vertices)
    """
    n = len(polygon_vertices)
    inside = False

    p1x, p1y = polygon_vertices[0]

    for i in range(1, n + 1):
        p2x, p2y = polygon_vertices[i % n]

        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x

                    if p1x == p2x or x <= xinters:
                        inside = not inside

        p1x, p1y = p2x, p2y

    return inside


def create_grid_points(
    bounds: Tuple[float, float, float, float],
    spacing_x: float,
    spacing_y: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0
) -> np.ndarray:
    """
    Create regular grid of points within bounding box.

    Args:
        bounds: (min_x, min_y, max_x, max_y)
        spacing_x: Horizontal spacing between points
        spacing_y: Vertical spacing between points
        offset_x: X offset for first point
        offset_y: Y offset for first point

    Returns:
        Nx2 array of grid point coordinates

    Example:
        >>> bounds = (0, 0, 1000, 1000)
        >>> grid = create_grid_points(bounds, spacing_x=100, spacing_y=100)
    """
    min_x, min_y, max_x, max_y = bounds

    # Calculate number of points
    nx = int((max_x - min_x - offset_x) / spacing_x) + 1
    ny = int((max_y - min_y - offset_y) / spacing_y) + 1

    # Create grid
    x = np.linspace(min_x + offset_x, min_x + offset_x + (nx-1) * spacing_x, nx)
    y = np.linspace(min_y + offset_y, min_y + offset_y + (ny-1) * spacing_y, ny)

    xv, yv = np.meshgrid(x, y)

    points = np.column_stack([xv.ravel(), yv.ravel()])

    return points


def calculate_setback_distance(
    points: np.ndarray,
    boundary_vertices: np.ndarray
) -> np.ndarray:
    """
    Calculate minimum distance from each point to boundary.

    Args:
        points: Nx2 array of point coordinates
        boundary_vertices: Mx2 array of boundary vertices

    Returns:
        Array of minimum distances (length N)

    Example:
        >>> turbines = np.array([[100, 100], [200, 200]])
        >>> boundary = np.array([[0, 0], [1000, 0], [1000, 1000], [0, 1000]])
        >>> setbacks = calculate_setback_distance(turbines, boundary)
    """
    n_points = len(points)
    n_vertices = len(boundary_vertices)

    min_distances = np.full(n_points, np.inf)

    # Calculate distance to each boundary edge
    for i in range(n_points):
        px, py = points[i]

        for j in range(n_vertices):
            v1 = boundary_vertices[j]
            v2 = boundary_vertices[(j + 1) % n_vertices]

            # Distance from point to line segment
            dist = _point_to_segment_distance(px, py, v1[0], v1[1], v2[0], v2[1])

            min_distances[i] = min(min_distances[i], dist)

    return min_distances


def _point_to_segment_distance(
    px: float, py: float,
    x1: float, y1: float,
    x2: float, y2: float
) -> float:
    """Calculate minimum distance from point to line segment."""
    # Vector from segment start to point
    dx = px - x1
    dy = py - y1

    # Vector of segment
    sx = x2 - x1
    sy = y2 - y1

    # Length squared of segment
    seg_len_sq = sx**2 + sy**2

    if seg_len_sq == 0:
        # Segment is a point
        return np.sqrt(dx**2 + dy**2)

    # Parameter of projection onto segment (0 to 1)
    t = max(0, min(1, (dx * sx + dy * sy) / seg_len_sq))

    # Closest point on segment
    closest_x = x1 + t * sx
    closest_y = y1 + t * sy

    # Distance to closest point
    dist = np.sqrt((px - closest_x)**2 + (py - closest_y)**2)

    return dist
