from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                               QFormLayout, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from qfluentwidgets import (ScrollArea, CardWidget, StrongBodyLabel,
                             BodyLabel, CaptionLabel, LineEdit, PushButton,
                             ComboBox, SubtitleLabel, TitleLabel,
                             PrimaryPushButton, InfoBadge, InfoLevel,
                             FluentIcon, IconWidget)


class _InstrumentCard(CardWidget):
    """Single instrument connection card."""

    def __init__(self, name: str, default_addr: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header row
        header = QHBoxLayout()
        icon = IconWidget(FluentIcon.IOT, self)
        icon.setFixedSize(20, 20)
        lbl_name = StrongBodyLabel(name, self)
        self.status_badge = InfoBadge.attension('Disconnected', self)
        header.addWidget(icon)
        header.addWidget(lbl_name)
        header.addStretch()
        header.addWidget(self.status_badge)
        layout.addLayout(header)

        # VISA address input
        addr_row = QHBoxLayout()
        addr_row.setSpacing(8)
        self.addr_edit = LineEdit(self)
        self.addr_edit.setText(default_addr)
        self.addr_edit.setPlaceholderText('VISA address, e.g. GPIB0::26::INSTR')
        self.connect_btn = PrimaryPushButton('Connect', self)
        self.connect_btn.setFixedWidth(100)
        self.disconnect_btn = PushButton('Disconnect', self)
        self.disconnect_btn.setFixedWidth(110)
        self.disconnect_btn.setEnabled(False)
        addr_row.addWidget(self.addr_edit, 1)
        addr_row.addWidget(self.connect_btn)
        addr_row.addWidget(self.disconnect_btn)
        layout.addLayout(addr_row)

        # Info label
        self.info_label = CaptionLabel('Not connected', self)
        layout.addWidget(self.info_label)

        # Simulate connect/disconnect
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self._on_disconnect)

    def _on_connect(self):
        addr = self.addr_edit.text().strip()
        self.status_badge.setText('Connected')
        self.status_badge.setLevel(InfoLevel.SUCCESS)
        self.info_label.setText(f'Connected → {addr}')
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.addr_edit.setEnabled(False)

    def _on_disconnect(self):
        self.status_badge.setText('Disconnected')
        self.status_badge.setLevel(InfoLevel.ATTENTION)
        self.info_label.setText('Disconnected')
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.addr_edit.setEnabled(True)


class HomeInterface(ScrollArea):
    """Home / Instrument Overview page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('homeInterface')
        self._build_ui()

    def _build_ui(self):
        self.setWidgetResizable(True)
        container = QWidget()
        self.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 20, 36, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ---- Banner ----
        banner = CardWidget(container)
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(24, 20, 24, 20)
        banner_layout.setSpacing(6)

        title = TitleLabel('GaN Device Characterization Platform', banner)
        sub = BodyLabel(
            'Automated test platform for GaN HEMT characterization\n'
            'Gate Transfer · Output Characteristics · Breakdown · Diode IV',
            banner,
        )
        banner_layout.addWidget(title)
        banner_layout.addWidget(sub)
        layout.addWidget(banner)

        # ---- Instruments ----
        instr_header = StrongBodyLabel('Instruments', container)
        layout.addWidget(instr_header)

        self.card_2636b = _InstrumentCard(
            'Keithley 2636B  (Gate SMU)',
            'GPIB0::26::INSTR',
            container,
        )
        self.card_2657a = _InstrumentCard(
            'Keithley 2657A  (Drain SMU High-V)',
            'GPIB0::25::INSTR',
            container,
        )
        layout.addWidget(self.card_2636b)
        layout.addWidget(self.card_2657a)

        # ---- Channel Mapping ----
        ch_card = CardWidget(container)
        ch_layout = QVBoxLayout(ch_card)
        ch_layout.setContentsMargins(16, 14, 16, 14)
        ch_layout.setSpacing(10)
        ch_layout.addWidget(StrongBodyLabel('Channel Mapping'))

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.gate_smu = ComboBox()
        self.gate_smu.addItems(['2636B Channel A', '2636B Channel B'])

        self.drain_lv_smu = ComboBox()
        self.drain_lv_smu.addItems(['2636B Channel B', '2636B Channel A'])

        self.drain_hv_smu = ComboBox()
        self.drain_hv_smu.addItems(['2657A Channel A'])

        form.addRow('Gate SMU:', self.gate_smu)
        form.addRow('Drain SMU (Low-V):', self.drain_lv_smu)
        form.addRow('Drain SMU (High-V):', self.drain_hv_smu)
        ch_layout.addLayout(form)
        layout.addWidget(ch_card)
