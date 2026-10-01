"""opencade: a free and open-source electro-pneumatic and industrial
automation simulator.

opencade is an educational simulator inspired by CADe SIMU, rebuilt with
modern Python and permissively licensed components.

The public API is organised around three main packages:

* :mod:`opencade.models` - circuit topology (nodes, wires, circuit).
* :mod:`opencade.components` - pneumatic, electrical and logic components.
* :mod:`opencade.solvers` - the domain solvers driven by
  :class:`opencade.simulator.Simulator`.
"""

__version__ = "0.1.0"
__author__ = "opencade contributors"
__email__ = "opencade@example.org"

__all__ = ["__version__", "__author__", "__email__"]
