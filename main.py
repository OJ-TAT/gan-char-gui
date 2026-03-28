import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qfluentwidgets import setTheme, Theme

from gui.main_window import MainWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    setTheme(Theme.DARK)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
