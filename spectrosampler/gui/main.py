"""Main entry point for SpectroSampler GUI."""

import logging
import sys

from spectrosampler.utils import setup_logging

logger = logging.getLogger(__name__)


def _print_help() -> None:
    print(
        "SpectroSampler GUI\n\n"
        "Usage:\n"
        "  spectrosampler-gui               Launch the GUI\n"
        "  spectrosampler-gui --help        Show this help and exit\n"
        "  spectrosampler-gui --version     Show version and exit\n"
    )


def main() -> None:
    """Main entry point for GUI application."""
    # Setup logging
    setup_logging(verbose=True)

    # Fast-path for CI/CLI flags before importing Qt (avoids EGL/X11 deps for --help/--version)
    if any(arg in ("-h", "--help") for arg in sys.argv[1:]):
        _print_help()
        return
    if any(arg in ("-v", "--version") for arg in sys.argv[1:]):
        print("SpectroSampler 0.1.0")
        return

    # Import Qt and window lazily to avoid loading GUI stack when not needed
    from PySide6.QtWidgets import QApplication

    from spectrosampler.gui.main_window import MainWindow

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("SpectroSampler")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("SpectroSampler")

    # Create main window
    window = MainWindow()
    window.setWindowTitle("SpectroSampler")
    window.resize(1400, 900)
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
