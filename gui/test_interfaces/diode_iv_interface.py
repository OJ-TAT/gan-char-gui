import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout
from PySide6.QtCore import QTimer, Qt
from qfluentwidgets import (CardWidget, StrongBodyLabel, DoubleSpinBox,
                             ComboBox, InfoBar, InfoBarPosition)

from gui.components.plot_card import PlotCard, FLUENT_COLORS
from gui.test_interfaces.base_test_interface import BaseTestInterface


class DiodeIVInterface(BaseTestInterface):
    """Diode I-V characterization page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_tick)
        self._sweep_data = {}
        self._tick_idx = 0

        self.control_bar.start_clicked.connect(self._on_start)
        self.control_bar.stop_clicked.connect(self._on_stop)
        self.control_bar.emergency_clicked.connect(self._on_stop)

    def _build_param_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        sweep_card = CardWidget()
        sweep_layout = QVBoxLayout(sweep_card)
        sweep_layout.setContentsMargins(12, 10, 12, 10)
        sweep_layout.addWidget(StrongBodyLabel('Sweep Parameters'))

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.v_start = DoubleSpinBox()
        self.v_start.setRange(-100, 100)
        self.v_start.setValue(-5)
        self.v_start.setSuffix(' V')

        self.v_stop = DoubleSpinBox()
        self.v_stop.setRange(-100, 100)
        self.v_stop.setValue(3)
        self.v_stop.setSuffix(' V')

        self.v_step = DoubleSpinBox()
        self.v_step.setRange(0.001, 10)
        self.v_step.setValue(0.05)
        self.v_step.setSuffix(' V')

        self.compliance = DoubleSpinBox()
        self.compliance.setRange(1e-9, 10)
        self.compliance.setValue(0.1)
        self.compliance.setSuffix(' A')
        self.compliance.setDecimals(3)

        self.diode_config = ComboBox()
        self.diode_config.addItems(['Gate-Source', 'Gate-Drain', 'Drain-Source'])

        form.addRow('V Start:', self.v_start)
        form.addRow('V Stop:', self.v_stop)
        form.addRow('V Step:', self.v_step)
        form.addRow('Compliance:', self.compliance)
        form.addRow('Diode Config:', self.diode_config)

        sweep_layout.addLayout(form)
        layout.addWidget(sweep_card)

        meas_card = CardWidget()
        meas_layout = QVBoxLayout(meas_card)
        meas_layout.setContentsMargins(12, 10, 12, 10)
        meas_layout.addWidget(StrongBodyLabel('Measurement'))

        form2 = QFormLayout()
        form2.setSpacing(8)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.nplc = DoubleSpinBox()
        self.nplc.setRange(0.001, 25)
        self.nplc.setValue(1)

        self.delay = DoubleSpinBox()
        self.delay.setRange(0, 10)
        self.delay.setValue(0.01)
        self.delay.setSuffix(' s')
        self.delay.setDecimals(4)

        form2.addRow('NPLC:', self.nplc)
        form2.addRow('Delay:', self.delay)
        meas_layout.addLayout(form2)
        layout.addWidget(meas_card)

        layout.addStretch()
        return panel

    def _chart_view_buttons(self):
        return [
            ('I-V',       lambda: self._switch_view('I-V')),
            ('log|I|-V',  lambda: self._switch_view('log|I|-V')),
        ]

    def _build_plot_card(self) -> PlotCard:
        self._plot = PlotCard('V (V)', 'I (A)', parent=self)
        return self._plot

    def _setup_metrics(self, layout):
        w1, self._lbl_von = self._make_metric('Von', 'V')
        w2, self._lbl_irev = self._make_metric('Irev', 'A')
        for w in (w1, w2):
            layout.addWidget(w)
        layout.addStretch()

    def _switch_view(self, view: str):
        for btn in self._view_buttons:
            btn.setChecked(btn.text() == view)
        if not self._sweep_data:
            return
        v = self._sweep_data.get('v', np.array([]))
        i = self._sweep_data.get('i', np.array([]))
        self._plot.clear_curves()
        if view == 'I-V':
            self._plot.set_log_y(False)
            self._plot.set_labels('V (V)', 'I (A)')
            self._plot.add_curve(v, i, name='I', color=FLUENT_COLORS[0])
        elif view == 'log|I|-V':
            self._plot.set_log_y(True)
            self._plot.set_labels('V (V)', 'log|I| (A)')
            self._plot.add_curve(v, np.abs(i) + 1e-12, name='|I|',
                                 color=FLUENT_COLORS[0])

    def _on_start(self):
        v_start = self.v_start.value()
        v_stop = self.v_stop.value()
        v_step = self.v_step.value()
        config = self.diode_config.currentText()

        v_arr = np.arange(v_start, v_stop + v_step, v_step)
        i_arr = self._simulate_diode_iv(v_arr, config)

        self._sweep_data = {'v': v_arr, 'i': i_arr}
        self._tick_idx = 0
        self._total_ticks = len(v_arr)

        self.control_bar.set_running(True)
        self.control_bar.set_status('Sweeping...')
        self.control_bar.set_progress(0)
        self._plot.clear_curves()
        self._plot.set_log_y(False)
        self._plot.set_labels('V (V)', 'I (A)')

        self._anim_curve = self._plot.add_curve([], [], name='I',
                                                 color=FLUENT_COLORS[0])
        self._timer.start(20)

    def _on_tick(self):
        n = self._total_ticks
        v = self._sweep_data['v']
        i_arr = self._sweep_data['i']

        if self._tick_idx >= n:
            self._timer.stop()
            self._finish_sweep()
            return

        self._tick_idx += 3
        end = min(self._tick_idx, n)
        self._anim_curve.setData(v[:end], i_arr[:end])
        self.control_bar.set_progress(int(end / n * 100))
        self.control_bar.set_status(f'V = {v[min(end-1, n-1)]:.2f} V')

    def _finish_sweep(self):
        self.control_bar.set_running(False)
        self.control_bar.set_progress(100)
        self.control_bar.set_status('Complete')
        self._update_metrics()
        InfoBar.success(
            title='Measurement Complete',
            content='Diode IV sweep finished.',
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self,
        )

    def _on_stop(self):
        self._timer.stop()
        self.control_bar.set_running(False)
        self.control_bar.set_status('Stopped')

    @staticmethod
    def _simulate_diode_iv(v: np.ndarray, config: str) -> np.ndarray:
        is_ = 1e-14
        n = 1.4 if 'Gate' in config else 1.1
        vt = 0.026
        i_arr = is_ * (np.exp(np.clip(v / (n * vt), -100, 40)) - 1)
        i_arr += np.random.normal(0, 1e-12, len(v))
        return i_arr

    def _update_metrics(self):
        v = self._sweep_data.get('v', np.array([]))
        i = self._sweep_data.get('i', np.array([]))
        if len(v) == 0:
            return

        # Von: V where I > 1mA
        on_mask = i > 1e-3
        von = v[on_mask][0] if np.any(on_mask) else float('nan')

        # Irev: mean of I where V < -1V
        rev_mask = v < -1
        irev = np.mean(np.abs(i[rev_mask])) if np.any(rev_mask) else float('nan')

        self._lbl_von.setText(f'{von:.2f} V' if not np.isnan(von) else '—')
        self._lbl_irev.setText(f'{irev:.2e} A' if not np.isnan(irev) else '—')
