"""Circuit node: a physical connection point shared by several terminals.

All terminals connected to the same node form a single
electrical/pneumatic "domain": in the current (ideal) model they share
the same physical quantity (pressure, voltage, logic level).
"""

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:  # pragma: no cover
    from .wire import Wire


class Node:
    """A single connection point of the circuit."""

    def __init__(self, id: int = 0, domain: str = "pneumatic") -> None:
        self.id = id
        #: Physical domain of the node ("pneumatic", "electrical", "logic").
        self.domain = domain
        #: Wires leaving this node.
        self.wires: List["Wire"] = []
        #: Physical state of the node, shared by every connected terminal.
        self.state: Dict[str, Any] = {
            "pressure": 0.0,  # Pa (gauge), pneumatic domain
            "voltage": 0.0,  # V, electrical domain
            "signal": False,  # bool, logic domain
            "flow": 0.0,  # m^3/s, pneumatic domain (reserved)
            "current": 0.0,  # A, electrical domain (reserved)
        }

    def connected_nodes(self) -> List["Node"]:
        """Return the neighbouring nodes joined to this one by a wire."""
        neighbours: List["Node"] = []
        for wire in self.wires:
            other = wire.get_other_node(self)
            if other is not None:
                neighbours.append(other)
        return neighbours

    def __repr__(self) -> str:
        return f"Node(id={self.id}, domain={self.domain!r})"
