"""Base class shared by every component type.

A *component* is the atomic element of a circuit: a cylinder, a valve,
a relay, a timer... Each component exposes named *terminals* (connection
points). Terminals are connected to circuit nodes
(:class:`opencade.models.node.Node`), which is how a component exchanges
physical quantities (pressure, voltage, logic level) with the rest of the
circuit.

Design note: the base class builds the initial state of a component
*lazily*, by calling :meth:`Component._initial_state` at the end of
``__init__``. Subclasses must therefore assign their own attributes
(parameters) **before** calling ``super().__init__()``.
"""

from typing import Any, Dict, Optional

from ..models.node import Node


class Component:
    """Abstract base class for every circuit component."""

    #: Physical domain of the component ("pneumatic", "electrical", "logic").
    domain = "generic"

    def __init__(self, name: str = "") -> None:
        self.id: Optional[int] = None
        self.name = name
        self.terminals: Dict[str, Optional[Node]] = {}
        self.state: Dict[str, Any] = self._initial_state()

    # ---------------------------------------------------------- state
    def _initial_state(self) -> Dict[str, Any]:
        """Return the default (power-on) state.

        Subclasses override this method. By the time it is called, all
        subclass parameters are already available.
        """
        return {}

    def reset(self) -> None:
        """Restore the component to its initial state."""
        self.state = self._initial_state()

    def update(self, dt: float) -> None:
        """Advance the component dynamics by *dt* seconds.

        The default implementation does nothing; that is appropriate for
        instantaneous elements (gates, contacts...). Stateful elements
        override it.
        """
        del dt

    # -------------------------------------------------------- terminals
    def connect_terminal(self, terminal_name: str, node: Optional[Node]) -> None:
        """Connect (or disconnect, with ``node=None``) a terminal to a node."""
        self.terminals[terminal_name] = node

    def get_terminal(self, terminal_name: str) -> Optional[Node]:
        """Return the node connected to *terminal_name* (or ``None``)."""
        return self.terminals.get(terminal_name)

    # ---------------------------------------------------------- helpers
    @property
    def description(self) -> str:
        """Short, human-readable summary of the component and its state."""
        state = ", ".join(f"{key}={value!r}" for key, value in sorted(self.state.items()))
        return f"{self.__class__.__name__}(id={self.id}, name={self.name!r}, {state})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name={self.name!r})"
