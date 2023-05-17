from PyQt5.QtWidgets import (
    QFileDialog,
    QWidget,
    QMainWindow,
    QApplication,
    QAction,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QProgressBar,
    QLineEdit,
    QGridLayout,
    QFrame,
    QCheckBox,
    QDialogButtonBox,
    QDialog,
    QMessageBox
)
from PyQt5.QtCore import *


class MainThread(QDialog):
    def __init(self, parent= None):
        super().__init__(parent)
        self.SetUpGui()
        self.oth = OtherThread()
        self.oth.start()
def SetUpGui(self):
    self.layout = QVBoxLayout()

    self.layout.addWidget(self.layout)


class OtherThread(QObject):
    startTask = pyqtSignal()        # in: start the task
    stopTask = pyqtSignal()         # in: stop the task
    statusMsg = pyqtSignal(str)     # out: publish the task status

    def __init(self, parent= None):
        super().__init__(parent)
        self.startTask.connect(self.start)
        self.stopTask.connect(self.capture_stop)

    def start(self):



    def stop(self):






