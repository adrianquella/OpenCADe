"""Circuit: the complete topology of components, nodes and wires.

The :class:`Circuit` is the single source of truth for everything the
user has built. It is shared by the GUI, the simulation engine and the
domain solvers.
"""

from typing import List, Optional

from ..components.base import Component
from .node import Node
from .wire import Wire


class Circuit:
    """Container for everything the user has built."""

    def __init__(self) -> None:
        self.nodes: List[Node] = []
        self.wires: List[Wire] = []
        self.components: List[Component] = []
        self._node_id = 0
        self._wire_id = 0
        self._component_id = 0

    # ------------------------------------------------- construction helpers
    def add_node(self, domain: str = "pneumatic") -> Node:
        """Create and register a new node in the given domain."""
        node = Node(id=self._node_id, domain=domain)
        self._node_id += 1
        self.nodes.append(node)
        return node

    def add_wire(self, node1: Node, node2: Node, **kwargs) -> Wire:
        """Create and register a wire joining two nodes of the same domain."""
        if node1.domain != node2.domain:
            raise ValueError(
                "Cannot wire nodes of different domains "
                f"({node1.domain!r} vs {node2.domain!r})"
            )
        wire = Wire(id=self._wire_id, node1=node1, node2=node2, **kwargs)
        self._wire_id += 1
        self.wires.append(wire)
        node1.wires.append(wire)
        node2.wires.append(wire)
        return wire

    def add_component(self, component: Component) -> Component:
        """Register a component and assign it the next free id."""
        component.id = self._component_id
        self._component_id += 1
        self.components.append(component)
        return component

    def remove_component(self, component: Component) -> None:
        """Remove a component from the circuit (wires stay intact)."""
        self.components.remove(component)

    # ---------------------------------------------------------------- queries
    def nodes_of_domain(self, domain: str) -> List[Node]:
        """Return the nodes belonging to the given physical domain."""
        return [node for node in self.nodes if node.domain == domain]

    def components_of_type(self, klass: type) -> List[Component]:
        """Return the registered components of the given type (or subclass)."""
        return [
            component
            for component in self.components
            if isinstance(component, klass)
        ]

    def get_node_by_id(self, node_id: int) -> Optional[Node]:
        """Find a node by id, or return ``None`` if it does not exist."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def clear(self) -> None:
        """Remove every node, wire and component."""
        for node in self.nodes:
            node.wires = []
        self.nodes.clear()
        self.wires.clear()
        self.components.clear()
        self._node_id = 0
        self._wire_id = 0
        self._component_id = 0
