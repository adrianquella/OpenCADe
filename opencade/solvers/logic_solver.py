"""Logic domain solver.

Logic elements are mostly stateless (except for timers), so each step
simply re-evaluates every logic component.
"""

from ..components.logic import LogicComponent
from ..models.circuit import Circuit


class LogicSolver:
    """Evaluates the logic network (gates, timers) on every step."""

    def __init__(self, circuit: Circuit) -> None:
        self.circuit = circuit

    def solve_step(self, dt: float) -> None:
        """Advance every logic component by one step."""
        for component in self.circuit.components_of_type(LogicComponent):
            component.update(dt)
