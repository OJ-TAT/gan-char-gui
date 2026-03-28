from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPalette, QColor
from qfluentwidgets import (PrimaryPushButton, PushButton, ProgressBar,
                             CaptionLabel)


class ControlBar(QWidget):
    """Start / Stop / Emergency Stop control bar with progress and status label."""

    start_clicked = Signal()
    stop_clicked = Signal()
    emergency_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # --- Button row ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.start_btn = PrimaryPushButton('▶  Start', self)
        self.stop_btn = PushButton('⏹  Stop', self)
        self.stop_btn.setEnabled(False)

        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

        # --- Emergency Stop ---
        self.emergency_btn = PushButton('🔴  EMERGENCY STOP', self)
        self.emergency_btn.setFixedHeight(40)
        self.emergency_btn.setStyleSheet(
            'QPushButton {'
            '  background-color: #c42b1c;'
            '  color: white;'
            '  font-weight: bold;'
            '  border-radius: 6px;'
            '  font-size: 13px;'
            '}'
            'QPushButton:hover {'
            '  background-color: #e74856;'
            '}'
            'QPushButton:pressed {'
            '  background-color: #a12013;'
            '}'
        )
        layout.addWidget(self.emergency_btn)

        # --- Progress bar ---
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # --- Status label ---
        self.status_label = CaptionLabel('Idle', self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.status_label)

        # Connections
        self.start_btn.clicked.connect(self.start_clicked)
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.emergency_btn.clicked.connect(self.emergency_clicked)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def set_running(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def set_progress(self, value: int):
        self.progress_bar.setValue(value)

    def set_status(self, text: str):
        self.status_label.setText(text)

    def reset(self):
        self.set_running(False)
        self.set_progress(0)
        self.set_status('Idle')
