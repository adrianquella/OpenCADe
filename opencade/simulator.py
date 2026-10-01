"""Simulation engine: coordinates the domain solvers in time.

The simulator owns the current :class:`~opencade.models.circuit.Circuit`
and advances it step by step. Every step runs the three domain solvers
in a physically sensible order:

1. Logic elements (PLC-style gates, timers) react to sensor signals.
2. The electrical network propagates voltages, energising relay coils
   and solenoid valve coils.
3. The pneumatic network routes pressure and moves the cylinders.
"""

import logging
import threading
import time
from typing import Optional

from .models.circuit import Circuit
from .solvers.electrical_solver import ElectricalSolver
from .solvers.logic_solver import LogicSolver
from .solvers.pneumatic_solver import PneumaticSolver

LOGGER = logging.getLogger(__name__)


class Simulator:
    """Drives the simulation of a circuit, usually at real-time speed."""

    def __init__(self, circuit: Circuit, time_step: float = 0.01) -> None:
        self.circuit = circuit
        self.time_step = time_step
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_time = 0.0
        self._step_count = 0

        # Domain solvers.
        self.logic_solver = LogicSolver(circuit)
        self.electrical_solver = ElectricalSolver(circuit)
        self.pneumatic_solver = PneumaticSolver(circuit)

    # ------------------------------------------------------------------ API
    @property
    def running(self) -> bool:
        """Whether the simulation loop is currently active."""
        return self._running

    @property
    def time(self) -> float:
        """Simulated time (s) since the last reset."""
        return self._current_time

    @property
    def step_count(self) -> int:
        """Number of steps executed since the last reset."""
        return self._step_count

    def start(self) -> None:
        """Start the simulation loop in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, name="opencade-sim", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the simulation loop and wait for the worker to finish."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def reset(self) -> None:
        """Stop the simulation and restore every component to its initial state."""
        self.stop()
        self._current_time = 0.0
        self._step_count = 0
        for component in self.circuit.components:
            component.reset()

    def step(self) -> None:
        """Advance the simulation by one time step (blocking; for debugging/testing)."""
        self._advance()
        self._current_time += self.time_step
        self._step_count += 1

    # ------------------------------------------------------------- internal
    def _advance(self) -> None:
        """Run one full solver pass over the circuit."""
        self.logic_solver.solve_step(self.time_step)
        self.electrical_solver.solve_step(self.time_step)
        self.pneumatic_solver.solve_step(self.time_step)

    def _run_loop(self) -> None:
        """Main loop, executed in a worker thread at real-time speed."""
        while self._running:
            started = time.perf_counter()
            try:
                self._advance()
                self._current_time += self.time_step
                self._step_count += 1
            except Exception:  # pragma: no cover - defensive
                LOGGER.exception("Simulation step failed; stopping the simulation")
                break
            sleep_time = self.time_step - (time.perf_counter() - started)
            if sleep_time > 0.0:
                time.sleep(sleep_time)
