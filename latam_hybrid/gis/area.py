"""
Site planning area management.

Handles planning area boundaries, coordinate transformations, and spatial queries.
"""

from typing import Optional, Union, Tuple, List
from pathlib import Path
import numpy as np

from ..core import GISData


class SiteArea:
    """
    Planning area manager with spatial analysis.

    Manages site boundaries and provides spatial queries for turbine/panel placement.
    Requires geopandas for full functionality.

    Example:
        >>> area = SiteArea.from_shapefile("planning_area.shp")
        >>> is_inside = area.contains_point(-70.5, -30.2)
        >>> area_m2 = area.get_area()
    """

    def __init__(self, gis_data: GISData):
        """
        Initialize site area.

        Args:
            gis_data: GISData with planning area geometry
        """
        self.data = gis_data
        self._gdf = None

    @classmethod
    def from_shapefile(
        cls,
        filepath: Union[str, Path],
        crs: Optional[str] = None
    ) -> 'SiteArea':
        """
        Load planning area from shapefile.

        Args:
            filepath: Path to shapefile
            crs: Target CRS (optional, uses file CRS if None)

        Returns:
            SiteArea instance

        Example:
            >>> area = SiteArea.from_shapefile("planning_area.shp")
        """
        from ..input import GISReader

        gis_data = GISReader.read_shapefile(filepath, crs=crs)
        return cls(gis_data)

    @classmethod
    def from_geojson(
        cls,
        filepath: Union[str, Path],
        crs: Optional[str] = None
    ) -> 'SiteArea':
        """
        Load planning area from GeoJSON.

        Args:
            filepath: Path to GeoJSON file
            crs: Target CRS (optional, uses file CRS if None)

        Returns:
            SiteArea instance
        """
        from ..input import GISReader

        gis_data = GISReader.read_geojson(filepath, crs=crs)
        return cls(gis_data)

    @classmethod
    def from_bounds(
        cls,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        crs: str = "EPSG:4326"
    ) -> 'SiteArea':
        """
        Create rectangular planning area from bounds.

        Args:
            min_x: Minimum x-coordinate (west or left)
            min_y: Minimum y-coordinate (south or bottom)
            max_x: Maximum x-coordinate (east or right)
            max_y: Maximum y-coordinate (north or top)
            crs: Coordinate Reference System

        Returns:
            SiteArea instance

        Example:
            >>> area = SiteArea.from_bounds(
            ...     min_x=-71, min_y=-31,
            ...     max_x=-70, max_y=-30,
            ...     crs="EPSG:4326"
            ... )
        """
        try:
            import geopandas as gpd
            from shapely.geometry import box
        except ImportError:
            raise ImportError(
                "geopandas required for GIS operations. "
                "Install with: conda install -c conda-forge geopandas"
            )

        # Create rectangular polygon
        polygon = box(min_x, min_y, max_x, max_y)

        gdf = gpd.GeoDataFrame(
            {'name': ['Planning Area']},
            geometry=[polygon],
            crs=crs
        )

        gis_data = GISData(
            planning_area=gdf,
            crs=crs,
            metadata={'source': 'bounds', 'bounds': (min_x, min_y, max_x, max_y)}
        )

        return cls(gis_data)

    def to_geopandas(self):
        """
        Convert to geopandas GeoDataFrame.

        Returns:
            GeoDataFrame with planning area geometry

        Raises:
            ImportError: If geopandas not installed
        """
        if self._gdf is not None:
            return self._gdf

        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("geopandas required")

        self._gdf = self.data.planning_area
        return self._gdf

    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if point is within planning area.

        Args:
            x: X-coordinate or longitude
            y: Y-coordinate or latitude

        Returns:
            True if point is inside planning area

        Example:
            >>> is_inside = area.contains_point(-70.5, -30.2)
        """
        try:
            from shapely.geometry import Point
        except ImportError:
            raise ImportError("shapely required")

        gdf = self.to_geopandas()
        point = Point(x, y)

        # Check if point is in any polygon
        return gdf.contains(point).any()

    def contains_points(self, points: np.ndarray) -> np.ndarray:
        """
        Check which points are within planning area.

        Args:
            points: Nx2 array of (x, y) coordinates

        Returns:
            Boolean array of length N

        Example:
            >>> coords = np.array([[x1, y1], [x2, y2], [x3, y3]])
            >>> inside = area.contains_points(coords)
        """
        try:
            from shapely.geometry import Point
        except ImportError:
            raise ImportError("shapely required")

        gdf = self.to_geopandas()

        results = np.zeros(len(points), dtype=bool)

        for i, (x, y) in enumerate(points):
            point = Point(x, y)
            results[i] = gdf.contains(point).any()

        return results

    def get_area(self, unit: str = 'm2') -> float:
        """
        Calculate planning area size.

        Args:
            unit: Area unit ('m2', 'km2', 'ha')

        Returns:
            Area in specified unit

        Example:
            >>> area_m2 = area.get_area('m2')
            >>> area_ha = area.get_area('ha')
        """
        gdf = self.to_geopandas()

        # Get area in m² (assumes projected CRS or calculates geodesic area)
        if gdf.crs.is_geographic:
            # For geographic CRS, use geodesic area
            area_m2 = gdf.to_crs('EPSG:6933').area.sum()  # Equal Area projection
        else:
            area_m2 = gdf.area.sum()

        # Convert to requested unit
        conversions = {
            'm2': 1.0,
            'km2': 1e-6,
            'ha': 1e-4
        }

        if unit not in conversions:
            raise ValueError(f"Unknown unit: {unit}. Use: {list(conversions.keys())}")

        return area_m2 * conversions[unit]

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box of planning area.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y)

        Example:
            >>> min_x, min_y, max_x, max_y = area.get_bounds()
        """
        gdf = self.to_geopandas()
        bounds = gdf.total_bounds  # [min_x, min_y, max_x, max_y]

        return tuple(bounds)

    def get_centroid(self) -> Tuple[float, float]:
        """
        Get centroid of planning area.

        Returns:
            Tuple of (x, y) coordinates

        Example:
            >>> center_x, center_y = area.get_centroid()
        """
        gdf = self.to_geopandas()
        centroid = gdf.union_all().centroid

        return (centroid.x, centroid.y)

    def buffer(self, distance: float) -> 'SiteArea':
        """
        Create buffered (expanded/contracted) planning area.

        Args:
            distance: Buffer distance (positive=expand, negative=contract)
                     Units depend on CRS (meters for projected, degrees for geographic)

        Returns:
            New SiteArea with buffered geometry

        Example:
            >>> # Expand area by 100m (if projected CRS)
            >>> buffered = area.buffer(100)
        """
        gdf = self.to_geopandas().copy()
        gdf['geometry'] = gdf.buffer(distance)

        gis_data = GISData(
            planning_area=gdf,
            crs=self.data.crs,
            metadata={
                **self.data.metadata,
                'buffer_distance': distance
            }
        )

        return SiteArea(gis_data)

    def reproject(self, target_crs: str) -> 'SiteArea':
        """
        Reproject planning area to different CRS.

        Args:
            target_crs: Target coordinate reference system (e.g., "EPSG:32719")

        Returns:
            New SiteArea in target CRS

        Example:
            >>> # Convert lat/lon to UTM
            >>> area_utm = area.reproject("EPSG:32719")
        """
        gdf = self.to_geopandas()

        if gdf.crs.to_string() == target_crs:
            return self  # Already in target CRS

        gdf_reprojected = gdf.to_crs(target_crs)

        gis_data = GISData(
            planning_area=gdf_reprojected,
            crs=target_crs,
            metadata=self.data.metadata
        )

        return SiteArea(gis_data)

    def filter_points_inside(
        self,
        points: np.ndarray,
        point_ids: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, Optional[List[str]]]:
        """
        Filter points to only those inside planning area.

        Args:
            points: Nx2 array of (x, y) coordinates
            point_ids: Optional list of point IDs

        Returns:
            Tuple of (filtered_points, filtered_ids)

        Example:
            >>> all_coords = np.array([[x1, y1], [x2, y2], [x3, y3]])
            >>> valid_coords, valid_ids = area.filter_points_inside(
            ...     all_coords, ['T1', 'T2', 'T3']
            ... )
        """
        inside = self.contains_points(points)

        filtered_points = points[inside]

        filtered_ids = None
        if point_ids is not None:
            filtered_ids = [pid for pid, is_in in zip(point_ids, inside) if is_in]

        return filtered_points, filtered_ids

    @property
    def crs(self) -> str:
        """Coordinate Reference System."""
        return self.data.crs

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Bounding box: (min_x, min_y, max_x, max_y)."""
        return self.get_bounds()

    @property
    def centroid(self) -> Tuple[float, float]:
        """Centroid: (x, y)."""
        return self.get_centroid()

    @property
    def area_m2(self) -> float:
        """Area in square meters."""
        return self.get_area('m2')

    @property
    def area_km2(self) -> float:
        """Area in square kilometers."""
        return self.get_area('km2')

    @property
    def area_ha(self) -> float:
        """Area in hectares."""
        return self.get_area('ha')

    def __repr__(self) -> str:
        area_km2 = self.get_area('km2')
        return (
            f"SiteArea(crs='{self.crs}', "
            f"area={area_km2:.2f} km², "
            f"bounds={self.bounds})"
        )


# Convenience function
def load_planning_area(
    source: Union[str, Path],
    **kwargs
) -> SiteArea:
    """
    Load planning area from file.

    Args:
        source: Path to shapefile or GeoJSON
        **kwargs: Additional arguments for loading

    Returns:
        SiteArea instance

    Example:
        >>> area = load_planning_area("planning_area.shp")
        >>> area = load_planning_area("boundary.geojson")
    """
    source = Path(source)

    if source.suffix.lower() in ['.shp', '.shapefile']:
        return SiteArea.from_shapefile(source, **kwargs)
    elif source.suffix.lower() in ['.geojson', '.json']:
        return SiteArea.from_geojson(source, **kwargs)
    else:
        raise ValueError(
            f"Unknown file type: {source.suffix}. "
            f"Supported: .shp, .geojson"
        )
