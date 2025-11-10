"""Application entry point for the Spectral Library desktop app."""

from __future__ import annotations

from .ui import MainWindow, create_application


def main() -> None:
    """Launch the PySide6 UI shell."""

    app = create_application()
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover - manual launch convenience
    main()
