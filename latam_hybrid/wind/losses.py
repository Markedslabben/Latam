"""
Wind farm losses model following WindPRO methodology.

Implements multiplicative loss calculation: Loss = (1-l1)*(1-l2)...(1-ln)
where l_n are individual loss categories as fractions (e.g., 0.03 for 3%).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class LossType(str, Enum):
    """Loss category types."""
    WAKE = "wake_losses"
    CURTAILMENT_SECTOR = "curtailment_sector_management"
    AVAILABILITY_TURBINES = "availability_turbines"
    AVAILABILITY_GRID = "availability_grid"
    ELECTRICAL = "electrical_losses"
    HIGH_HYSTERESIS = "high_hysteresis_losses"
    ENVIRONMENTAL_DEGRADATION = "environmental_performance_degradation"
    OTHER = "other_losses"


@dataclass
class LossCategory:
    """
    Individual loss category.

    Attributes:
        name: Loss category name
        value: Loss value as fraction (0-1), e.g., 0.03 for 3%
        is_computed: True if computed from simulations, False if user-specified
        description: Optional description of the loss category
    """
    name: str
    value: float
    is_computed: bool = False
    description: str = ""

    def __post_init__(self):
        """Validate loss category."""
        if not 0 <= self.value <= 1:
            raise ValueError(
                f"Loss value must be between 0 and 1 (fraction), got {self.value}"
            )

    @property
    def percentage(self) -> float:
        """Return loss as percentage (0-100)."""
        return self.value * 100

    def to_dict(self) -> Dict:
        """Export to dictionary."""
        return {
            'name': self.name,
            'value': self.value,
            'percentage': self.percentage,
            'is_computed': self.is_computed,
            'description': self.description
        }


class WindFarmLosses:
    """
    Wind farm losses manager with multiplicative loss calculation.

    Follows WindPRO methodology where total loss factor is:
    Loss_factor = (1-l1) * (1-l2) * ... * (1-ln)

    Net AEP = Gross AEP * Loss_factor

    Loss Categories:
        - Wake losses (computed from pywake)
        - Curtailment from sector management (computed from sector module)
        - Availability turbines (default 1.5%)
        - Availability grid (default 1.5%)
        - Electrical losses (default 2.0%)
        - High hysteresis losses (default 0.3%)
        - Environmental performance degradation (default 3.0%)
        - Other losses (default 0.5%)
    """

    # WindPRO default loss values (as fractions)
    DEFAULTS = {
        LossType.AVAILABILITY_TURBINES: 0.015,      # 1.5%
        LossType.AVAILABILITY_GRID: 0.015,          # 1.5%
        LossType.ELECTRICAL: 0.020,                 # 2.0%
        LossType.HIGH_HYSTERESIS: 0.003,            # 0.3%
        LossType.ENVIRONMENTAL_DEGRADATION: 0.030,  # 3.0%
        LossType.OTHER: 0.005,                      # 0.5%
    }

    def __init__(self):
        """Initialize empty losses manager."""
        self._losses: Dict[str, LossCategory] = {}

    def add_loss(
        self,
        name: str,
        value: float,
        is_computed: bool = False,
        description: str = ""
    ) -> 'WindFarmLosses':
        """
        Add or update a loss category.

        Args:
            name: Loss category name (use LossType enum for standard categories)
            value: Loss value as fraction (0-1)
            is_computed: True if computed from simulations
            description: Optional description

        Returns:
            Self for method chaining

        Example:
            >>> losses = WindFarmLosses()
            >>> losses.add_loss('wake_losses', 0.08, is_computed=True)
            >>> losses.add_loss('availability_turbines', 0.015)
        """
        self._losses[name] = LossCategory(
            name=name,
            value=value,
            is_computed=is_computed,
            description=description
        )
        return self

    def add_default_losses(
        self,
        availability_turbines: Optional[float] = None,
        availability_grid: Optional[float] = None,
        electrical_losses: Optional[float] = None,
        high_hysteresis: Optional[float] = None,
        environmental_degradation: Optional[float] = None,
        other_losses: Optional[float] = None
    ) -> 'WindFarmLosses':
        """
        Add standard loss categories with WindPRO defaults or custom values.

        Args:
            availability_turbines: Turbine availability loss (default 1.5%)
            availability_grid: Grid availability loss (default 1.5%)
            electrical_losses: Electrical system losses (default 2.0%)
            high_hysteresis: Power curve hysteresis losses (default 0.3%)
            environmental_degradation: Environmental performance degradation (default 3.0%)
            other_losses: Other miscellaneous losses (default 0.5%)

        Returns:
            Self for method chaining

        Example:
            >>> losses = WindFarmLosses()
            >>> losses.add_default_losses(
            ...     availability_turbines=0.02,  # Custom 2%
            ...     electrical_losses=0.025      # Custom 2.5%
            ... )
        """
        # Use provided values or defaults
        values = {
            LossType.AVAILABILITY_TURBINES: availability_turbines or self.DEFAULTS[LossType.AVAILABILITY_TURBINES],
            LossType.AVAILABILITY_GRID: availability_grid or self.DEFAULTS[LossType.AVAILABILITY_GRID],
            LossType.ELECTRICAL: electrical_losses or self.DEFAULTS[LossType.ELECTRICAL],
            LossType.HIGH_HYSTERESIS: high_hysteresis or self.DEFAULTS[LossType.HIGH_HYSTERESIS],
            LossType.ENVIRONMENTAL_DEGRADATION: environmental_degradation or self.DEFAULTS[LossType.ENVIRONMENTAL_DEGRADATION],
            LossType.OTHER: other_losses or self.DEFAULTS[LossType.OTHER]
        }

        descriptions = {
            LossType.AVAILABILITY_TURBINES: "Turbine downtime for maintenance and repairs",
            LossType.AVAILABILITY_GRID: "Grid outages and maintenance",
            LossType.ELECTRICAL: "Cable losses and transformer losses",
            LossType.HIGH_HYSTERESIS: "Power curve hysteresis effects",
            LossType.ENVIRONMENTAL_DEGRADATION: "Performance decline over project lifetime",
            LossType.OTHER: "Miscellaneous unaccounted losses"
        }

        for loss_type, value in values.items():
            self.add_loss(
                name=loss_type.value,
                value=value,
                is_computed=False,
                description=descriptions[loss_type]
            )

        return self

    def calculate_total_loss_factor(self) -> float:
        """
        Calculate total loss factor using multiplicative formula.

        Formula: Loss_factor = (1-l1) * (1-l2) * ... * (1-ln)

        Returns:
            Total loss factor (0-1) to multiply with gross AEP

        Example:
            >>> losses = WindFarmLosses()
            >>> losses.add_loss('loss1', 0.03)  # 3%
            >>> losses.add_loss('loss2', 0.02)  # 2%
            >>> losses.calculate_total_loss_factor()
            0.9506  # (1-0.03) * (1-0.02) = 0.97 * 0.98 = 0.9506
        """
        loss_factor = 1.0
        for loss in self._losses.values():
            loss_factor *= (1 - loss.value)
        return loss_factor

    def calculate_total_loss_percentage(self) -> float:
        """
        Calculate total loss as percentage.

        Returns:
            Total loss percentage (0-100)

        Example:
            >>> losses = WindFarmLosses()
            >>> losses.add_loss('loss1', 0.03)  # 3%
            >>> losses.add_loss('loss2', 0.02)  # 2%
            >>> losses.calculate_total_loss_percentage()
            4.94  # 1 - 0.9506 = 0.0494 = 4.94%
        """
        return (1 - self.calculate_total_loss_factor()) * 100

    def calculate_net_aep(self, gross_aep: float) -> float:
        """
        Calculate net AEP by applying all losses to gross AEP.

        Args:
            gross_aep: Gross annual energy production (GWh or any unit)

        Returns:
            Net AEP after applying all losses (same unit as input)

        Example:
            >>> losses = WindFarmLosses()
            >>> losses.add_default_losses()
            >>> losses.calculate_net_aep(1000.0)  # 1000 GWh gross
            918.2  # Net AEP after ~8.8% total losses
        """
        return gross_aep * self.calculate_total_loss_factor()

    def get_loss_breakdown(self) -> Dict[str, Dict]:
        """
        Get detailed breakdown of all loss categories.

        Returns:
            Dictionary with loss category details

        Example:
            >>> losses = WindFarmLosses()
            >>> losses.add_loss('wake_losses', 0.08, is_computed=True)
            >>> breakdown = losses.get_loss_breakdown()
            >>> print(breakdown['wake_losses']['percentage'])
            8.0
        """
        return {
            name: loss.to_dict()
            for name, loss in self._losses.items()
        }

    def get_computed_losses(self) -> Dict[str, LossCategory]:
        """Get only computed losses (wake, curtailment)."""
        return {
            name: loss
            for name, loss in self._losses.items()
            if loss.is_computed
        }

    def get_user_losses(self) -> Dict[str, LossCategory]:
        """Get only user-specified losses (availability, electrical, etc.)."""
        return {
            name: loss
            for name, loss in self._losses.items()
            if not loss.is_computed
        }

    def to_dict(self) -> Dict:
        """
        Export complete losses summary to dictionary.

        Returns:
            Dictionary with all loss information
        """
        return {
            'loss_categories': self.get_loss_breakdown(),
            'total_loss_factor': self.calculate_total_loss_factor(),
            'total_loss_percentage': self.calculate_total_loss_percentage(),
            'computed_losses': {
                name: loss.percentage
                for name, loss in self.get_computed_losses().items()
            },
            'user_losses': {
                name: loss.percentage
                for name, loss in self.get_user_losses().items()
            }
        }

    def __repr__(self) -> str:
        n_losses = len(self._losses)
        total_loss_pct = self.calculate_total_loss_percentage()
        return (
            f"WindFarmLosses(n_categories={n_losses}, "
            f"total_loss={total_loss_pct:.2f}%)"
        )


def create_default_losses(
    wake_loss: Optional[float] = None,
    curtailment_sector: Optional[float] = None,
    **kwargs
) -> WindFarmLosses:
    """
    Create WindFarmLosses with defaults and optional computed losses.

    Args:
        wake_loss: Wake loss fraction (0-1) if computed
        curtailment_sector: Sector curtailment loss fraction (0-1) if computed
        **kwargs: Override default loss values (see WindFarmLosses.add_default_losses)

    Returns:
        Configured WindFarmLosses instance

    Example:
        >>> losses = create_default_losses(
        ...     wake_loss=0.08,
        ...     availability_turbines=0.02
        ... )
    """
    losses = WindFarmLosses()

    # Add computed losses if provided
    if wake_loss is not None:
        losses.add_loss(
            LossType.WAKE.value,
            wake_loss,
            is_computed=True,
            description="Wake losses from turbine interactions"
        )

    if curtailment_sector is not None:
        losses.add_loss(
            LossType.CURTAILMENT_SECTOR.value,
            curtailment_sector,
            is_computed=True,
            description="Curtailment from sector management"
        )

    # Add default losses with any overrides
    losses.add_default_losses(**kwargs)

    return losses
