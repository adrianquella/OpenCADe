"""Logic components (PLC-style): boolean gates and timers.

Logic elements exchange pure boolean levels through the ``signal``
channel of their terminal nodes.
"""

from typing import Any, Dict

from .base import Component


class LogicComponent(Component):
    """Base class for logic components."""

    domain = "logic"

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.terminals["in"] = None
        self.terminals["out"] = None

    # ---------------------------------------------------------- helpers
    def _read_input(self, terminal_name: str) -> bool:
        """Read the boolean level of a terminal (False if unconnected)."""
        node = self.get_terminal(terminal_name)
        if node is None:
            return False
        return bool(node.state.get("signal", False))

    def _write_output(self, value: bool) -> None:
        """Publish a boolean level on the ``out`` terminal."""
        out = self.get_terminal("out")
        if out is not None:
            out.state["signal"] = bool(value)


class ANDGate(LogicComponent):
    """Boolean AND gate with two inputs (``in`` and ``in2``)."""

    def __init__(self, name: str = "AND") -> None:
        super().__init__(name)
        self.terminals["in2"] = None

    def _initial_state(self) -> Dict[str, Any]:
        return {"output": False}

    def update(self, dt: float) -> None:
        del dt
        self.state["output"] = self._read_input("in") and self._read_input("in2")
        self._write_output(self.state["output"])


class ORGate(LogicComponent):
    """Boolean OR gate with two inputs (``in`` and ``in2``)."""

    def __init__(self, name: str = "OR") -> None:
        super().__init__(name)
        self.terminals["in2"] = None

    def _initial_state(self) -> Dict[str, Any]:
        return {"output": False}

    def update(self, dt: float) -> None:
        del dt
        self.state["output"] = self._read_input("in") or self._read_input("in2")
        self._write_output(self.state["output"])


class NOTGate(LogicComponent):
    """Boolean NOT gate (inverter)."""

    def _initial_state(self) -> Dict[str, Any]:
        return {"output": False}

    def update(self, dt: float) -> None:
        del dt
        self.state["output"] = not self._read_input("in")
        self._write_output(self.state["output"])


class Timer(LogicComponent):
    """On-delay (TO) timer.

    The output goes True only after *preset_time* seconds of continuous
    input; it resets immediately when the input goes False.
    """

    def __init__(self, name: str = "Timer", preset_time: float = 1.0) -> None:
        self.preset_time = preset_time
        super().__init__(name)

    def _initial_state(self) -> Dict[str, Any]:
        return {"elapsed": 0.0, "output": False}

    def update(self, dt: float) -> None:
        if self._read_input("in"):
            self.state["elapsed"] += dt
            if self.state["elapsed"] >= self.preset_time:
                self.state["output"] = True
        else:
            self.state["elapsed"] = 0.0
            self.state["output"] = False
        self._write_output(self.state["output"])
