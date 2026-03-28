from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
from qfluentwidgets import CardWidget, StrongBodyLabel
import pyqtgraph as pg
import numpy as np

FLUENT_COLORS = ['#60cdff', '#f7630c', '#00b7c3', '#8764b8', '#f3b93a', '#e74856']

PLOT_BG_COLOR = '#1e1e2e'
AXIS_PEN = pg.mkPen(color='#cdd6f4', width=1)
GRID_ALPHA = 30  # out of 255


def _hex_to_rgba(hex_color: str, alpha: int = 255):
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (r, g, b, alpha)


class PlotCard(CardWidget):
    """Reusable PyQtGraph chart card with Fluent Dark styling."""

    def __init__(self, x_label: str = 'X', y_label: str = 'Y',
                 title: str = '', parent=None):
        super().__init__(parent)
        self._color_idx = 0
        self._curves: list[pg.PlotDataItem] = []
        self._log_mode = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        if title:
            lbl = StrongBodyLabel(title, self)
            layout.addWidget(lbl)

        self.plot_widget = pg.PlotWidget(background=PLOT_BG_COLOR)
        self._configure_plot(x_label, y_label)
        layout.addWidget(self.plot_widget)

        self._add_crosshair()

    def _configure_plot(self, x_label: str, y_label: str):
        pw = self.plot_widget
        pw.setBackground(PLOT_BG_COLOR)

        pw.showGrid(x=True, y=True, alpha=GRID_ALPHA / 255)

        bottom = pw.getAxis('bottom')
        left = pw.getAxis('left')
        for ax in (bottom, left):
            ax.setPen(AXIS_PEN)
            ax.setTextPen(pg.mkPen(color='#cdd6f4'))

        bottom.setLabel(x_label, color='#cdd6f4')
        left.setLabel(y_label, color='#cdd6f4')

        pw.getPlotItem().setContentsMargins(5, 5, 5, 5)

    def _add_crosshair(self):
        pw = self.plot_widget
        self._v_line = pg.InfiniteLine(angle=90, movable=False,
                                       pen=pg.mkPen(color='#6c7086', width=1, style=Qt.PenStyle.DashLine))
        self._h_line = pg.InfiniteLine(angle=0, movable=False,
                                       pen=pg.mkPen(color='#6c7086', width=1, style=Qt.PenStyle.DashLine))
        pw.addItem(self._v_line, ignoreBounds=True)
        pw.addItem(self._h_line, ignoreBounds=True)

        self._proxy = pg.SignalProxy(pw.scene().sigMouseMoved, rateLimit=60,
                                     slot=self._on_mouse_moved)

    def _on_mouse_moved(self, evt):
        pos = evt[0]
        pw = self.plot_widget
        if pw.sceneBoundingRect().contains(pos):
            mouse_point = pw.getPlotItem().vb.mapSceneToView(pos)
            self._v_line.setPos(mouse_point.x())
            self._h_line.setPos(mouse_point.y())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_curve(self, x, y, name: str = '', color: str | None = None,
                  width: int = 2, symbol=None) -> pg.PlotDataItem:
        if color is None:
            color = FLUENT_COLORS[self._color_idx % len(FLUENT_COLORS)]
            self._color_idx += 1
        pen = pg.mkPen(color=color, width=width)
        curve = self.plot_widget.plot(x, y, pen=pen, name=name, symbol=symbol,
                                      symbolSize=4, symbolPen=None,
                                      symbolBrush=pg.mkBrush(color))
        self._curves.append(curve)
        return curve

    def clear_curves(self):
        for c in self._curves:
            self.plot_widget.removeItem(c)
        self._curves.clear()
        self._color_idx = 0

    def set_log_y(self, enabled: bool):
        self._log_mode = enabled
        self.plot_widget.getPlotItem().setLogMode(y=enabled)

    def set_labels(self, x_label: str = '', y_label: str = ''):
        if x_label:
            self.plot_widget.getAxis('bottom').setLabel(x_label, color='#cdd6f4')
        if y_label:
            self.plot_widget.getAxis('left').setLabel(y_label, color='#cdd6f4')

    def set_title(self, title: str):
        self.plot_widget.setTitle(title, color='#cdd6f4')
