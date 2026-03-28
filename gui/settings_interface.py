from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog
from PySide6.QtCore import Qt
from qfluentwidgets import (ScrollArea, SettingCardGroup,
                             OptionsSettingCard, PushSettingCard,
                             HyperlinkCard, FluentIcon, qconfig)


class SettingsInterface(ScrollArea):
    """Settings page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('settingsInterface')
        self._build_ui()

    def _build_ui(self):
        self.setWidgetResizable(True)
        container = QWidget()
        self.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(36, 20, 36, 20)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ---- Appearance ----
        appearance_group = SettingCardGroup('Appearance', container)

        self.theme_card = OptionsSettingCard(
            qconfig.themeMode,
            FluentIcon.BRUSH,
            'Application Theme',
            'Choose Light, Dark or follow the system setting',
            texts=['Light', 'Dark', 'Use system setting'],
            parent=appearance_group,
        )
        appearance_group.addSettingCard(self.theme_card)
        layout.addWidget(appearance_group)

        # ---- Data ----
        data_group = SettingCardGroup('Data', container)

        self.save_path_card = PushSettingCard(
            'Choose Folder',
            FluentIcon.FOLDER,
            'Data Save Path',
            'Select the folder to save measurement data',
            parent=data_group,
        )
        self.save_path_card.clicked.connect(self._on_choose_folder)
        data_group.addSettingCard(self.save_path_card)
        layout.addWidget(data_group)

        # ---- About ----
        about_group = SettingCardGroup('About', container)

        self.about_card = HyperlinkCard(
            url='https://github.com/OJ-TAT/gan-char-gui',
            text='Open GitHub',
            icon=FluentIcon.GITHUB,
            title='GaN Device Characterization Platform',
            content='Version 1.0.0 — Built with PySide6 + QFluentWidgets + PyQtGraph',
            parent=about_group,
        )
        about_group.addSettingCard(self.about_card)
        layout.addWidget(about_group)

    def _on_choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Data Folder')
        if folder:
            self.save_path_card.setContent(folder)
