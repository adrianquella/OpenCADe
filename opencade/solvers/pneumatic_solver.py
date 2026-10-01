"""Pneumatic network solver.

The solver works on *pressure domains*: a domain is a set of nodes joined
by wires (ideal pipes). Every step:

1. Every domain is reset to atmospheric pressure (0 Pa gauge).
2. Air supplies pressurise the domain they feed.
3. Directional valves route the supply pressure between their ports,
   depending on their position.
4. Cylinders integrate the net chamber pressure into rod motion.

The model is intentionally simplified (quasi-static pressures, no chamber
volumes, no compressible flow), which is enough for educational
simulation of control circuits.
"""

from typing import Dict, List

from ..components.pneumatic import AirSupply, Cylinder, Valve
from ..models.circuit import Circuit
from ..models.node import Node


class PneumaticSolver:
    """Routes air pressure through the pneumatic network."""

    def __init__(self, circuit: Circuit) -> None:
        self.circuit = circuit

    def solve_step(self, dt: float) -> None:
        """Propagate pressure through the network and advance the actuators."""
        mapping: Dict[int, int] = {}
        domains: List[List[Node]] = []
        for node in self.circuit.nodes_of_domain("pneumatic"):
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

        # 1) Every domain starts at atmospheric pressure (0 Pa gauge).
        for domain in domains:
            for node in domain:
                node.state["pressure"] = 0.0

        # 2) Air supplies pressurise their own domains.
        for supply in self.circuit.components_of_type(AirSupply):
            out = supply.get_terminal("out")
            if out is None or out.id not in mapping:
                continue
            for node in domains[mapping[out.id]]:
                node.state["pressure"] = supply.pressure

        # 3) Valves route pressure according to their position.
        for valve in self.circuit.components_of_type(Valve):
            self._route_valve(valve, domains, mapping)

        # 4) Cylinders move according to the net chamber pressure.
        for cylinder in self.circuit.components_of_type(Cylinder):
            cylinder.update(dt)

    # ------------------------------------------------------------- internal
    @staticmethod
    def _route_valve(
        valve: Valve, domains: List[List[Node]], mapping: Dict[int, int]
    ) -> None:
        """Route the supply pressure through the valve ports."""
        p_port = valve.get_terminal("P")
        if p_port is None or p_port.id not in mapping:
            return
        supply_pressure = p_port.state.get("pressure", 0.0)
        if supply_pressure <= 0.0:
            return

        if valve.state.get("position", 0.0) > 0.5:
            pressurise = valve.get_terminal("A")
            exhaust = valve.get_terminal("B")
        else:
            pressurise = valve.get_terminal("B")
            exhaust = valve.get_terminal("A")

        for port, pressure in ((pressurise, supply_pressure), (exhaust, 0.0)):
            if port is None or port.id not in mapping:
                continue
            for node in domains[mapping[port.id]]:
                node.state["pressure"] = pressure
