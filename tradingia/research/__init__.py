"""Research workflows for TradingIA."""

from tradingia.research.dashboard import ResearchDashboard, ResearchReport
from tradingia.research.optimizer import OptimizationResult, ParameterOptimizer, build_parameter_grid

__all__ = [
    "OptimizationResult",
    "ParameterOptimizer",
    "ResearchDashboard",
    "ResearchReport",
    "build_parameter_grid",
]
