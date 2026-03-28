import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout
from PySide6.QtCore import QTimer, Qt
from qfluentwidgets import (CardWidget, StrongBodyLabel, DoubleSpinBox,
                             LineEdit, InfoBar, InfoBarPosition)

from gui.components.plot_card import PlotCard, FLUENT_COLORS
from gui.test_interfaces.base_test_interface import BaseTestInterface

import pyqtgraph as pg


class OutputInterface(BaseTestInterface):
    """Output Characteristics (Id-Vds) test page."""

    def __init__(self, parent=None):
        self._current_view = 'Id-Vds'
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
        sweep_layout.addWidget(StrongBodyLabel('Vds Sweep'))

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.vds_start = DoubleSpinBox()
        self.vds_start.setRange(0, 2000)
        self.vds_start.setValue(0)
        self.vds_start.setSuffix(' V')

        self.vds_stop = DoubleSpinBox()
        self.vds_stop.setRange(0, 2000)
        self.vds_stop.setValue(30)
        self.vds_stop.setSuffix(' V')

        self.vds_step = DoubleSpinBox()
        self.vds_step.setRange(0.001, 100)
        self.vds_step.setValue(0.5)
        self.vds_step.setSuffix(' V')

        self.vgs_list = LineEdit()
        self.vgs_list.setText('-2, 0, 1, 2')
        self.vgs_list.setPlaceholderText('e.g. -2, 0, 1, 2')

        form.addRow('Vds Start:', self.vds_start)
        form.addRow('Vds Stop:', self.vds_stop)
        form.addRow('Vds Step:', self.vds_step)
        form.addRow('Vgs List:', self.vgs_list)
        sweep_layout.addLayout(form)
        layout.addWidget(sweep_card)

        meas_card = CardWidget()
        meas_layout = QVBoxLayout(meas_card)
        meas_layout.setContentsMargins(12, 10, 12, 10)
        meas_layout.addWidget(StrongBodyLabel('Measurement'))

        form2 = QFormLayout()
        form2.setSpacing(8)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.drain_comp = DoubleSpinBox()
        self.drain_comp.setRange(1e-6, 10)
        self.drain_comp.setValue(1)
        self.drain_comp.setSuffix(' A')
        self.drain_comp.setDecimals(3)

        self.gate_comp = DoubleSpinBox()
        self.gate_comp.setRange(1e-9, 1)
        self.gate_comp.setValue(1e-3)
        self.gate_comp.setSuffix(' A')
        self.gate_comp.setDecimals(6)

        self.delay = DoubleSpinBox()
        self.delay.setRange(0, 10)
        self.delay.setValue(0.01)
        self.delay.setSuffix(' s')
        self.delay.setDecimals(4)

        self.nplc = DoubleSpinBox()
        self.nplc.setRange(0.001, 25)
        self.nplc.setValue(1)

        form2.addRow('Drain Compliance:', self.drain_comp)
        form2.addRow('Gate Compliance:', self.gate_comp)
        form2.addRow('Delay:', self.delay)
        form2.addRow('NPLC:', self.nplc)
        meas_layout.addLayout(form2)
        layout.addWidget(meas_card)

        layout.addStretch()
        return panel

    def _chart_view_buttons(self):
        return [
            ('Id-Vds', lambda: self._switch_view('Id-Vds')),
            ('Ron',    lambda: self._switch_view('Ron')),
        ]

    def _build_plot_card(self) -> PlotCard:
        self._plot = PlotCard('Vds (V)', 'Id (A)', parent=self)
        return self._plot

    def _setup_metrics(self, layout):
        w1, self._lbl_ron = self._make_metric('Ron', 'Ω')
        w2, self._lbl_id_max = self._make_metric('Id_max', 'A')
        for w in (w1, w2):
            layout.addWidget(w)
        layout.addStretch()

    # ------------------------------------------------------------------
    # View switching
    # ------------------------------------------------------------------

    def _switch_view(self, view: str):
        self._current_view = view
        for btn in self._view_buttons:
            btn.setChecked(btn.text() == view)

        if not self._sweep_data:
            return

        self._plot.clear_curves()
        vds_arr = self._sweep_data.get('vds', np.array([]))

        if view == 'Id-Vds':
            self._plot.set_log_y(False)
            self._plot.set_labels('Vds (V)', 'Id (A)')
            for i, (vgs, id_arr) in enumerate(self._sweep_data.get('id_curves', [])):
                self._plot.add_curve(vds_arr, id_arr, name=f'Vgs={vgs}V',
                                     color=FLUENT_COLORS[i % len(FLUENT_COLORS)])
        elif view == 'Ron':
            self._plot.set_log_y(False)
            self._plot.set_labels('Vgs (V)', 'Ron (Ω)')
            vgs_vals = []
            ron_vals = []
            # Use index 1 (first non-zero Vds point) for Ron calculation
            ron_idx = 1 if len(vds_arr) > 1 else 0
            for vgs, id_arr in self._sweep_data.get('id_curves', []):
                i_at_idx = id_arr[ron_idx] if len(id_arr) > ron_idx else 0
                ron = vds_arr[ron_idx] / (i_at_idx + 1e-12) if i_at_idx > 1e-9 else float('nan')
                vgs_vals.append(vgs)
                ron_vals.append(ron)
            self._plot.add_curve(np.array(vgs_vals), np.array(ron_vals),
                                 name='Ron', color=FLUENT_COLORS[0])

    # ------------------------------------------------------------------
    # Demo logic
    # ------------------------------------------------------------------

    def _on_start(self):
        vds_start = self.vds_start.value()
        vds_stop = self.vds_stop.value()
        vds_step = self.vds_step.value()

        try:
            vgs_values = [float(v.strip())
                          for v in self.vgs_list.text().split(',') if v.strip()]
        except ValueError:
            vgs_values = [0]

        vds_arr = np.arange(vds_start, vds_stop + vds_step, vds_step)
        id_curves = [(vgs, self._simulate_id_vds(vds_arr, vgs)) for vgs in vgs_values]

        self._sweep_data = {'vds': vds_arr, 'id_curves': id_curves}
        self._tick_idx = 0
        self._total_ticks = len(vds_arr)

        self.control_bar.set_running(True)
        self.control_bar.set_status('Sweeping...')
        self.control_bar.set_progress(0)
        self._plot.clear_curves()
        self._plot.set_log_y(False)
        self._plot.set_labels('Vds (V)', 'Id (A)')

        self._anim_curves = []
        for i, (vgs, _) in enumerate(id_curves):
            c = self._plot.add_curve([], [], name=f'Vgs={vgs}V',
                                     color=FLUENT_COLORS[i % len(FLUENT_COLORS)])
            self._anim_curves.append(c)

        self._timer.start(20)

    def _on_tick(self):
        idx = self._tick_idx
        n = self._total_ticks
        vds = self._sweep_data['vds']
        id_curves = self._sweep_data['id_curves']

        if idx >= n:
            self._timer.stop()
            self._finish_sweep()
            return

        self._tick_idx += 3
        end = min(self._tick_idx, n)

        for c, (_, id_arr) in zip(self._anim_curves, id_curves):
            c.setData(vds[:end], id_arr[:end])

        self.control_bar.set_progress(int(end / n * 100))
        self.control_bar.set_status(f'Vds = {vds[min(end-1, n-1)]:.2f} V')

    def _finish_sweep(self):
        self.control_bar.set_running(False)
        self.control_bar.set_progress(100)
        self.control_bar.set_status('Complete')
        self._update_metrics()
        InfoBar.success(
            title='Measurement Complete',
            content='Output Characteristics sweep finished.',
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self,
        )

    def _on_stop(self):
        self._timer.stop()
        self.control_bar.set_running(False)
        self.control_bar.set_status('Stopped')

    # ------------------------------------------------------------------

    @staticmethod
    def _simulate_id_vds(vds: np.ndarray, vgs: float) -> np.ndarray:
        vth = -3.5
        if vgs <= vth:
            return np.zeros_like(vds) + np.abs(np.random.normal(0, 1e-8, len(vds)))
        vov = vgs - vth
        mu_cox_w_l = 0.05
        vdsat = vov * 0.9
        id_arr = np.where(
            vds < vdsat,
            mu_cox_w_l * (vov * vds - 0.5 * vds ** 2) * (1 + 0.01 * vds),
            mu_cox_w_l * 0.5 * vov ** 2 * (1 + 0.01 * vds),
        )
        id_arr = np.clip(id_arr, 0, None)
        id_arr += np.abs(np.random.normal(0, 1e-6, len(vds)))
        return id_arr

    def _update_metrics(self):
        if not self._sweep_data:
            return
        id_curves = self._sweep_data.get('id_curves', [])
        vds = self._sweep_data.get('vds', np.array([]))
        if not id_curves or len(vds) == 0:
            return

        _, id_arr_max_vgs = id_curves[-1]
        id_max = np.max(id_arr_max_vgs)

        # Ron from first non-zero Vds point of highest on-state curve
        if len(vds) > 1 and len(id_arr_max_vgs) > 1 and id_arr_max_vgs[1] > 1e-6:
            ron = vds[1] / (id_arr_max_vgs[1] + 1e-12)
        else:
            ron = float('nan')

        self._lbl_id_max.setText(f'{id_max*1000:.1f} mA')
        self._lbl_ron.setText(f'{ron:.2f} Ω' if not np.isnan(ron) else '—')
