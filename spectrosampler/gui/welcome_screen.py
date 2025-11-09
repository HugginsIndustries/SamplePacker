"""Welcome screen widget shown on application startup."""

import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from spectrosampler.gui.settings import SettingsManager
from spectrosampler.gui.theme import ThemeManager

logger = logging.getLogger(__name__)


class WelcomeScreen(QWidget):
    """Welcome screen widget with project options and recent files."""

    new_project_requested = Signal()  # Emitted when "Create New Project" clicked
    open_project_requested = Signal()  # Emitted when "Open Project" clicked
    recent_project_clicked = Signal(Path)  # Emitted when recent project item clicked
    recent_audio_file_clicked = Signal(Path)  # Emitted when recent audio file clicked

    def __init__(self, parent: QWidget | None = None):
        """Initialize welcome screen.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Settings manager
        self._settings_manager = SettingsManager()

        # Theme manager
        self._theme_manager = ThemeManager(self)
        pref = self._settings_manager.get_theme_preference()
        self._theme_manager.apply_theme(pref)
        self._theme_manager.theme_changed.connect(lambda _: self._apply_theme())

        # Setup UI
        self._setup_ui()

        # Apply theme
        self._apply_theme()

        # Load recent files
        self.update_recent_projects()
        self.update_recent_audio_files()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Title
        title = QLabel("SpectroSampler")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Turn long field recordings into curated sample packs with a fast, modern desktop workflow."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Action buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)

        # Create New Project button
        self._new_project_btn = QPushButton("Create New Project")
        self._new_project_btn.setMinimumHeight(50)
        self._new_project_btn.clicked.connect(self.new_project_requested.emit)
        buttons_layout.addWidget(self._new_project_btn)

        # Open Project button
        self._open_project_btn = QPushButton("Open Project...")
        self._open_project_btn.setMinimumHeight(50)
        self._open_project_btn.clicked.connect(self.open_project_requested.emit)
        buttons_layout.addWidget(self._open_project_btn)

        layout.addLayout(buttons_layout)
        layout.addSpacing(30)

        # Recent Projects section
        recent_projects_label = QLabel("Recent Projects")
        recent_projects_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(recent_projects_label)

        self._recent_projects_list = QListWidget()
        self._recent_projects_list.setMaximumHeight(200)
        self._recent_projects_list.itemDoubleClicked.connect(self._on_recent_project_double_clicked)
        layout.addWidget(self._recent_projects_list)

        # Clear recent projects button
        clear_recent_projects_btn = QPushButton("Clear Recent Projects")
        clear_recent_projects_btn.clicked.connect(self._on_clear_recent_projects)
        layout.addWidget(clear_recent_projects_btn)

        layout.addSpacing(20)

        # Recent Audio Files section
        recent_audio_label = QLabel("Recent Audio Files")
        recent_audio_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(recent_audio_label)

        self._recent_audio_list = QListWidget()
        self._recent_audio_list.setMaximumHeight(200)
        self._recent_audio_list.itemDoubleClicked.connect(self._on_recent_audio_double_clicked)
        layout.addWidget(self._recent_audio_list)

        # Clear recent audio files button
        clear_recent_audio_btn = QPushButton("Clear Recent Audio Files")
        clear_recent_audio_btn.clicked.connect(self._on_clear_recent_audio)
        layout.addWidget(clear_recent_audio_btn)

        layout.addStretch()

        self.setLayout(layout)

    def _apply_theme(self) -> None:
        """Apply theme to welcome screen."""
        stylesheet = self._theme_manager.get_stylesheet()

        # Add welcome screen specific styles
        palette = self._theme_manager.palette
        bg = palette["background"].name()
        bg_secondary = palette["background_secondary"].name()
        text = palette["text"].name()
        text_secondary = palette["text_secondary"].name()
        border = palette["border"].name()
        accent = palette["accent"].name()
        accent_hover = palette["accent_hover"].name()
        selection = palette["selection"].name()

        welcome_styles = f"""
            WelcomeScreen {{
                background-color: {bg};
            }}
            WelcomeScreen QLabel {{
                color: {text};
            }}
            WelcomeScreen QLabel#subtitleLabel {{
                color: {text_secondary};
            }}
            WelcomeScreen QPushButton {{
                background-color: {bg_secondary};
                color: {text};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 12px;
            }}
            WelcomeScreen QPushButton:hover {{
                background-color: {accent_hover};
            }}
            WelcomeScreen QPushButton:pressed {{
                background-color: {accent};
                color: {palette['text_bright'].name()};
            }}
            WelcomeScreen QListWidget {{
                background-color: {bg_secondary};
                border: 1px solid {border};
                color: {text};
            }}
            WelcomeScreen QListWidget::item {{
                padding: 8px;
            }}
            WelcomeScreen QListWidget::item:selected {{
                background-color: {selection};
            }}
            WelcomeScreen QListWidget::item:hover {{
                background-color: {accent_hover};
            }}
        """

        self.setStyleSheet(stylesheet + welcome_styles)

    def _on_recent_project_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle recent project double-click.

        Args:
            item: List widget item that was clicked.
        """
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and isinstance(path, Path):
            self.recent_project_clicked.emit(path)

    def _on_recent_audio_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle recent audio file double-click.

        Args:
            item: List widget item that was clicked.
        """
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and isinstance(path, Path):
            self.recent_audio_file_clicked.emit(path)

    def _on_clear_recent_projects(self) -> None:
        """Handle clear recent projects button click."""
        self._settings_manager.clear_recent_projects()
        self._update_recent_projects()

    def _on_clear_recent_audio(self) -> None:
        """Handle clear recent audio files button click."""
        self._settings_manager.clear_recent_audio_files()
        self._update_recent_audio_files()

    def update_recent_projects(self, projects: list[tuple[Path, datetime]] | None = None) -> None:
        """Update recent projects list.

        Args:
            projects: List of recent projects. If None, loads from settings.
        """
        if projects is None:
            max_count = self._settings_manager.get_max_recent_projects()
            projects = self._settings_manager.get_recent_projects(max_count=max_count)

        self._recent_projects_list.clear()

        if not projects:
            item = QListWidgetItem("No recent projects")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non-selectable
            self._recent_projects_list.addItem(item)
            return

        for path, timestamp in projects:
            # Format display text
            filename = path.stem
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")
            display_text = f"{filename} ({time_str})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(str(path))  # Show full path on hover
            self._recent_projects_list.addItem(item)

    def update_recent_audio_files(self, files: list[tuple[Path, datetime]] | None = None) -> None:
        """Update recent audio files list.

        Args:
            files: List of recent audio files. If None, loads from settings.
        """
        if files is None:
            max_count = self._settings_manager.get_max_recent_audio_files()
            files = self._settings_manager.get_recent_audio_files(max_count=max_count)

        self._recent_audio_list.clear()

        if not files:
            item = QListWidgetItem("No recent audio files")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non-selectable
            self._recent_audio_list.addItem(item)
            return

        for path, timestamp in files:
            # Format display text
            filename = path.name
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")
            display_text = f"{filename} ({time_str})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(str(path))  # Show full path on hover
            self._recent_audio_list.addItem(item)
