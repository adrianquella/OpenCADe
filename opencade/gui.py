"""Main window of the opencade desktop application.

The window provides the classic CADe SIMU layout: menus, toolbars to
insert components, a status bar and a central canvas where the circuit
is drawn and simulated.

Note: the canvas is still a placeholder in this first release; circuits
can already be built and simulated programmatically (see the "Headless
demo" section of the README).
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
)

from .components import (
    AirSupply,
    Cylinder,
    Motor,
    PowerSupply,
    Relay,
    Sensor,
    Switch,
    Valve,
)
from .models.circuit import Circuit
from .simulator import Simulator


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("opencade - Electro-pneumatic simulator")
        self.resize(1200, 800)

        # Application core. It is decoupled from the GUI so that it can
        # also be driven headlessly from scripts or tests.
        self.circuit = Circuit()
        self.simulator = Simulator(self.circuit)

        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_canvas()

    # ------------------------------------------------------------------ UI
    def _create_menu_bar(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction(QAction("New circuit", self, triggered=self.new_circuit))
        file_menu.addAction(QAction("Open...", self, triggered=self.open_circuit))
        file_menu.addAction(QAction("Save", self, triggered=self.save_circuit))
        file_menu.addSeparator()
        file_menu.addAction(QAction("Exit", self, triggered=self.close))

        simulation_menu = menubar.addMenu("Simula&tion")
        simulation_menu.addAction(
            QAction("Start", self, triggered=self.start_simulation)
        )
        simulation_menu.addAction(
            QAction("Stop", self, triggered=self.stop_simulation)
        )
        simulation_menu.addAction(
            QAction("Reset", self, triggered=self.reset_simulation)
        )

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(
            QAction("About opencade", self, triggered=self.show_about)
        )

    def _create_tool_bar(self) -> None:
        pneumatic_bar = QToolBar("Pneumatic", self)
        pneumatic_bar.setMovable(False)
        pneumatic_bar.addAction("Air supply", self._add_air_supply)
        pneumatic_bar.addAction("5/2 valve", self._add_valve)
        pneumatic_bar.addAction("Cylinder", self._add_cylinder)

        electrical_bar = QToolBar("Electrical", self)
        electrical_bar.setMovable(False)
        electrical_bar.addAction("Power supply", self._add_power_supply)
        electrical_bar.addAction("Switch", self._add_switch)
        electrical_bar.addAction("Relay", self._add_relay)
        electrical_bar.addAction("Motor", self._add_motor)
        electrical_bar.addAction("Sensor", self._add_sensor)

        self.addToolBar(Qt.LeftToolBarArea, pneumatic_bar)
        self.addToolBar(Qt.LeftToolBarArea, electrical_bar)

    def _create_status_bar(self) -> None:
        self.statusBar().showMessage("Ready")

    def _create_canvas(self) -> None:
        """Create the circuit drawing area.

        The full graphics widget (a QGraphicsScene with grid, component
        icons and wire routing) will replace this placeholder in a
        future release.
        """
        self.canvas = QLabel("opencade canvas - coming soon", self)
        self.canvas.setAlignment(Qt.AlignCenter)
        self.canvas.setMinimumSize(640, 480)
        self.canvas.setStyleSheet(
            "background-color: #1e1e2e; color: #cdd6f4; font-size: 16px;"
        )
        self.setCentralWidget(self.canvas)

    # ------------------------------------------------------------ components
    def _add_air_supply(self) -> None:
        self.circuit.add_component(AirSupply())
        self._component_added("Air supply")

    def _add_valve(self) -> None:
        self.circuit.add_component(Valve())
        self._component_added("5/2 valve")

    def _add_cylinder(self) -> None:
        self.circuit.add_component(Cylinder())
        self._component_added("Cylinder")

    def _add_power_supply(self) -> None:
        self.circuit.add_component(PowerSupply())
        self._component_added("Power supply")

    def _add_switch(self) -> None:
        self.circuit.add_component(Switch())
        self._component_added("Switch")

    def _add_relay(self) -> None:
        self.circuit.add_component(Relay())
        self._component_added("Relay")

    def _add_motor(self) -> None:
        self.circuit.add_component(Motor())
        self._component_added("Motor")

    def _add_sensor(self) -> None:
        self.circuit.add_component(Sensor())
        self._component_added("Sensor")

    def _component_added(self, label: str) -> None:
        self.statusBar().showMessage(f"{label} added to the circuit")

    # ------------------------------------------------------------ simulation
    def new_circuit(self) -> None:
        """Discard the current circuit and start from scratch."""
        reply = QMessageBox.question(
            self,
            "New circuit",
            "Discard the current circuit and start over?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.simulator.stop()
            self.circuit = Circuit()
            self.simulator = Simulator(self.circuit)
            self.statusBar().showMessage("New empty circuit")

    def open_circuit(self) -> None:
        self.statusBar().showMessage("Opening circuits is not implemented yet")

    def save_circuit(self) -> None:
        self.statusBar().showMessage("Saving circuits is not implemented yet")

    def start_simulation(self) -> None:
        self.simulator.start()
        self.statusBar().showMessage("Simulation running")

    def stop_simulation(self) -> None:
        self.simulator.stop()
        self.statusBar().showMessage("Simulation stopped")

    def reset_simulation(self) -> None:
        self.simulator.reset()
        self.statusBar().showMessage("Simulation reset")

    def show_about(self) -> None:
        from . import __version__

        QMessageBox.about(
            self,
            "About opencade",
            (
                "<h3>opencade %s</h3>"
                "A free and open-source electro-pneumatic and industrial "
                "automation simulator, inspired by CADe SIMU.<br>"
                "Licensed under the MIT License." % __version__
            ),
        )

