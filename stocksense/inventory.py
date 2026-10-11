"""A transparent demonstration order rule, with delivery timing made explicit."""
from dataclasses import dataclass
import math
from numbers import Integral

import numpy as np


@dataclass(frozen=True)
class StockPlan:
    coverage_days: int
    forecast_demand: float
    target_stock: float
    inventory_position: int
    suggested_order: int
    demand_before_delivery: float
    shortage_before_delivery: float


def plan_stock(predictions, *, stock: int, outstanding: int, lead_days: int,
               review_days: int, buffer: int) -> StockPlan:
    values = np.asarray(predictions, dtype=float)
    if values.shape != (7,) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Supply seven finite, non-negative daily forecast quantities.")
    inputs = {"Stock available": stock, "Outstanding units": outstanding,
              "Supplier lead time": lead_days, "Review interval": review_days, "Buffer stock": buffer}
    for name, value in inputs.items():
        if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
            raise ValueError(f"{name} must be a non-negative whole number.")
    if review_days < 1:
        raise ValueError("Review interval must be at least one day.")
    coverage = lead_days + review_days
    if coverage > 7:
        raise ValueError("Lead time plus review interval must not exceed seven days.")
    # Delivery occurs after lead_days forecast days; zero means before day 1.
    demand = float(values[:coverage].sum())
    before = float(values[:lead_days].sum())
    position = int(stock + outstanding)
    target = demand + buffer
    return StockPlan(coverage, demand, target, position, math.ceil(max(0, target - position)),
                     before, max(0, before - stock))
