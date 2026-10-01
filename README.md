# opencade

A free and open-source **electro-pneumatic and industrial automation
simulator** written in Python. opencade is inspired by the classic
**CADe SIMU** and rebuilt with a modern, extensible,
permissively-licensed architecture.

> Status: early development (v0.1.0). The simulation core and the
> component library work; the graphical canvas is a placeholder.

## Features

- **Component library**: pneumatic (air supply, 5/2 valve,
  double-acting cylinder), electrical (power supply, switch, relay,
  motor, threshold sensor) and logic (AND/OR/NOT gates, on-delay
  timer).
- **Time-stepped simulation engine** that coordinates three domain
  solvers (logic, electrical, pneumatic) in a physically sensible
  order.
- **Domain model**: nodes and wires form ideal "domains" (pressure or
  voltage) shared by the connected terminals.
- **Headless API**: circuits can be built and simulated from a script
  without the GUI (perfect for tests and demos).
- **MIT licensed**, no proprietary dependencies.

## Requirements

- Python 3.9 or newer
- PyQt5 (only for the GUI; the headless API works without it)

## Installation

```bash
# (recommended) create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
```

## Usage

### Graphical interface

```bash
python -m opencade.main
```

The toolbars add components to the current circuit; simulation
start/stop/reset are available in the *Simulation* menu.

### Headless demo (no GUI required)

```python
from opencade.components import AirSupply, Cylinder, PowerSupply, Switch, Valve
from opencade.models import Circuit
from opencade.simulator import Simulator

circuit = Circuit()

# ------------------------------- pneumatic side
air = AirSupply(pressure=6.0e5)   # 6 bar
valve = Valve()
cyl = Cylinder(bore=0.05, stroke=0.10)

n_supply = circuit.add_node(domain="pneumatic")
n_p = circuit.add_node(domain="pneumatic")
n_a = circuit.add_node(domain="pneumatic")
n_b = circuit.add_node(domain="pneumatic")
n_cap = circuit.add_node(domain="pneumatic")
n_rod = circuit.add_node(domain="pneumatic")

air.connect_terminal("out", n_supply)
valve.connect_terminal("P", n_p)
valve.connect_terminal("A", n_a)
valve.connect_terminal("B", n_b)
cyl.connect_terminal("cap", n_cap)
cyl.connect_terminal("rod", n_rod)

circuit.add_wire(n_supply, n_p)
circuit.add_wire(n_a, n_cap)
# n_b and n_rod remain at atmospheric (exhaust / rod side unconnected).

# ------------------------------- electrical side
psu = PowerSupply(voltage=24.0)
sw = Switch()

n_plus = circuit.add_node(domain="electrical")
n_sw_in = circuit.add_node(domain="electrical")
n_sw_out = circuit.add_node(domain="electrical")
n_coil_in = circuit.add_node(domain="electrical")
n_coil_out = circuit.add_node(domain="electrical")

psu.connect_terminal("+", n_plus)
psu.connect_terminal("-", n_coil_out)
sw.connect_terminal("in", n_sw_in)
sw.connect_terminal("out", n_sw_out)
valve.connect_terminal("CI", n_coil_in)
valve.connect_terminal("CO", n_coil_out)

circuit.add_wire(n_plus, n_sw_in)
circuit.add_wire(n_sw_out, n_coil_in)
# n_coil_out is shared with the negative rail.

for component in (air, valve, cyl, psu, sw):
    circuit.add_component(component)

sw.set_closed(True)  # press the button

simulator = Simulator(circuit, time_step=0.01)
for _ in range(200):  # simulate 2 seconds
    simulator.step()

print(f"t = {simulator.time:.2f} s")
print(
    f"Cylinder position: {cyl.state['position']:.3f} m "
    f"(stroke {cyl.stroke:.3f} m)"
)
```

Expected output: the 24 V coil is energised through the closed switch,
the valve shifts to position 1, pressure is routed to the cylinder cap
and the rod extends to its full stroke:

```
t = 2.00 s
Cylinder position: 0.100 m (stroke 0.100 m)
```

## Project structure

```
opencade/
├── opencade/
│   ├── __init__.py              # package metadata
│   ├── main.py                  # entry point (python -m opencade.main)
│   ├── gui.py                   # PyQt5 main window
│   ├── simulator.py             # simulation engine (time loop + solvers)
│   ├── components/              # component library
│   │   ├── base.py              # Component base class (terminals, state)
│   │   ├── pneumatic.py         # AirSupply, Valve, Cylinder
│   │   ├── electrical.py        # PowerSupply, Switch, Relay, Motor, Sensor
│   │   └── logic.py             # AND/OR/NOT gates, Timer
│   ├── models/                  # circuit topology
│   │   ├── node.py              # Node (connection point)
│   │   ├── wire.py              # Wire (ideal conductor)
│   │   └── circuit.py           # Circuit (nodes, wires, components)
│   ├── solvers/                 # domain solvers
│   │   ├── pneumatic_solver.py
│   │   ├── electrical_solver.py
│   │   └── logic_solver.py
│   └── utils/                   # helpers
│       ├── config.py            # global configuration (dot access)
│       └── math_utils.py        # flow, pressure, Ohm's law formulas
├── requirements.txt
├── LICENSE
└── README.md
```

## How it works

Every step (default 10 ms) the simulation engine runs:

1. **Logic solver** - re-evaluates the gates and timers.
2. **Electrical solver** - groups the electrical nodes into domains,
   fixes the power rails, propagates the voltage through the closed
   contacts (switches, relay contacts) and energises the relay /
   solenoid coils that see a sufficient voltage drop.
3. **Pneumatic solver** - resets all pneumatic domains to atmospheric
   pressure, pressurises the supplied domains, routes the pressure
   through the valves according to their position and advances the
   cylinders.

Model simplifications (documented limits, intended for educational
control-circuit simulation rather than engineering analysis):

- ideal conductors: closed contacts propagate the voltage without drop;
- quasi-static pneumatic pressure: no chamber volumes, no compressible
  flow;
- relay contacts switch instantaneously;
- cylinder travel speed is constant (no dynamic friction model).

## Roadmap

- [ ] Graphic canvas (QGraphicsScene): grid, component icons, wire routing.
- [ ] Component editing (parameters, drag and drop).
- [ ] Circuit save/load (JSON).
- [ ] Real-time animation of cylinders, valves and relays.
- [ ] Ladder-logic editor (PLC-style).
- [ ] Advanced fluid dynamics (chamber volumes, orifice flow).
- [ ] Automated test suite (pytest).

## License

This project is licensed under the [MIT License](LICENSE).

