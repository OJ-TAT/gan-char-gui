import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from qfluentwidgets import (CardWidget, StrongBodyLabel, DoubleSpinBox,
                             SwitchButton, InfoBar, InfoBarPosition,
                             MessageBox, BodyLabel)

from gui.components.plot_card import PlotCard, FLUENT_COLORS
from gui.test_interfaces.base_test_interface import BaseTestInterface


class BreakdownInterface(BaseTestInterface):
    """Breakdown Test page."""

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
        sweep_layout.addWidget(StrongBodyLabel('Breakdown Sweep'))

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.vds_start = DoubleSpinBox()
        self.vds_start.setRange(0, 5000)
        self.vds_start.setValue(0)
        self.vds_start.setSuffix(' V')

        self.vds_stop = DoubleSpinBox()
        self.vds_stop.setRange(0, 5000)
        self.vds_stop.setValue(1200)
        self.vds_stop.setSuffix(' V')

        self.vds_step = DoubleSpinBox()
        self.vds_step.setRange(0.1, 100)
        self.vds_step.setValue(5)
        self.vds_step.setSuffix(' V')

        self.vgs_off = DoubleSpinBox()
        self.vgs_off.setRange(-100, 0)
        self.vgs_off.setValue(-8)
        self.vgs_off.setSuffix(' V')

        self.bv_threshold = DoubleSpinBox()
        self.bv_threshold.setRange(1e-9, 1)
        self.bv_threshold.setValue(1e-3)
        self.bv_threshold.setDecimals(6)
        self.bv_threshold.setSuffix(' A')

        form.addRow('Vds Start:', self.vds_start)
        form.addRow('Vds Stop:', self.vds_stop)
        form.addRow('Vds Step:', self.vds_step)
        form.addRow('Vgs Off:', self.vgs_off)
        form.addRow('BV Threshold:', self.bv_threshold)

        self.auto_stop_row = QHBoxLayout()
        self.auto_stop_label = BodyLabel('Auto-Stop:')
        self.auto_stop_switch = SwitchButton()
        self.auto_stop_switch.setChecked(True)
        self.auto_stop_row.addWidget(self.auto_stop_label)
        self.auto_stop_row.addStretch()
        self.auto_stop_row.addWidget(self.auto_stop_switch)

        sweep_layout.addLayout(form)
        sweep_layout.addLayout(self.auto_stop_row)
        layout.addWidget(sweep_card)

        meas_card = CardWidget()
        meas_layout = QVBoxLayout(meas_card)
        meas_layout.setContentsMargins(12, 10, 12, 10)
        meas_layout.addWidget(StrongBodyLabel('Measurement'))

        form2 = QFormLayout()
        form2.setSpacing(8)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.compliance = DoubleSpinBox()
        self.compliance.setRange(1e-12, 1)
        self.compliance.setValue(1e-3)
        self.compliance.setDecimals(6)
        self.compliance.setSuffix(' A')

        self.nplc = DoubleSpinBox()
        self.nplc.setRange(0.001, 25)
        self.nplc.setValue(1)

        form2.addRow('Compliance:', self.compliance)
        form2.addRow('NPLC:', self.nplc)
        meas_layout.addLayout(form2)
        layout.addWidget(meas_card)

        layout.addStretch()
        return panel

    def _chart_view_buttons(self):
        return [
            ('log|Id|', lambda: self._switch_view('log|Id|')),
            ('Id-Vds',  lambda: self._switch_view('Id-Vds')),
        ]

    def _build_plot_card(self) -> PlotCard:
        self._plot = PlotCard('Vds (V)', 'log|Id| (A)', parent=self)
        return self._plot

    def _setup_metrics(self, layout):
        w1, self._lbl_bv = self._make_metric('BV', 'V')
        layout.addWidget(w1)
        layout.addStretch()

    def _switch_view(self, view: str):
        for btn in self._view_buttons:
            btn.setChecked(btn.text() == view)
        if not self._sweep_data:
            return
        vds = self._sweep_data.get('vds', np.array([]))
        id_arr = self._sweep_data.get('id', np.array([]))
        self._plot.clear_curves()
        if view == 'log|Id|':
            self._plot.set_log_y(True)
            self._plot.set_labels('Vds (V)', 'log|Id| (A)')
            self._plot.add_curve(vds, np.abs(id_arr) + 1e-12,
                                 name='Id', color=FLUENT_COLORS[0])
        elif view == 'Id-Vds':
            self._plot.set_log_y(False)
            self._plot.set_labels('Vds (V)', 'Id (A)')
            self._plot.add_curve(vds, id_arr, name='Id', color=FLUENT_COLORS[0])

    def _on_start(self):
        vds_stop = self.vds_stop.value()
        if vds_stop > 200:
            dlg = MessageBox(
                '⚠️  High Voltage Warning',
                f'Vds Stop is set to {vds_stop:.0f} V.\n'
                'Please ensure proper safety measures are in place.\n'
                'Do you want to proceed?',
                self,
            )
            if not dlg.exec():
                return

        vds_start = self.vds_start.value()
        vds_step = self.vds_step.value()
        vds_arr = np.arange(vds_start, vds_stop + vds_step, vds_step)
        id_arr = self._simulate_breakdown(vds_arr)

        self._sweep_data = {'vds': vds_arr, 'id': id_arr}
        self._tick_idx = 0
        self._total_ticks = len(vds_arr)

        self.control_bar.set_running(True)
        self.control_bar.set_status('Sweeping...')
        self.control_bar.set_progress(0)
        self._plot.clear_curves()
        self._plot.set_log_y(True)
        self._plot.set_labels('Vds (V)', 'log|Id| (A)')

        self._anim_curve = self._plot.add_curve([], [], name='Id',
                                                 color=FLUENT_COLORS[0])
        self._timer.start(20)

    def _on_tick(self):
        idx = self._tick_idx
        n = self._total_ticks
        vds = self._sweep_data['vds']
        id_arr = self._sweep_data['id']
        threshold = self.compliance.value()

        if idx >= n:
            self._timer.stop()
            self._finish_sweep()
            return

        self._tick_idx += 2
        end = min(self._tick_idx, n)

        # Auto-stop at breakdown
        if self.auto_stop_switch.isChecked():
            breakdown_mask = np.abs(id_arr[:end]) >= threshold
            if np.any(breakdown_mask):
                bv_idx = np.argmax(breakdown_mask)
                end = min(bv_idx + 5, n)
                self._anim_curve.setData(vds[:end], np.abs(id_arr[:end]) + 1e-12)
                self.control_bar.set_progress(100)
                self._tick_idx = n
                self._timer.stop()
                self._finish_sweep(bv=vds[bv_idx])
                return

        self._anim_curve.setData(vds[:end], np.abs(id_arr[:end]) + 1e-12)
        self.control_bar.set_progress(int(end / n * 100))
        self.control_bar.set_status(f'Vds = {vds[min(end-1, n-1)]:.0f} V')

    def _finish_sweep(self, bv: float | None = None):
        self.control_bar.set_running(False)
        self.control_bar.set_progress(100)

        if bv is not None:
            self._lbl_bv.setText(f'{bv:.0f} V')
            self.control_bar.set_status(f'BV ≈ {bv:.0f} V')
            InfoBar.warning(
                title='Breakdown Detected',
                content=f'Breakdown voltage ≈ {bv:.0f} V',
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self,
            )
        else:
            self.control_bar.set_status('Complete (no breakdown)')
            InfoBar.success(
                title='Measurement Complete',
                content='Breakdown sweep finished without breakdown.',
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
    def _simulate_breakdown(vds: np.ndarray) -> np.ndarray:
        bv = np.random.uniform(800, 1100)
        # Leakage floor
        id_arr = 1e-9 * np.exp(vds / 600)
        # Avalanche near BV
        id_arr += 1e-9 * np.exp(np.clip((vds - bv * 0.95) / 10, -100, 80))
        id_arr += np.abs(np.random.normal(0, 1e-10, len(vds)))
        return id_arr
