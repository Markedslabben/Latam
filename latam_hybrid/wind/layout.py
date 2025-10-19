"""
Wind turbine layout management.

Handles turbine positioning, spacing validation, and coordinate transformations.
"""

from pathlib import Path
from typing import Optional, Union, List, Tuple, Dict
import pandas as pd
import numpy as np

from ..core import LayoutData, DataValidator


class TurbineLayout:
    """
    Wind turbine layout manager.

    Handles turbine positions and validates spacing constraints.
    Supports lat/lon (EPSG:4326) and projected coordinates (UTM, etc.).
    """

    def __init__(self, layout_data: LayoutData):
        """
        Initialize turbine layout.

        Args:
            layout_data: LayoutData with coordinates and CRS info
        """
        self.data = layout_data

    @classmethod
    def from_csv(
        cls,
        filepath: Union[str, Path],
        x_column: str = 'x',
        y_column: str = 'y',
        id_column: Optional[str] = None,
        crs: str = "EPSG:4326",
        validate: bool = True
    ) -> 'TurbineLayout':
        """
        Load turbine layout from CSV file.

        Args:
            filepath: Path to CSV file
            x_column: X-coordinate or longitude column name
            y_column: Y-coordinate or latitude column name
            id_column: Turbine ID column (optional)
            crs: Coordinate Reference System
            validate: Whether to validate coordinates

        Returns:
            TurbineLayout instance

        Example:
            >>> layout = TurbineLayout.from_csv(
            ...     "turbine_layout_13.csv",
            ...     x_column="lon",
            ...     y_column="lat",
            ...     crs="EPSG:4326"
            ... )
        """
        from ..input import FileLoader

        # Load CSV
        df = FileLoader.load_csv(filepath)

        # Extract coordinates
        if x_column not in df.columns or y_column not in df.columns:
            raise ValueError(
                f"Columns '{x_column}' and '{y_column}' not found. "
                f"Available: {df.columns.tolist()}"
            )

        coordinates = df[[x_column, y_column]].values

        # Extract IDs if available
        turbine_ids = None
        if id_column and id_column in df.columns:
            turbine_ids = df[id_column].tolist()

        # Validate
        if validate:
            validation_result = DataValidator.validate_coordinates(
                coordinates,
                crs=crs,
                check_bounds=(crs == "EPSG:4326")
            )
            validation_result.raise_if_invalid()

        # Create LayoutData
        layout_data = LayoutData(
            coordinates=coordinates,
            turbine_ids=turbine_ids,
            crs=crs,
            metadata={'filepath': str(filepath)}
        )

        return cls(layout_data)

    @classmethod
    def from_coordinates(
        cls,
        coordinates: Union[np.ndarray, List[Tuple[float, float]]],
        turbine_ids: Optional[List[str]] = None,
        crs: str = "EPSG:4326"
    ) -> 'TurbineLayout':
        """
        Create layout from coordinate array.

        Args:
            coordinates: Nx2 array of (x, y) or (lon, lat) coordinates
            turbine_ids: Optional list of turbine IDs
            crs: Coordinate Reference System

        Returns:
            TurbineLayout instance

        Example:
            >>> coords = np.array([[0, 0], [800, 0], [1600, 0]])
            >>> layout = TurbineLayout.from_coordinates(
            ...     coords,
            ...     turbine_ids=['T1', 'T2', 'T3'],
            ...     crs="EPSG:32719"  # UTM Zone 19S
            ... )
        """
        # Convert to numpy array if needed
        if not isinstance(coordinates, np.ndarray):
            coordinates = np.array(coordinates)

        layout_data = LayoutData(
            coordinates=coordinates,
            turbine_ids=turbine_ids,
            crs=crs,
            metadata={'source': 'programmatic'}
        )

        return cls(layout_data)

    @classmethod
    def create_grid(
        cls,
        n_rows: int,
        n_cols: int,
        spacing_x: float = 800.0,
        spacing_y: float = 600.0,
        offset_x: float = 0.0,
        offset_y: float = 0.0,
        crs: str = "EPSG:32719"
    ) -> 'TurbineLayout':
        """
        Create regular grid layout.

        Args:
            n_rows: Number of rows
            n_cols: Number of columns per row
            spacing_x: Spacing between columns (meters or degrees)
            spacing_y: Spacing between rows (meters or degrees)
            offset_x: X offset for first turbine
            offset_y: Y offset for first turbine
            crs: Coordinate Reference System

        Returns:
            TurbineLayout instance

        Example:
            >>> # Create 3x4 grid with 800m x 600m spacing
            >>> layout = TurbineLayout.create_grid(
            ...     n_rows=3,
            ...     n_cols=4,
            ...     spacing_x=800,
            ...     spacing_y=600
            ... )
        """
        coordinates = []
        turbine_ids = []

        for row in range(n_rows):
            for col in range(n_cols):
                x = offset_x + col * spacing_x
                y = offset_y + row * spacing_y
                coordinates.append([x, y])
                turbine_ids.append(f"T{row+1}_{col+1}")

        return cls.from_coordinates(
            np.array(coordinates),
            turbine_ids=turbine_ids,
            crs=crs
        )

    def get_spacing_matrix(self) -> np.ndarray:
        """
        Calculate inter-turbine spacing matrix.

        Returns:
            NxN matrix of distances between all turbine pairs

        Example:
            >>> spacing = layout.get_spacing_matrix()
            >>> min_spacing = spacing[spacing > 0].min()
        """
        coords = self.data.coordinates
        n_turbines = len(coords)

        # Calculate Euclidean distances
        spacing_matrix = np.zeros((n_turbines, n_turbines))

        for i in range(n_turbines):
            for j in range(n_turbines):
                if i != j:
                    dist = np.sqrt(
                        (coords[i, 0] - coords[j, 0])**2 +
                        (coords[i, 1] - coords[j, 1])**2
                    )
                    spacing_matrix[i, j] = dist

        return spacing_matrix

    def validate_minimum_spacing(
        self,
        min_spacing: float,
        rotor_diameter: Optional[float] = None
    ) -> Dict:
        """
        Validate that turbines meet minimum spacing requirements.

        Args:
            min_spacing: Minimum allowed spacing (meters or rotor diameters)
            rotor_diameter: Rotor diameter in meters (if min_spacing is in rotor diameters)

        Returns:
            Dictionary with validation results

        Example:
            >>> # Validate 5D spacing with 164m rotor
            >>> result = layout.validate_minimum_spacing(5.0, rotor_diameter=164)
            >>> if not result['is_valid']:
            ...     print(f"Violations: {result['violations']}")
        """
        spacing_matrix = self.get_spacing_matrix()

        # Convert to meters if given in rotor diameters
        if rotor_diameter is not None:
            min_spacing_m = min_spacing * rotor_diameter
        else:
            min_spacing_m = min_spacing

        # Find violations
        violations = []
        for i in range(len(self.data.coordinates)):
            for j in range(i + 1, len(self.data.coordinates)):
                dist = spacing_matrix[i, j]
                if dist < min_spacing_m:
                    violations.append({
                        'turbine_1': i,
                        'turbine_2': j,
                        'distance_m': dist,
                        'violation_m': min_spacing_m - dist
                    })

        is_valid = len(violations) == 0

        result = {
            'is_valid': is_valid,
            'min_spacing_required_m': min_spacing_m,
            'min_spacing_actual_m': spacing_matrix[spacing_matrix > 0].min() if len(spacing_matrix) > 1 else None,
            'n_violations': len(violations),
            'violations': violations
        }

        return result

    def to_pywake_format(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert to pywake format (x, y arrays).

        Returns:
            Tuple of (x_coordinates, y_coordinates)

        Example:
            >>> x, y = layout.to_pywake_format()
            >>> # Use with pywake: wfm(x, y, ...)
        """
        return self.data.coordinates[:, 0], self.data.coordinates[:, 1]

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert layout to DataFrame for easy viewing/export.

        Returns:
            DataFrame with turbine positions

        Example:
            >>> df = layout.to_dataframe()
            >>> df.to_csv("layout_export.csv")
        """
        data = {
            'x': self.data.coordinates[:, 0],
            'y': self.data.coordinates[:, 1]
        }

        if self.data.turbine_ids:
            data['turbine_id'] = self.data.turbine_ids

        df = pd.DataFrame(data)
        return df

    @property
    def n_turbines(self) -> int:
        """Number of turbines in layout."""
        return self.data.n_turbines

    @property
    def coordinates(self) -> np.ndarray:
        """Turbine coordinates array."""
        return self.data.coordinates

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Layout bounding box: (min_x, min_y, max_x, max_y)."""
        coords = self.data.coordinates
        return (
            coords[:, 0].min(),
            coords[:, 1].min(),
            coords[:, 0].max(),
            coords[:, 1].max()
        )

    @property
    def center(self) -> Tuple[float, float]:
        """Layout center point: (center_x, center_y)."""
        coords = self.data.coordinates
        return (
            coords[:, 0].mean(),
            coords[:, 1].mean()
        )

    def __repr__(self) -> str:
        return (
            f"TurbineLayout(n_turbines={self.n_turbines}, "
            f"crs='{self.data.crs}', "
            f"bounds={self.bounds})"
        )


# Convenience function
def load_layout(
    source: Union[str, Path, np.ndarray],
    **kwargs
) -> TurbineLayout:
    """
    Load turbine layout from file or array.

    Args:
        source: File path or coordinate array
        **kwargs: Additional arguments for loading

    Returns:
        TurbineLayout instance

    Example:
        >>> # From file
        >>> layout = load_layout("turbine_coordinates.csv", x_column="lon", y_column="lat")
        >>>
        >>> # From array
        >>> coords = np.array([[0, 0], [800, 0]])
        >>> layout = load_layout(coords)
    """
    if isinstance(source, (str, Path)):
        return TurbineLayout.from_csv(source, **kwargs)
    elif isinstance(source, np.ndarray):
        return TurbineLayout.from_coordinates(source, **kwargs)
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")
