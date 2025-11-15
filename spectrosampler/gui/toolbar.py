"""Toolbar widget for tool mode selection."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ToolbarWidget(QWidget):
    """Vertical toolbar widget with tool mode buttons."""

    def __init__(self, parent: QWidget | None = None):
        """Initialize toolbar widget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Load icons
        icon_size = 24
        assets_dir = Path(__file__).parent.parent.parent / "assets"

        def load_svg_icon(path: Path, size: int = icon_size) -> QIcon:
            """Load SVG icon preserving colors by rendering to pixmap."""
            if not path.exists():
                return QIcon()
            renderer = QSvgRenderer(str(path))
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)

        select_icon = load_svg_icon(assets_dir / "pointer.svg")
        edit_icon = load_svg_icon(assets_dir / "pencil.svg")
        create_icon = load_svg_icon(assets_dir / "add.svg")

        # Create tool mode group box
        tool_group = QGroupBox("Tool")
        tool_layout = QVBoxLayout()
        tool_layout.setContentsMargins(8, 8, 8, 8)
        tool_layout.setSpacing(8)

        # Create button group for mutually exclusive selection
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        # Create mode buttons (non-functional placeholders for now)
        self._select_button = QPushButton()
        self._select_button.setCheckable(True)
        self._select_button.setChecked(True)  # Default to Select mode
        self._select_button.setIcon(select_icon)
        self._select_button.setIconSize(QSize(24, 24))
        self._select_button.setMinimumHeight(40)
        self._select_button.setMinimumWidth(40)  # Reduced to fit within toolbar
        self._select_button.setToolTip("Select")
        self._button_group.addButton(self._select_button, 0)

        self._edit_button = QPushButton()
        self._edit_button.setCheckable(True)
        self._edit_button.setIcon(edit_icon)
        self._edit_button.setIconSize(QSize(24, 24))
        self._edit_button.setMinimumHeight(40)
        self._edit_button.setMinimumWidth(40)  # Reduced to fit within toolbar
        self._edit_button.setToolTip("Edit")
        self._button_group.addButton(self._edit_button, 1)

        self._create_button = QPushButton()
        self._create_button.setCheckable(True)
        self._create_button.setIcon(create_icon)
        self._create_button.setIconSize(QSize(24, 24))
        self._create_button.setMinimumHeight(40)
        self._create_button.setMinimumWidth(40)  # Reduced to fit within toolbar
        self._create_button.setToolTip("Create")
        self._button_group.addButton(self._create_button, 2)

        # Add buttons to tool group layout
        tool_layout.addWidget(self._select_button)
        tool_layout.addWidget(self._edit_button)
        tool_layout.addWidget(self._create_button)

        tool_group.setLayout(tool_layout)

        # Add tool group to main layout
        layout.addWidget(tool_group)

        layout.addStretch()

        self.setLayout(layout)

        # Set minimum width for toolbar (~75px total, half of original)
        self.setMinimumWidth(75)
