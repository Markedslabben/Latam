"""
GIS data readers for spatial analysis.

Supports shapefiles, GeoJSON, and other spatial data formats.
"""

from pathlib import Path
from typing import Optional, Union, List
import numpy as np

from ..core import GISData, DataValidator
from .loaders import FileLoader


class GISReader:
    """
    Reader for GIS spatial data.

    Requires geopandas for shapefile/GeoJSON reading.
    """

    @staticmethod
    def read_shapefile(
        filepath: Union[str, Path],
        crs: Optional[str] = None,
        validate: bool = True
    ) -> GISData:
        """
        Read shapefile for planning area or boundaries.

        Args:
            filepath: Path to shapefile (.shp) or directory
            crs: Target CRS (None to keep original)
            validate: Whether to validate data

        Returns:
            GISData object

        Raises:
            ImportError: If geopandas not available
            FileNotFoundError: If shapefile not found
            ValueError: If validation fails

        Example:
            >>> gis_data = GISReader.read_shapefile(
            ...     "Planningarea_shp/planning_area.shp",
            ...     crs="EPSG:4326"
            ... )
        """
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError(
                "geopandas is required for GIS data reading. "
                "Install with: conda install -c conda-forge geopandas"
            )

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Shapefile not found: {filepath}")

        # Read shapefile
        try:
            gdf = gpd.read_file(filepath)
        except Exception as e:
            raise ValueError(f"Failed to read shapefile {filepath}: {e}")

        if gdf.empty:
            raise ValueError(f"Shapefile is empty: {filepath}")

        # Reproject if requested
        original_crs = gdf.crs.to_string() if gdf.crs else "Unknown"
        if crs and gdf.crs and gdf.crs.to_string() != crs:
            gdf = gdf.to_crs(crs)

        # Validate
        if validate:
            # Check for valid geometries
            invalid = ~gdf.geometry.is_valid
            if invalid.any():
                n_invalid = invalid.sum()
                print(f"Warning: {n_invalid} invalid geometries found")
                # Try to fix
                gdf.loc[invalid, 'geometry'] = gdf.loc[invalid, 'geometry'].buffer(0)

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'original_crs': original_crs,
            'target_crs': gdf.crs.to_string() if gdf.crs else "Unknown",
            'n_features': len(gdf),
            'geometry_types': gdf.geometry.type.unique().tolist(),
            'bounds': gdf.total_bounds.tolist(),  # [minx, miny, maxx, maxy]
            'columns': gdf.columns.tolist()
        }

        # Extract elevation if present
        elevation = None
        if 'elevation' in gdf.columns or 'z' in gdf.columns:
            elev_col = 'elevation' if 'elevation' in gdf.columns else 'z'
            elevation = gdf[elev_col].values

        return GISData(
            planning_area=gdf,
            elevation=elevation,
            crs=gdf.crs.to_string() if gdf.crs else "Unknown",
            metadata=metadata
        )

    @staticmethod
    def read_geojson(
        filepath: Union[str, Path],
        crs: Optional[str] = None,
        validate: bool = True
    ) -> GISData:
        """
        Read GeoJSON file.

        Args:
            filepath: Path to GeoJSON file
            crs: Target CRS (None to keep original)
            validate: Whether to validate data

        Returns:
            GISData object

        Example:
            >>> gis_data = GISReader.read_geojson(
            ...     "planning_area.geojson",
            ...     crs="EPSG:4326"
            ... )
        """
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError(
                "geopandas is required for GIS data reading. "
                "Install with: conda install -c conda-forge geopandas"
            )

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"GeoJSON file not found: {filepath}")

        # Read GeoJSON
        try:
            gdf = gpd.read_file(filepath)
        except Exception as e:
            raise ValueError(f"Failed to read GeoJSON {filepath}: {e}")

        if gdf.empty:
            raise ValueError(f"GeoJSON is empty: {filepath}")

        # Reproject if requested
        original_crs = gdf.crs.to_string() if gdf.crs else "Unknown"
        if crs and gdf.crs and gdf.crs.to_string() != crs:
            gdf = gdf.to_crs(crs)

        # Validate
        if validate:
            invalid = ~gdf.geometry.is_valid
            if invalid.any():
                n_invalid = invalid.sum()
                print(f"Warning: {n_invalid} invalid geometries found")
                gdf.loc[invalid, 'geometry'] = gdf.loc[invalid, 'geometry'].buffer(0)

        # Metadata
        metadata = {
            'filepath': str(filepath),
            'original_crs': original_crs,
            'target_crs': gdf.crs.to_string() if gdf.crs else "Unknown",
            'n_features': len(gdf),
            'geometry_types': gdf.geometry.type.unique().tolist(),
            'bounds': gdf.total_bounds.tolist(),
            'columns': gdf.columns.tolist()
        }

        return GISData(
            planning_area=gdf,
            elevation=None,
            crs=gdf.crs.to_string() if gdf.crs else "Unknown",
            metadata=metadata
        )

    @staticmethod
    def create_bounding_box(
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        crs: str = "EPSG:4326"
    ) -> GISData:
        """
        Create rectangular planning area from bounding box coordinates.

        Useful for quickly defining a study area.

        Args:
            min_lon: Minimum longitude (west)
            min_lat: Minimum latitude (south)
            max_lon: Maximum longitude (east)
            max_lat: Maximum latitude (north)
            crs: Coordinate reference system

        Returns:
            GISData object with rectangular planning area

        Example:
            >>> gis_data = GISReader.create_bounding_box(
            ...     min_lon=-70.7, min_lat=-18.6,
            ...     max_lon=-70.5, max_lat=-18.4
            ... )
        """
        try:
            import geopandas as gpd
            from shapely.geometry import box
        except ImportError:
            raise ImportError(
                "geopandas and shapely required. "
                "Install with: conda install -c conda-forge geopandas"
            )

        # Create bounding box polygon
        polygon = box(min_lon, min_lat, max_lon, max_lat)

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(
            {'name': ['Bounding Box Area']},
            geometry=[polygon],
            crs=crs
        )

        # Calculate area
        # For lat/lon, convert to projected CRS for area calculation
        if 'EPSG:4326' in crs:
            # Use UTM zone (approximate for Chile/Peru region: Zone 19S)
            gdf_projected = gdf.to_crs("EPSG:32719")
            area_m2 = gdf_projected.geometry.area.values[0]
        else:
            area_m2 = gdf.geometry.area.values[0]

        # Metadata
        metadata = {
            'source': 'Generated bounding box',
            'crs': crs,
            'n_features': 1,
            'geometry_types': ['Polygon'],
            'bounds': [min_lon, min_lat, max_lon, max_lat],
            'area_m2': float(area_m2),
            'area_km2': float(area_m2 / 1e6)
        }

        return GISData(
            planning_area=gdf,
            elevation=None,
            crs=crs,
            metadata=metadata
        )


# Convenience function
def read_gis_data(
    filepath: Union[str, Path],
    source_type: str = 'auto',
    **kwargs
) -> GISData:
    """
    Auto-detect format and read GIS data.

    Args:
        filepath: Path to GIS data file
        source_type: Source type ('shapefile', 'geojson', or 'auto')
        **kwargs: Additional arguments passed to specific reader

    Returns:
        GISData object

    Example:
        >>> gis_data = read_gis_data("planning_area.shp")
        >>> gis_data = read_gis_data("area.geojson", crs="EPSG:4326")
    """
    filepath = Path(filepath)

    # Auto-detect format
    if source_type == 'auto':
        suffix = filepath.suffix.lower()
        if suffix == '.shp':
            source_type = 'shapefile'
        elif suffix in ['.geojson', '.json']:
            source_type = 'geojson'
        else:
            # Try shapefile by default
            source_type = 'shapefile'

    # Read based on detected type
    if source_type == 'shapefile':
        return GISReader.read_shapefile(filepath, **kwargs)
    elif source_type == 'geojson':
        return GISReader.read_geojson(filepath, **kwargs)
    else:
        raise ValueError(f"Unknown source_type: {source_type}")
