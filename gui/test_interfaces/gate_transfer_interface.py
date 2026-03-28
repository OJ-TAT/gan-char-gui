import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout
from PySide6.QtCore import QTimer, Qt
from qfluentwidgets import (CardWidget, StrongBodyLabel, DoubleSpinBox,
                             LineEdit, SegmentedWidget, InfoBar,
                             InfoBarPosition)

from gui.components.plot_card import PlotCard, FLUENT_COLORS
from gui.test_interfaces.base_test_interface import BaseTestInterface

import pyqtgraph as pg


class GateTransferInterface(BaseTestInterface):
    """Gate Transfer (Id-Vgs) test page."""

    def __init__(self, parent=None):
        self._current_view = 'Id-Vgs'
        super().__init__(parent)
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_tick)
        self._sweep_data = {}
        self._tick_idx = 0

        self.control_bar.start_clicked.connect(self._on_start)
        self.control_bar.stop_clicked.connect(self._on_stop)
        self.control_bar.emergency_clicked.connect(self._on_stop)

    # ------------------------------------------------------------------
    # Param panel
    # ------------------------------------------------------------------

    def _build_param_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # ---- Sweep parameters ----
        sweep_card = CardWidget()
        sweep_layout = QVBoxLayout(sweep_card)
        sweep_layout.setContentsMargins(12, 10, 12, 10)
        sweep_layout.addWidget(StrongBodyLabel('Sweep Parameters'))

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.vgs_start = DoubleSpinBox()
        self.vgs_start.setRange(-100, 100)
        self.vgs_start.setValue(-10)
        self.vgs_start.setSuffix(' V')
        self.vgs_start.setSingleStep(0.5)

        self.vgs_stop = DoubleSpinBox()
        self.vgs_stop.setRange(-100, 100)
        self.vgs_stop.setValue(2)
        self.vgs_stop.setSuffix(' V')
        self.vgs_stop.setSingleStep(0.5)

        self.vgs_step = DoubleSpinBox()
        self.vgs_step.setRange(0.001, 10)
        self.vgs_step.setValue(0.1)
        self.vgs_step.setSuffix(' V')
        self.vgs_step.setSingleStep(0.05)

        self.vds_fixed = DoubleSpinBox()
        self.vds_fixed.setRange(0, 2000)
        self.vds_fixed.setValue(10)
        self.vds_fixed.setSuffix(' V')

        self.vds_list = LineEdit()
        self.vds_list.setText('1, 5, 10')
        self.vds_list.setPlaceholderText('e.g. 1, 5, 10')

        form.addRow('Vgs Start:', self.vgs_start)
        form.addRow('Vgs Stop:', self.vgs_stop)
        form.addRow('Vgs Step:', self.vgs_step)
        form.addRow('Vds Fixed:', self.vds_fixed)
        form.addRow('Vds List:', self.vds_list)

        sweep_layout.addLayout(form)
        layout.addWidget(sweep_card)

        # ---- Measurement parameters ----
        meas_card = CardWidget()
        meas_layout = QVBoxLayout(meas_card)
        meas_layout.setContentsMargins(12, 10, 12, 10)
        meas_layout.addWidget(StrongBodyLabel('Measurement'))

        form2 = QFormLayout()
        form2.setSpacing(8)
        form2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.gate_comp = DoubleSpinBox()
        self.gate_comp.setRange(1e-9, 1)
        self.gate_comp.setValue(1e-3)
        self.gate_comp.setSuffix(' A')
        self.gate_comp.setDecimals(6)
        self.gate_comp.setSingleStep(1e-3)

        self.drain_comp = DoubleSpinBox()
        self.drain_comp.setRange(1e-6, 10)
        self.drain_comp.setValue(0.1)
        self.drain_comp.setSuffix(' A')
        self.drain_comp.setDecimals(3)

        self.delay = DoubleSpinBox()
        self.delay.setRange(0, 10)
        self.delay.setValue(0.01)
        self.delay.setSuffix(' s')
        self.delay.setDecimals(4)

        self.nplc = DoubleSpinBox()
        self.nplc.setRange(0.001, 25)
        self.nplc.setValue(1)

        form2.addRow('Gate Compliance:', self.gate_comp)
        form2.addRow('Drain Compliance:', self.drain_comp)
        form2.addRow('Delay:', self.delay)
        form2.addRow('NPLC:', self.nplc)

        meas_layout.addLayout(form2)
        layout.addWidget(meas_card)

        # ---- Sweep direction ----
        dir_card = CardWidget()
        dir_layout = QVBoxLayout(dir_card)
        dir_layout.setContentsMargins(12, 10, 12, 10)
        dir_layout.addWidget(StrongBodyLabel('Sweep Direction'))

        self.sweep_dir = SegmentedWidget()
        self.sweep_dir.addItem('single', 'Single')
        self.sweep_dir.addItem('dual', 'Dual')
        self.sweep_dir.setCurrentItem('single')
        dir_layout.addWidget(self.sweep_dir)
        layout.addWidget(dir_card)

        layout.addStretch()
        return panel

    def _chart_view_buttons(self):
        return [
            ('Id-Vgs', lambda: self._switch_view('Id-Vgs')),
            ('log|Id|', lambda: self._switch_view('log|Id|')),
            ('gm',      lambda: self._switch_view('gm')),
            ('Ig',      lambda: self._switch_view('Ig')),
        ]

    def _build_plot_card(self) -> PlotCard:
        self._plot = PlotCard('Vgs (V)', 'Id (A)', parent=self)
        return self._plot

    def _setup_metrics(self, layout):
        w1, self._lbl_vth = self._make_metric('Vth', 'V')
        w2, self._lbl_gm = self._make_metric('gm_max', 'S')
        w3, self._lbl_ion_ioff = self._make_metric('Ion/Ioff')
        w4, self._lbl_ss = self._make_metric('SS', 'mV/dec')
        for w in (w1, w2, w3, w4):
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
        vgs_arr = self._sweep_data.get('vgs', np.array([]))

        if view == 'Id-Vgs':
            self._plot.set_log_y(False)
            self._plot.set_labels('Vgs (V)', 'Id (A)')
            for i, (vds, id_arr) in enumerate(self._sweep_data.get('id_curves', [])):
                self._plot.add_curve(vgs_arr, id_arr,
                                     name=f'Vds={vds}V',
                                     color=FLUENT_COLORS[i % len(FLUENT_COLORS)])
        elif view == 'log|Id|':
            self._plot.set_log_y(True)
            self._plot.set_labels('Vgs (V)', 'log|Id| (A)')
            for i, (vds, id_arr) in enumerate(self._sweep_data.get('id_curves', [])):
                self._plot.add_curve(vgs_arr, np.abs(id_arr) + 1e-12,
                                     name=f'Vds={vds}V',
                                     color=FLUENT_COLORS[i % len(FLUENT_COLORS)])
        elif view == 'gm':
            self._plot.set_log_y(False)
            self._plot.set_labels('Vgs (V)', 'gm (S)')
            for i, (vds, id_arr) in enumerate(self._sweep_data.get('id_curves', [])):
                gm = np.gradient(id_arr, vgs_arr)
                self._plot.add_curve(vgs_arr, gm,
                                     name=f'Vds={vds}V',
                                     color=FLUENT_COLORS[i % len(FLUENT_COLORS)])
        elif view == 'Ig':
            self._plot.set_log_y(False)
            self._plot.set_labels('Vgs (V)', 'Ig (A)')
            ig = self._sweep_data.get('ig', np.zeros_like(vgs_arr))
            self._plot.add_curve(vgs_arr, ig, name='Ig',
                                 color=FLUENT_COLORS[5])

    # ------------------------------------------------------------------
    # Demo sweep logic
    # ------------------------------------------------------------------

    def _on_start(self):
        vgs_start = self.vgs_start.value()
        vgs_stop = self.vgs_stop.value()
        vgs_step = self.vgs_step.value()

        try:
            vds_values = [float(v.strip())
                          for v in self.vds_list.text().split(',') if v.strip()]
        except ValueError:
            vds_values = [self.vds_fixed.value()]

        vgs_arr = np.arange(vgs_start, vgs_stop + vgs_step, vgs_step)
        id_curves = []

        for vds in vds_values:
            id_arr = self._simulate_id_vgs(vgs_arr, vds)
            id_curves.append((vds, id_arr))

        ig = np.random.normal(0, 1e-10, len(vgs_arr))

        self._sweep_data = {
            'vgs': vgs_arr,
            'id_curves': id_curves,
            'ig': ig,
        }

        # Animate: reveal progressively
        self._tick_idx = 0
        self._total_ticks = len(vgs_arr)
        self.control_bar.set_running(True)
        self.control_bar.set_status('Sweeping...')
        self.control_bar.set_progress(0)
        self._plot.clear_curves()
        self._plot.set_log_y(False)
        self._plot.set_labels('Vgs (V)', 'Id (A)')

        # Pre-create curves
        self._anim_curves = []
        for i, (vds, _) in enumerate(id_curves):
            c = self._plot.add_curve([], [], name=f'Vds={vds}V',
                                     color=FLUENT_COLORS[i % len(FLUENT_COLORS)])
            self._anim_curves.append(c)

        self._timer.start(20)

    def _on_tick(self):
        idx = self._tick_idx
        vgs = self._sweep_data['vgs']
        id_curves = self._sweep_data['id_curves']
        n = self._total_ticks

        if idx >= n:
            self._timer.stop()
            self._finish_sweep()
            return

        self._tick_idx += 4  # step by 4 points for speed
        end = min(self._tick_idx, n)

        for c, (_, id_arr) in zip(self._anim_curves, id_curves):
            c.setData(vgs[:end], id_arr[:end])

        progress = int(end / n * 100)
        self.control_bar.set_progress(progress)
        self.control_bar.set_status(f'Vgs = {vgs[min(end-1, n-1)]:.2f} V')

    def _finish_sweep(self):
        self.control_bar.set_running(False)
        self.control_bar.set_progress(100)
        self.control_bar.set_status('Complete')
        self._update_metrics()
        InfoBar.success(
            title='Measurement Complete',
            content='Gate Transfer sweep finished.',
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
    # Simulation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _simulate_id_vgs(vgs: np.ndarray, vds: float) -> np.ndarray:
        """Simulate a GaN HEMT Id-Vgs curve."""
        vth = -3.5 + np.random.uniform(-0.3, 0.3)
        mu = 0.04 * (1 + vds * 0.005)
        w_l = 100
        id_arr = np.where(
            vgs > vth,
            mu * w_l * (vgs - vth) ** 1.6 * np.tanh(2 * vds),
            0.0,
        )
        # Add noise
        id_arr += np.abs(np.random.normal(0, 1e-8, len(vgs)))
        return id_arr

    def _update_metrics(self):
        if not self._sweep_data:
            return
        vgs = self._sweep_data['vgs']
        id_curves = self._sweep_data['id_curves']
        if not id_curves:
            return
        _, id_arr = id_curves[-1]

        # Vth (linear extrapolation)
        gm = np.gradient(id_arr, vgs)
        gm_max = np.max(gm)
        idx_gm_max = np.argmax(gm)
        vth_est = vgs[idx_gm_max] - id_arr[idx_gm_max] / (gm_max + 1e-30)

        # Ion/Ioff — use the lower 20% of the sweep range as the off-state region
        vgs_min = vgs[0]
        vgs_range = vgs[-1] - vgs_min
        off_threshold = vgs_min + vgs_range * 0.2
        off_mask = vgs < off_threshold
        i_on = np.max(id_arr)
        i_off = np.max(id_arr[off_mask]) if np.any(off_mask) else 1e-9
        ion_ioff = i_on / (i_off + 1e-30)

        # Subthreshold swing (mV/dec)
        mask = (id_arr > 1e-9) & (id_arr < 1e-3)
        if np.sum(mask) > 3:
            log_id = np.log10(id_arr[mask] + 1e-30)
            dvgs = np.diff(vgs[mask])
            dlog = np.diff(log_id)
            valid = np.abs(dlog) > 1e-12
            if np.any(valid):
                ss = np.mean(np.abs(dvgs[valid]) / np.abs(dlog[valid])) * 1000
            else:
                ss = float('nan')
        else:
            ss = float('nan')

        self._lbl_vth.setText(f'{vth_est:.2f} V')
        self._lbl_gm.setText(f'{gm_max*1000:.2f} mS')
        self._lbl_ion_ioff.setText(f'{ion_ioff:.1e}')
        self._lbl_ss.setText(f'{ss:.1f}' if not np.isnan(ss) else '—')


