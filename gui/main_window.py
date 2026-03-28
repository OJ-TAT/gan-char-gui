from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from qfluentwidgets import (FluentWindow, FluentIcon, NavigationItemPosition,
                             SubtitleLabel)

from gui.home_interface import HomeInterface
from gui.settings_interface import SettingsInterface
from gui.test_interfaces.gate_transfer_interface import GateTransferInterface
from gui.test_interfaces.output_interface import OutputInterface
from gui.test_interfaces.breakdown_interface import BreakdownInterface
from gui.test_interfaces.diode_iv_interface import DiodeIVInterface


class MainWindow(FluentWindow):
    """Main application window using Fluent Design."""

    def __init__(self):
        super().__init__()
        self._init_window()
        self._create_interfaces()
        self._init_navigation()

    def _init_window(self):
        self.setWindowTitle('GaN Device Characterization Platform')
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

    def _create_interfaces(self):
        self.home_interface = HomeInterface(self)
        self.home_interface.setObjectName('homeInterface')

        self.gate_transfer_interface = GateTransferInterface(self)
        self.gate_transfer_interface.setObjectName('gateTransferInterface')

        self.output_interface = OutputInterface(self)
        self.output_interface.setObjectName('outputInterface')

        self.breakdown_interface = BreakdownInterface(self)
        self.breakdown_interface.setObjectName('breakdownInterface')

        self.diode_iv_interface = DiodeIVInterface(self)
        self.diode_iv_interface.setObjectName('diodeIVInterface')

        self.settings_interface = SettingsInterface(self)
        self.settings_interface.setObjectName('settingsInterface')

    def _init_navigation(self):
        self.addSubInterface(
            self.home_interface,
            FluentIcon.HOME,
            'Home',
        )
        self.addSubInterface(
            self.gate_transfer_interface,
            FluentIcon.SPEED_HIGH,
            'Gate Transfer',
        )
        self.addSubInterface(
            self.output_interface,
            FluentIcon.DOCUMENT,
            'Output Characteristics',
        )
        self.addSubInterface(
            self.breakdown_interface,
            FluentIcon.MEGAPHONE,
            'Breakdown Test',
        )
        self.addSubInterface(
            self.diode_iv_interface,
            FluentIcon.DEVELOPER_TOOLS,
            'Diode IV',
        )

        self.navigationInterface.addSeparator()

        self.addSubInterface(
            self.settings_interface,
            FluentIcon.SETTING,
            'Settings',
            position=NavigationItemPosition.BOTTOM,
        )
