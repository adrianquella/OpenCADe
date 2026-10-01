"""Pneumatic components: air supply, directional valve and cylinders.

The physics implemented here is intentionally simplified (quasi-static
pressures, constant travel speed) so that control-circuit behaviour is
easy to follow. A full fluid-dynamic model (compressible flow, chamber
volumes) is planned for a future release.
"""

from typing import Any, Dict

from ..utils.math_utils import cylinder_area
from .base import Component


class PneumaticComponent(Component):
    """Base class for pneumatic components."""

    domain = "pneumatic"

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.terminals["in"] = None
        self.terminals["out"] = None


class AirSupply(PneumaticComponent):
    """Ideal constant-pressure air supply (gauge pressure, in Pa).

    The pneumatic solver reads the ``out`` terminal of every air supply
    and pressurises the whole connected domain at ``pressure``.

    Terminals:
      out - supply port.
    """

    def __init__(self, name: str = "AirSupply", pressure: float = 6.0e5) -> None:
        # NOTE: assign before super().__init__ (see the base class docstring).
        self.pressure = pressure
        super().__init__(name)

    def _initial_state(self) -> Dict[str, Any]:
        return {"pressure": self.pressure}


class Valve(PneumaticComponent):
    """Directional control valve (5/2) with a solenoid coil.

    Port naming follows the ISO 1219 convention:

    - ``P`` - supply (pressure)
    - ``A`` / ``B`` - working ports
    - ``EA`` / ``EB`` - exhaust of ``A`` / ``B``
    - ``CI`` / ``CO`` - solenoid coil terminals (electrical actuation)

    With the coil de-energised (``position == 0.0``) the valve routes
    ``P -> B`` and ``A -> EA``; energised (``position == 1.0``) it routes
    ``P -> A`` and ``B -> EB``.
    """

    def __init__(self, name: str = "Valve", coil_voltage: float = 24.0) -> None:
        self.coil_voltage = coil_voltage
        super().__init__(name)
        self.terminals["P"] = None
        self.terminals["A"] = None
        self.terminals["B"] = None
        self.terminals["EA"] = None
        self.terminals["EB"] = None
        self.terminals["CI"] = None
        self.terminals["CO"] = None

    def _initial_state(self) -> Dict[str, Any]:
        return {"position": 0.0, "coil_energized": False}


class Cylinder(PneumaticComponent):
    """Double-acting pneumatic cylinder.

    ``position`` is the rod extension in metres: 0 = fully retracted,
    ``stroke`` = fully extended. Motion is driven by the net pressure
    difference between the cap and the rod chamber.

    Terminals:
      cap - cap-end chamber port
      rod - rod-end chamber port
    """

    def __init__(
        self,
        name: str = "Cylinder",
        bore: float = 0.05,
        stroke: float = 0.10,
        mass: float = 5.0,
        max_speed: float = 0.2,
        pressure_threshold: float = 500.0,
    ) -> None:
        self.bore = bore                              # m, piston diameter
        self.stroke = stroke                          # m, travel
        self.mass = mass                              # kg, moving mass
        self.max_speed = max_speed                    # m/s, travel speed limit
        self.pressure_threshold = pressure_threshold  # Pa, static friction model
        self.area = cylinder_area(bore)               # m^2
        super().__init__(name)
        self.terminals["cap"] = None
        self.terminals["rod"] = None

    def _initial_state(self) -> Dict[str, Any]:
        return {"position": 0.0, "velocity": 0.0, "force": 0.0}

    @property
    def extended(self) -> bool:
        """Whether the cylinder is fully extended."""
        return self.state["position"] >= self.stroke - 1e-9

    @property
    def retracted(self) -> bool:
        """Whether the cylinder is fully retracted."""
        return self.state["position"] <= 1e-9

    def update(self, dt: float) -> None:
        """Integrate the cylinder motion from the chamber pressures."""
        cap = self.get_terminal("cap")
        rod = self.get_terminal("rod")
        p_cap = cap.state.get("pressure", 0.0) if cap is not None else 0.0
        p_rod = rod.state.get("pressure", 0.0) if rod is not None else 0.0
        delta_p = p_cap - p_rod
        self.state["force"] = delta_p * self.area

        if abs(delta_p) < self.pressure_threshold:
            velocity = 0.0
        elif delta_p > 0.0:
            velocity = self.max_speed
        else:
            velocity = -self.max_speed

        position = self.state["position"] + velocity * dt
        self.state["position"] = max(0.0, min(self.stroke, position))
        self.state["velocity"] = velocity
