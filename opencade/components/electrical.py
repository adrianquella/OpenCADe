"""Electrical components: power supply, switches, relays, motors, sensors.

The electrical model is intentionally simplified: closed contacts
propagate the *higher* rail voltage to the connected domain without any
drop (ideal-conductor assumption). This is enough to simulate control
circuits (relays, solenoids, motors) but not power analysis.
"""

from typing import Any, Dict

from .base import Component


class ElectricalComponent(Component):
    """Base class for electrical components."""

    domain = "electrical"

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.terminals["in"] = None
        self.terminals["out"] = None


class PowerSupply(ElectricalComponent):
    """Ideal DC power supply (e.g. a 24 V control transformer).

    Terminals:
      + - positive rail
      - - negative rail (reference, 0 V)
    """

    def __init__(self, name: str = "PowerSupply", voltage: float = 24.0) -> None:
        # NOTE: assign before super().__init__ (see the base class docstring).
        self.voltage = voltage
        super().__init__(name)

    def _initial_state(self) -> Dict[str, Any]:
        return {"voltage": self.voltage}


class Switch(ElectricalComponent):
    """Simple make/break contact (pushbutton, limit switch contact, ...).

    ``normally_closed`` selects the default contact state. The state is
    driven from outside (GUI, sensor, ...) through :meth:`set_closed`.
    """

    def __init__(self, name: str = "Switch", normally_closed: bool = False) -> None:
        self.normally_closed = normally_closed
        super().__init__(name)

    def _initial_state(self) -> Dict[str, Any]:
        return {"closed": self.normally_closed}

    @property
    def closed(self) -> bool:
        """Whether the contact currently closes the circuit."""
        return self.state["closed"]

    def set_closed(self, closed: bool) -> None:
        """Force the contact state (open or closed)."""
        self.state["closed"] = bool(closed)


class Relay(ElectricalComponent):
    """Electromechanical relay with form-A (NO) and form-B (NC) contacts.

    Terminals:
      coil_in / coil_out - electromagnetic coil
      common / normally_open / normally_closed - contacts
    """

    def __init__(
        self,
        name: str = "Relay",
        coil_voltage: float = 24.0,
        coil_resistance: float = 240.0,
    ) -> None:
        self.coil_voltage = coil_voltage
        self.coil_resistance = coil_resistance
        super().__init__(name)
        self.terminals["coil_in"] = None
        self.terminals["coil_out"] = None
        self.terminals["common"] = None
        self.terminals["normally_open"] = None
        self.terminals["normally_closed"] = None

    def _initial_state(self) -> Dict[str, Any]:
        return {"energized": False}

    @property
    def energized(self) -> bool:
        """Whether the coil is energised and the contacts have switched."""
        return self.state["energized"]

    def update(self, dt: float) -> None:
        """Keep the contacts following the coil state.

        Contacts switch instantaneously for now; a mechanical time
        constant can be added in a future release.
        """
        del dt


class Motor(ElectricalComponent):
    """Simplified DC motor.

    The motor accelerates towards a rated speed with a first-order time
    constant when powered, and coasts to a stop otherwise.

    Terminals:
      + / - - power terminals
    """

    def __init__(
        self,
        name: str = "Motor",
        voltage: float = 24.0,
        rated_speed: float = 120.0,
        time_constant: float = 0.5,
    ) -> None:
        self.voltage = voltage
        self.rated_speed = rated_speed      # rad/s
        self.time_constant = time_constant  # s
        super().__init__(name)
        self.terminals["+"] = None
        self.terminals["-"] = None

    def _initial_state(self) -> Dict[str, Any]:
        return {"speed": 0.0, "torque": 0.0}

    def update(self, dt: float) -> None:
        """Integrate the speed towards the target speed."""
        plus = self.get_terminal("+")
        minus = self.get_terminal("-")
        v_plus = plus.state.get("voltage", 0.0) if plus is not None else 0.0
        v_minus = minus.state.get("voltage", 0.0) if minus is not None else 0.0
        applied = v_plus - v_minus

        if abs(applied) < 0.5 * self.voltage:
            target = 0.0
        elif applied > 0.0:
            target = self.rated_speed
        else:
            target = -self.rated_speed

        alpha = min(1.0, dt / self.time_constant)
        self.state["speed"] = self.state["speed"] + alpha * (target - self.state["speed"])
        self.state["torque"] = 0.0


class Sensor(ElectricalComponent):
    """Generic threshold sensor (limit switch, pressure switch, ...).

    The sensor reads a physical quantity from its ``signal`` terminal
    (e.g. the pneumatic pressure of the connected domain) and exposes a
    digital level on its ``out`` terminal.

    Terminals:
      signal - physical input
      out - digital output
    """

    def __init__(
        self,
        name: str = "Sensor",
        threshold: float = 2.0e5,
        channel: str = "pressure",
    ) -> None:
        self.threshold = threshold
        self.channel = channel  # key read from the terminal node state
        super().__init__(name)
        self.terminals["signal"] = None
        self.terminals["out"] = None

    def _initial_state(self) -> Dict[str, Any]:
        return {"active": False}

    def update(self, dt: float) -> None:
        """Evaluate the threshold and publish the digital signal."""
        del dt
        source = self.get_terminal("signal")
        value = source.state.get(self.channel, 0.0) if source is not None else 0.0
        self.state["active"] = bool(value >= self.threshold)
        out = self.get_terminal("out")
        if out is not None:
            out.state["signal"] = self.state["active"]
