"""Command-line entry point for opencade.

Run the application with::

    python -m opencade.main
"""

import sys


def main() -> int:
    """Create the Qt application, show the main window and run the event loop."""
    from PyQt5.QtWidgets import QApplication

    from . import __version__
    from .gui import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("opencade")
    app.setApplicationVersion(__version__)

    window = MainWindow()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
