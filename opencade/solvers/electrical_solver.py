"""Electrical network solver (simplified rail propagation).

Strategy: electrical nodes are grouped into *domains* (connected
components through wires). Then the solver iterates:

1. Power supplies fix their rails (+ rail at the supply voltage,
   - rail at 0 V).
2. Closed contacts (switches, relay contacts) propagate the *higher*
   voltage between the two domains they connect.
3. Loads update their state: relay coils and solenoid valve coils are
   energised when the voltage drop across them is high enough; motors
   and sensors advance their dynamics.

The iteration runs until the network is stable (or a bounded number of
passes, which keeps feedback loops fast).

Ideal-conductor assumption: closed contacts propagate the voltage
without drop, so the model targets control circuits, not power analysis.
"""

from typing import Dict, List, Optional

from ..components.electrical import Motor, PowerSupply, Relay, Sensor, Switch
from ..components.pneumatic import Valve
from ..models.circuit import Circuit
from ..models.node import Node

#: Maximum number of propagation passes per step (bounds feedback loops).
MAX_RELAXATION_PASSES = 32


class ElectricalSolver:
    """Computes the rail voltages and energises the loads (coils, ...)."""

    def __init__(self, circuit: Circuit, coil_energisation_ratio: float = 0.8) -> None:
        self.circuit = circuit
        #: A coil is considered actuated when it sees this fraction of
        #: its nominal voltage.
        self.coil_energisation_ratio = coil_energisation_ratio

    def solve_step(self, dt: float) -> None:
        """Propagate voltages through the electrical network."""
        mapping: Dict[int, int] = {}
        domains: List[List[Node]] = []
        for node in self.circuit.nodes_of_domain("electrical"):
            if node.id in mapping:
                continue
            index = len(domains)
            domains.append([node])
            mapping[node.id] = index
            stack = [node]
            while stack:
                current = stack.pop()
                for wire in current.wires:
                    other = wire.get_other_node(current)
                    if other is not None and other.id not in mapping:
                        mapping[other.id] = index
                        domains[index].append(other)
                        stack.append(other)

        if not domains:
            return

        voltage: Dict[int, float] = {index: 0.0 for index in range(len(domains))}

        # Rails: power supplies fix their + and - domain voltages.
        for supply in self.circuit.components_of_type(PowerSupply):
            plus = supply.get_terminal("+")
            minus = supply.get_terminal("-")
            if plus is not None and plus.id in mapping:
                voltage[mapping[plus.id]] = supply.voltage
            if minus is not None and minus.id in mapping:
                voltage[mapping[minus.id]] = 0.0

        # Relaxation: propagate through closed contacts and update the
        # loads until the network is stable.
        for _ in range(MAX_RELAXATION_PASSES):
            changed = self._propagate_closed_contacts(voltage, mapping)
            changed = self._update_electrical_loads(voltage, mapping) or changed
            if not changed:
                break

        # Publish the node voltages and advance the stateful loads.
        for node in self.circuit.nodes_of_domain("electrical"):
            node.state["voltage"] = voltage[mapping[node.id]]
        for motor in self.circuit.components_of_type(Motor):
            motor.update(dt)
        for sensor in self.circuit.components_of_type(Sensor):
            sensor.update(dt)

    # ------------------------------------------------------------- internal
    @staticmethod
    def _dom(mapping: Dict[int, int], node: Optional[Node]) -> Optional[int]:
        """Index of the domain containing *node* (or ``None``)."""
        if node is None:
            return None
        return mapping.get(node.id)

    @staticmethod
    def _propagate_between(
        a: Optional[int], b: Optional[int], voltage: Dict[int, float]
    ) -> bool:
        """A closed contact passes the higher voltage to the other side."""
        if a is None or b is None or a == b:
            return False
        va, vb = voltage[a], voltage[b]
        if va > vb:
            voltage[b] = va
            return True
        if vb > va:
            voltage[a] = vb
            return True
        return False

    def _propagate_closed_contacts(
        self, voltage: Dict[int, float], mapping: Dict[int, int]
    ) -> bool:
        """Propagate voltage through every currently-closed contact."""
        changed = False
        for switch in self.circuit.components_of_type(Switch):
            if not switch.closed:
                continue
            changed = self._propagate_between(
                self._dom(mapping, switch.get_terminal("in")),
                self._dom(mapping, switch.get_terminal("out")),
                voltage,
            ) or changed
        for relay in self.circuit.components_of_type(Relay):
            common = self._dom(mapping, relay.get_terminal("common"))
            if relay.energized:
                contact = self._dom(mapping, relay.get_terminal("normally_open"))
            else:
                contact = self._dom(mapping, relay.get_terminal("normally_closed"))
            changed = self._propagate_between(common, contact, voltage) or changed
        return changed

    def _update_electrical_loads(
        self, voltage: Dict[int, float], mapping: Dict[int, int]
    ) -> bool:
        """Energise relay coils and solenoid valves.

        Returns True if any load state changed.
        """
        changed = False
        for relay in self.circuit.components_of_type(Relay):
            energised = self._coil_energised(
                mapping,
                relay.get_terminal("coil_in"),
                relay.get_terminal("coil_out"),
                relay.coil_voltage,
                voltage,
            )
            if relay.state["energized"] != energised:
                relay.state["energized"] = energised
                changed = True
        for valve in self.circuit.components_of_type(Valve):
            energised = self._coil_energised(
                mapping,
                valve.get_terminal("CI"),
                valve.get_terminal("CO"),
                valve.coil_voltage,
                voltage,
            )
            if valve.state["coil_energized"] != energised:
                valve.state["coil_energized"] = energised
                valve.state["position"] = 1.0 if energised else 0.0
                changed = True
        return changed

    def _coil_energised(
        self,
        mapping: Dict[int, int],
        coil_in: Optional[Node],
        coil_out: Optional[Node],
        coil_voltage: float,
        voltage: Dict[int, float],
    ) -> bool:
        """Whether the voltage drop across the coil exceeds the threshold."""
        a = self._dom(mapping, coil_in)
        b = self._dom(mapping, coil_out)
        if a is None or b is None:
            return False
        return (voltage[a] - voltage[b]) >= self.coil_energisation_ratio * coil_voltage

