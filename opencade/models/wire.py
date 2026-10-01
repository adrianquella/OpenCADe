"""Wire: an ideal conductor joining two nodes of the same domain.

Wires are perfect conductors (no resistance, no capacitance/inductance,
no leakage). A couple of physical parameters are kept to make the
transition to a parasitic model easier in the future.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    from .node import Node


class Wire:
    """Ideal connection between two :class:`~opencade.models.node.Node`."""

    def __init__(
        self,
        id: int = 0,
        node1: Optional["Node"] = None,
        node2: Optional["Node"] = None,
        resistance: float = 0.0,
        diameter: float = 0.0,
    ) -> None:
        self.id = id
        self.node1 = node1
        self.node2 = node2
        #: Electrical resistance in ohms. 0 means an ideal wire.
        self.resistance = resistance
        #: Diameter in metres (pneumatic line / conductor gauge).
        self.diameter = diameter

    def get_other_node(self, node: "Node") -> Optional["Node"]:
        """Given one of the connected nodes, return the other one."""
        if node is self.node1:
            return self.node2
        if node is self.node2:
            return self.node1
        return None

    def __repr__(self) -> str:
        n1 = self.node1.id if self.node1 is not None else None
        n2 = self.node2.id if self.node2 is not None else None
        return f"Wire(id={self.id}, nodes=({n1}, {n2}))"
