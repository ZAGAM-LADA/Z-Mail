import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Z-MAIL RECOVERY")
    app.setOrganizationName("Z-MAIL")
    window = MainWindow()
    window.show()
    return app.exec()
