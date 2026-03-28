from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QSplitter, QScrollArea, QFrame)
from PySide6.QtCore import Qt
from qfluentwidgets import (CardWidget, SubtitleLabel, BodyLabel,
                             ComboBox, PushButton, StrongBodyLabel,
                             PillPushButton, FluentIcon, ToolButton)

from gui.components.plot_card import PlotCard
from gui.components.control_bar import ControlBar


class BaseTestInterface(QWidget):
    """Base class for all four test pages.

    Subclasses must implement:
    - _build_param_panel()  → returns QWidget placed in left panel
    - _chart_view_buttons() → returns list of (label, callback) tuples
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.setHandleWidth(6)

        # ---- Left panel ----
        left_widget = QWidget()
        left_widget.setFixedWidth(360)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(12)

        # Param panel (filled by subclass)
        self.param_panel = self._build_param_panel()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.param_panel)
        left_layout.addWidget(scroll, 1)

        # Preset row
        preset_card = CardWidget()
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(12, 10, 12, 10)
        preset_layout.setSpacing(6)
        preset_layout.addWidget(StrongBodyLabel('Presets'))
        preset_row = QHBoxLayout()
        self.preset_combo = ComboBox()
        self.preset_combo.addItems(['Default', 'Fast Sweep', 'High Accuracy'])
        self.save_preset_btn = PushButton('Save')
        self.load_preset_btn = PushButton('Load')
        preset_row.addWidget(self.preset_combo, 1)
        preset_row.addWidget(self.save_preset_btn)
        preset_row.addWidget(self.load_preset_btn)
        preset_layout.addLayout(preset_row)
        left_layout.addWidget(preset_card)

        # Control bar
        ctrl_card = CardWidget()
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(12, 10, 12, 10)
        self.control_bar = ControlBar()
        ctrl_layout.addWidget(self.control_bar)
        left_layout.addWidget(ctrl_card)

        splitter.addWidget(left_widget)

        # ---- Right panel ----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)

        # View toggle buttons
        view_btns = self._chart_view_buttons()
        if view_btns:
            btn_row = QHBoxLayout()
            btn_row.setSpacing(6)
            self._view_buttons = []
            for i, (label, callback) in enumerate(view_btns):
                btn = PillPushButton(label)
                btn.setCheckable(True)
                btn.clicked.connect(callback)
                if i == 0:
                    btn.setChecked(True)
                btn_row.addWidget(btn)
                self._view_buttons.append(btn)
            btn_row.addStretch()
            right_layout.addLayout(btn_row)

        # Plot card
        self.plot_card = self._build_plot_card()
        right_layout.addWidget(self.plot_card, 1)

        # Metrics row
        self.metrics_card = CardWidget()
        metrics_layout = QHBoxLayout(self.metrics_card)
        metrics_layout.setContentsMargins(16, 10, 16, 10)
        metrics_layout.setSpacing(30)
        self._setup_metrics(metrics_layout)
        right_layout.addWidget(self.metrics_card)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)

    # ------------------------------------------------------------------
    # Subclass hooks
    # ------------------------------------------------------------------

    def _build_param_panel(self) -> QWidget:
        """Override in subclass to return a widget with parameters."""
        return QWidget()

    def _chart_view_buttons(self) -> list:
        """Override to return list of (label, callback) for chart toggle buttons."""
        return []

    def _build_plot_card(self) -> PlotCard:
        """Override to create a properly labelled PlotCard."""
        return PlotCard('X', 'Y')

    def _setup_metrics(self, layout: QHBoxLayout):
        """Override to add metric labels to the metrics row."""
        pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _make_metric(self, name: str, unit: str = '') -> tuple:
        """Return (container_widget, value_label) pair for a metric display."""
        container = QWidget()
        vl = QVBoxLayout(container)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(2)
        lbl_name = BodyLabel(f'{name}' + (f' [{unit}]' if unit else ''))
        lbl_val = StrongBodyLabel('—')
        vl.addWidget(lbl_name)
        vl.addWidget(lbl_val)
        return container, lbl_val
