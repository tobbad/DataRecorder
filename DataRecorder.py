# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import time as ti
from math import ceil, isnan
from datetime import *
import numpy as np
import platform
from configuration import configuration
from YoctopuceTask import YoctopuceTask, SignalHubThread
from DataSet import DataSet
my_os = platform.system()
print(my_os)
if my_os == "Windows":
    sys.path.append(
        os.sep.join(
            [
                "C:",
                "Users",
                "tobias.badertscher",
                "AppData",
                "Local",
                "miniconda3",
                "Lib",
                "site-packages"
            ]
        )
    )
    sys.path.append(
        os.sep.join(
            [
                "C:",
                "Users",
                "tobias.badertscher",
                "AppData",
                "roaming",
                "python",
                "python39",
                "site-package"
            ]
        )
    )

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
    QMessageBox,
)
from PyQt5.QtGui import (
    QIcon,
    QKeySequence,
    QPixmap,
    QColor,
    QPalette,
    QIntValidator,
    QFontMetrics,
    QPainter,
)

from PyQt5.QtCore import *
import pyqtgraph as pg

# import matplotlib as pg # Maybe matplot lib can handle NaN?
# import mkl
import qrc_resources

cwd =os.getcwd()
print(cwd)

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


sys.excepthook = except_hook


def currThread():
    return "[thread-" + str(int(QThread.currentThreadId())) + "]"


class StopRecordingDlg(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = True

        self.setWindowTitle("StopRecording!")

        QBtn = {"Yes": QDialogButtonBox.Yes, "No": QDialogButtonBox.No}
        print(QBtn.values())
        btn = 0
        for b in QBtn.values():
            btn |= b

        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.clicked.connect(self.clicked)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def clicked(self, btn):
        if btn.text() == "&Yes":
            self._state = True
        elif btn.text() == "&No":
            self._state = False
        else:
            print("Unknown btn text %s" % btn.text())
        print("StopRecordingDlg %s" % ("Yes" if self._state else "No"))
        self.done(self._state)

    def state(self):
        return self._state


class stopDialog(QDialog):
    def __init__(self):
        super().__init__()
        print("Stop dialog")
        self._state = True
        self.setWindowTitle("HELLO!")

        QBtn = QDialogButtonBox.Yes | QDialogButtonBox.No

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def accept(self):
        print("Set to True")
        self._stat = True

    def reject(self):
        print("Set to False")
        self._state = False

    @property
    def state(self):
        print("Dialog state %d" % self.state)
        return self._state


class SensorDisplay(QMainWindow):
    def __init__(self):
        print("Create app")
        super().__init__()
        self.conf = None
        self.eData = None
        self.cData = None
        self.nanData = None
        self.filename = "./"
        self.btn = {}
        self.capture_size = 0
        self.setSampleInterval_ms = 1
        self.captureTime_s = 1
        self.rawdata = []
        self.unit = []
        self.rawunit = None
        self.punit = None
        self.functionValues = {}
        self._doRecord = False
        self.btnState = {"Start": False, "Clear": False, "Stop": False, "Save": False}
        self.conf = None
        self._doSaveConfig = False
        self.yoctoTask = None
        self.subSigThread = SignalHubThread()
        self.sensor = None
        print("Connected state is %s "% self.connected)

        self.setUpGUI()
        self.updateConnected()

        self.plotname = ""
        self.closeOk = False

        self.capture()  # Set up here to detect connection
        self.updateCnt = 20
        self.updateCounter = self.updateCnt
        self._onGoing = False

    def setUpGUI(self):
        self.setWindowTitle("DataRecorder")
        self.setWindowIcon(QIcon(":/stop.svg"))
        self.addMenuBar()

        self.layout = QVBoxLayout()
        tabWidget = QTabWidget()
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.message = self.statusBar()
        self.message.setSizeGripEnabled(False)
        self.message.addPermanentWidget(self.sizeLabel)
        # Add tab widget for Recorder an Emulator
        self.recorder = self.Recorder()
        tabWidget.addTab(self.recorder, "Recorder")
        self.emulator = self.Emulator()
        tabWidget.addTab(self.emulator, "Emulator")
        # tabWidget.addTab(self.Icons(), "Icons")
        tabWidget.currentChanged.connect(self.tabChanged)

        widget = QWidget()
        widget.setLayout(self.layout)
        # Set the central widget of the Window.
        self.layout.addWidget(tabWidget)
        self.setCentralWidget(widget)
        self.showMsg("Ready")
        print("Gui Ready in Thread %s" % currThread())

    def addMenuBar(self):
        fileOpenAction = self.createAction("&Open...", self.file_open)

        helpAboutAction = self.createAction("&AboutDataRecorder", self.help_about)

        self.fileMenu = self.menuBar().addMenu("&File")
        fileMenueAction = (fileOpenAction, helpAboutAction)

        self.addActions(self.fileMenu, fileMenueAction)

    def createAction(
            self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False
    ):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/{0}.svg".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def fixedUpdate(self):
        if self.xaxisScale.currentIndex() == 1:
            self.frameXMinMax.show()
        elif self.xaxisScale.currentIndex() == 0:
            self.frameXMinMax.hide()

        if self.yaxisScale.currentIndex() == 1:
            self.frameYMinMax.show()
        elif self.xaxisScale.currentIndex() == 0:
            self.frameYMinMax.hide()
        self.updatePlots()

    def Recorder(self):
        print("Set up Recorder")
        res = QWidget()

        layout = QVBoxLayout()
        self.recorderGraph = pg.PlotWidget()

        self.egp = self.recorderGraph.plotItem
        print(self.egp)
        # self.egp.setLabels("left" = '<span style="color:white;font-size:10px">Temperature (°C)</span>')
        self.egr = pg.ViewBox()
        print(self.egr)
        self.egp.showAxis('right')

        self.egp.scene().addItem(self.egr)
        self.egp.getAxis('right').linkToView(self.egr)
        self.egr.setXLink(self.egp)
        self.egp.getAxis('right').setLabel('<span style="color:white;font-size:10px">Current (mA)</span>')
     # self.recorderGraph.setLabel('right', "<span style=\"color:white;font-size:10px\">Current (mA)</span>")
        self.recorderGraph.setLabel(
            "bottom", '<span style="color:white;font-size:10px">Time (s)</span>'
        )
        layout.addWidget(self.recorderGraph)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Time AxisScale"))
        self.xaxisScale = QComboBox()
        self.xaxisScale.addItems(
            [
                "variabel",
                "fixed",
            ]
        )
        self.xaxisScale.currentIndexChanged.connect(self.fixedUpdate)
        hbox.addWidget(self.xaxisScale)
        hbox.addWidget(QLabel("Y AxisScale"))
        self.yaxisScale = QComboBox()
        self.yaxisScale.addItems(
            [
                "variabel",
                "fixed",
            ]
        )
        self.yaxisScale.currentIndexChanged.connect(self.fixedUpdate)
        hbox.addWidget(self.yaxisScale)
        self.showGen1CB = QCheckBox("generic1", self)
        self.showGen1CB.setChecked(True)
        self.showGen1CB.setStyleSheet("background-color:white")
        self.showGen1CB.stateChanged.connect(self.updatecb)
        hbox.addWidget(self.showGen1CB)
        self.showGen2CB = QCheckBox("generic2", self)
        self.showGen2CB.setChecked(True)
        self.showGen2CB.setStyleSheet("background-color:white")
        self.showGen2CB.stateChanged.connect(self.updatecb)
        hbox.addWidget(self.showGen2CB)

        layout.addLayout(hbox)

        onlyUInt = QIntValidator(1, 65535, self)
        self.frameXMinMax = QFrame()
        hbox = QHBoxLayout()

        self.minLabel = QLabel("Minimal time")
        hbox.addWidget(self.minLabel)
        self.minTime = QLineEdit()
        self.minTime.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.minTime.setText("0")
        self.minTime.setValidator(onlyUInt)
        hbox.addWidget(self.minTime)

        self.maxLabel = QLabel("Maximal time")
        hbox.addWidget(self.maxLabel)
        self.maxTime = QLineEdit()
        self.maxTime.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.maxTime.setText("0")
        self.maxTime.setValidator(onlyUInt)
        hbox.addWidget(self.maxTime)
        self.frameXMinMax.setLayout(hbox)
        layout.addWidget(self.frameXMinMax)

        self.frameYMinMax = QFrame()
        hbox = QHBoxLayout()
        self.minyLabel = QLabel("Showed minimal Y Axis")
        hbox.addWidget(self.minyLabel)
        self.miny = QLineEdit()
        self.miny.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.miny.setText("0")
        self.miny.setValidator(onlyUInt)
        hbox.addWidget(self.miny)

        self.maxyLabel = QLabel("Showed maximal Y Axis")
        hbox.addWidget(self.maxyLabel)
        self.maxy = QLineEdit()
        self.maxy.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.maxy.setValidator(onlyUInt)
        self.maxy.setText("0")
        hbox.addWidget(self.maxy)
        self.frameYMinMax.setLayout(hbox)
        layout.addWidget(self.frameYMinMax)

        self.fixedUpdate()

        hbox = QHBoxLayout()
        icons = [
            ["Start", self.doStart, False],
            ["Stop", self.doStop, False],
            ["Clear", self.doClear, False],
            ["Save", self.doSave, False],
        ]
        for name, fn, show in icons:
            self.btn[name] = QPushButton(name)
            icon = QIcon(":/%s.svg" % name.lower())
            self.btn[name].setIcon(icon)
            self.btn[name].clicked.connect(fn)
            self.btnState[name] = show
            hbox.addWidget(self.btn[name])
        layout.addLayout(hbox)


        hbox = QHBoxLayout()
        self.intervalFrame = QFrame()
        hboxs = QHBoxLayout()
        self.setSampleInterval_ms = 200
        self.captureTime_s = 1
        onlyInt0_1000 = QIntValidator(1, 1000, self)
        siLabel = QLabel("Sample interval")
        self.sIntVal_edit = QLineEdit()
        self.sIntVal_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sIntVal_edit.setText("1")
        self.sIntVal_edit.setValidator(onlyInt0_1000)
        siLabel.setBuddy(self.sIntVal_edit)
        hboxs.addWidget(siLabel)
        hboxs.addWidget(self.sIntVal_edit)
        self.sampleUnit = QComboBox()
        self.sampleUnit.addItems(["ms", "s"])
        self.sampleUnit.setCurrentIndex(0)
        hboxs.addWidget(self.sampleUnit)
        self.intervalFrame.setLayout(hboxs)
        hbox.addWidget(self.intervalFrame)
        self.intervalFrame.show()

        duration = QLabel("Capture Time")
        self.captime_edit = QLineEdit()
        self.captime_edit.setText("1")
        self.captime_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.captime_edit.setPlaceholderText("xxxx")
        self.captime_edit.setValidator(onlyInt0_1000)
        duration.setBuddy(self.captime_edit)
        hbox.addWidget(duration)
        hbox.addWidget(self.captime_edit)
        self.sampcapDur = QComboBox()

        self.sampcapDur.addItems(["s", "m", "h"])
        hbox.addWidget(self.sampcapDur)
        self.progressBar = QProgressBar(minimum=0, maximum=100, objectName="bar")
        self.progressBar.setValue(0)
        self.progressBar.resize(300, 100)
        hbox.addWidget(self.progressBar)
        layout.addLayout(hbox)

        self.frame1 = QFrame()
        self.frame1.setStyleSheet(
            "QFrame {background-color: rgb(255, 255, 255);"
            "border-width: 1;"
            "border-radius: 3;"
            "border-style: solid;"
            "border-color: rgb(0, 0, 0)}"
        )
        self.frame1.setFrameShape(QFrame.StyledPanel)
        self.frame1.setLineWidth(3)

        gLayout = QGridLayout()

        self.gen1Label = QLabel("generic1")
        gLayout.addWidget(self.gen1Label, 0, 0)

        label = QLabel("Messwert")
        gLayout.addWidget(label, 0, 2)
        self._actVal1 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actVal1, 0, 3)
        label = QLabel("Min:")
        gLayout.addWidget(label, 0, 4)
        self._actmin1 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actmin1, 0, 5)
        label = QLabel("Max:")
        gLayout.addWidget(label, 0, 6)
        self._actmax1 = QLabel("%.2f" % 120)
        gLayout.addWidget(self._actmax1, 0, 7)
        self.pUnit = QLabel("°C")
        gLayout.addWidget(self.pUnit, 0, 8)

        label = QLabel("Rohwert")
        gLayout.addWidget(label, 1, 2)
        self._actRawVal1 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actRawVal1, 1, 3)
        label = QLabel("Min:")
        gLayout.addWidget(label, 1, 4)
        self._actRawMin1 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actRawMin1, 1, 5)
        label = QLabel("Max:")
        gLayout.addWidget(label, 1, 6)
        self._actRawMax1 = QLabel("%.2f" % 120)
        gLayout.addWidget(self._actRawMax1, 1, 7)
        self.rawUnit = QLabel("mA")
        gLayout.addWidget(self.rawUnit, 1, 8)
        self.frame1.setLayout(gLayout)
        # self.frame1.hide()
        layout.addWidget(self.frame1)

        self.frame2 = QFrame()
        self.frame2.setStyleSheet(
            "QFrame {background-color: rgb(255, 255, 255);"
            "border-width: 1;"
            "border-radius: 3;"
            "border-style: solid;"
            "border-color: rgb(0, 0, 0)}"
        )
        self.frame2.setFrameShape(QFrame.StyledPanel)
        self.frame2.setLineWidth(3)
        # frame1.setStyleSheet("background-color: blue")
        # frame1.setFrameStyle(QFrame.VLine|QFrame.Sunken)

        gLayout = QGridLayout()

        self.gen2Label = QLabel("generic2")
        gLayout.addWidget(self.gen2Label, 0, 0)
        # gLayout.addWidget(self.conState, 0, 1)
        label = QLabel("Messwert")
        gLayout.addWidget(label, 0, 2)
        self._actVal2 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actVal2, 0, 3)
        label = QLabel("Min:")
        gLayout.addWidget(label, 0, 4)
        self._actmin2 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actmin2, 0, 5)
        label = QLabel("Max:")
        gLayout.addWidget(label, 0, 6)
        self._actmax2 = QLabel("%.2f" % 120)
        gLayout.addWidget(self._actmax2, 0, 7)
        self.pUnit = QLabel("°C")
        gLayout.addWidget(self.pUnit, 0, 8)

        label = QLabel("Rohwert")
        gLayout.addWidget(label, 1, 2)
        self._actRawVal2 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actRawVal2, 1, 3)
        label = QLabel("Min:")
        gLayout.addWidget(label, 1, 4)
        self._actRawMin2 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actRawMin2, 1, 5)
        label = QLabel("Max:")
        gLayout.addWidget(label, 1, 6)
        self._actRawMax2 = QLabel("%.2f" % 120)
        gLayout.addWidget(self._actRawMax2, 1, 7)
        self.rawUnit = QLabel("mA")
        gLayout.addWidget(self.rawUnit, 1, 8)
        self.frame2.setLayout(gLayout)
        # self.frame2.hide()
        layout.addWidget(self.frame2)

        hbox = QHBoxLayout()

        hbox.addWidget(QLabel("File name"))
        self.QFilename = QLineEdit()
        self.QFilename.setText("")

        hbox.addWidget(self.QFilename)
        hbox.addWidget(QLabel("Plot name"))
        self.QPlotname = QLineEdit()
        self.QPlotname.setText("")
        hbox.addWidget(self.QPlotname)

        layout.addLayout(hbox)
        self.onTimingChanged()
        res.setLayout(layout)

        self.QFilename.textChanged.connect(self.recorderFileNameChanged)
        self.QPlotname.textChanged.connect(self.plotNameChanged)
        self.sIntVal_edit.textChanged.connect(self.onTimingChanged)
        self.captime_edit.textChanged.connect(self.onTimingChanged)
        self.sampleUnit.currentIndexChanged.connect(self.onTimingChanged)
        self.sampcapDur.currentIndexChanged.connect(self.onTimingChanged)

        print("Recorder created")
        return res

    def onStateClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            print("state is %s" % (radioButton.state))

    def plotNameChanged(self):
        self.plotname = self.QPlotname.text()
        self.recorderGraph.setTitle(self.plotname)
        print("Set plotname to %s" % (self.plotname))

    def recorderFileNameChanged(self):
        print("Recorder file channge %s" % (self.QFilename.text()))

    def Emulator(self):
        res = QWidget()
        layout = QVBoxLayout()
        self.emulatorGraph = pg.PlotWidget()
        self.emulatorGraph.addLegend()
        layout.addWidget(self.emulatorGraph)
        self.emulatorGraph.setTitle("Initial")


        hbox = QHBoxLayout()
        self.showeGen1 = QCheckBox("Show generic1", self)
        self.showeGen1.stateChanged.connect(self.updatePlots)
        self.showeGen1.setChecked(True)
        self.showeGen1.setStyleSheet("color: rgb(255, 0, 0);")
        hbox.addWidget(self.showeGen1)

        self.showeGen2 = QCheckBox("Show generic2", self)
        self.showeGen2.setChecked(True)
        self.showeGen2.stateChanged.connect(self.updatePlots)
        self.showeGen2.setStyleSheet("color: rgb(0, 255, 0);")
        hbox.addWidget(self.showeGen2)

        self.sync = QCheckBox("Synchronize", self)
        self.sync.stateChanged.connect(self.updatePlots)
        self.sync.setChecked(True)
        self.sync.stateChanged.connect(self.synChecked)
        hbox.addWidget(self.sync)

        btns =  [["Replay", self.doReplay, False]]
        for name, fn, show in btns:
            self.btn[name] = QPushButton(name)
            icon = QIcon(":/%s.svg" % name.lower())
            self.btn[name].setIcon(icon)
            self.btn[name].clicked.connect(fn)
            self.btnState[name] = show
            if show:
                self.btn[name].show()
            else:
                self.btn[name].hide()
            hbox.addWidget(self.btn[name])

        self.eintervalFrame = QFrame()
        hbox1 = QHBoxLayout()
        self.setSampleEInterval_ms = 200
        self.captureETime_s = 1
        onlyInt0_1000 = QIntValidator(1, 1000, self)
        siELabel = QLabel("Sample interval")
        self.siE_edit = QLineEdit()
        self.siE_edit.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.siE_edit.setText("1")
        self.siE_edit.setValidator(onlyInt0_1000)
        siELabel.setBuddy(self.siE_edit)
        hbox1.addWidget(siELabel)
        hbox1.addWidget(self.siE_edit)
        self.sampleEUnit = QComboBox()
        self.sampleEUnit.addItems(["ms", "s"])
        self.sampleEUnit.setCurrentIndex(0)
        hbox1.addWidget(self.sampleEUnit)
        self.eintervalFrame.setLayout(hbox1)
        hbox.addWidget(self.eintervalFrame)


        layout.addLayout(hbox)

        gLayout = QGridLayout()
        label = QLabel("Aktueller Wert")
        gLayout.addWidget(label, 0, 0)
        self._acteVal = QLabel("%.2f" % 0)
        gLayout.addWidget(self._acteVal, 0, 1)
        print(self._acteVal)
        label = QLabel("Min:")
        gLayout.addWidget(label, 0, 2)
        self._actemin = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actemin, 0, 3)
        label = QLabel("Max:")
        gLayout.addWidget(label, 0, 4)
        self._actemax = QLabel("%.2f" % 120)
        gLayout.addWidget(self._actemax, 0, 5)
        self.peUnit = QLabel("°C")
        gLayout.addWidget(self.peUnit, 0, 6)

        label = QLabel("Aktueller Rohwert")
        gLayout.addWidget(label, 1, 0)
        self._acteRawVal = QLabel("%.2f" % 0)
        gLayout.addWidget(self._acteRawVal, 1, 1)
        label = QLabel("Min:")
        gLayout.addWidget(label, 1, 2)
        self._acteRawMin = QLabel("%.2f" % 0)
        gLayout.addWidget(self._acteRawMin, 1, 3)
        label = QLabel("Max:")
        gLayout.addWidget(label, 1, 4)
        self._acteRawMax = QLabel("%.2f" % 120)
        gLayout.addWidget(self._acteRawMax, 1, 5)
        self.raweUnit = QLabel("mA")
        gLayout.addWidget(self.raweUnit, 1, 6)
        layout.addLayout(gLayout)

        res.setLayout(layout)
        if self.eData is not None:
            self.syncData()
            self.updatePlots()
        print("Emulator created %s" % self.emulatorGraph)
        return res

    def append_data(self, data):
        if data[0] is None:
            print("Stop capture")
            self.stopCapture()
            return
        self.onGoing = self.onGoing and (not (isnan(data[3])) or (not isnan(data[6])))
        self.cData.onGoing = self.onGoing
        self.nanData.onGoing = self.onGoing
        if not self.onGoing:
            #print("Removed sensors onGoing is %s" %  self.onGoing)
            self.sensor = None
        self.cData.append(data)
        self.nanData.append(data)
        self.updateCounter-=1
        if self.updateCounter == 0:
            self.updateCounter = self.updateCnt
            self.syncData()
            self.updatePlots()

    def file_open(self):
        local_dir = os.path.dirname(self.filename) if self.filename is not None else "."
        fmt = ["CSV Files (*.csv)", "Excel Files (*.xslc)"]
        files = QFileDialog.getOpenFileName(self, "Load data", local_dir, fmt[0])
        if files:
            print("Emulator data")
            r2p = self.conf.getR2PFunction
            p2r = self.conf.getP2RFunction
            self.eData = DataSet("eData", False, p2r, r2p)
            self.eData.load(files[0])
            self.updatePlots()

    def capture(self):
        # Start Yoctopuce I/O task in a separate thread
        if self.yoctoTask is None:
            print("Inital Set up yoctopuc task")
            self.yoctoTask = YoctopuceTask(self.subSigThread)
            self.subSigThread.statusMsg.connect(self.showMsg)
            self.subSigThread.arrival.connect(self.arrival)
            self.subSigThread.oarrival.connect(self.oarrival)
            self.subSigThread.removal.connect(self.removal)
            self.subSigThread.stopTask.connect(self.stopCapture)
            self.subSigThread.moveToThread(self.subSigThread)
            self.subSigThread.updateSignal.connect(self.append_data)
            self.subSigThread.startTask.emit()
            self.subSigThread.start()

    def synChecked(self):
        if self.sync.isChecked():
            self.eintervalFrame.hide()
            self.btn["Replay"].hide()
            print("Sync is active")
        else:
            self.btn["Replay"].show()
            self.eintervalFrame.show()

            print("Sync is passive")
    @property
    def connected(self):
        if self.sensor is None:
            print("No more connected")
            return False
        else:
            #print("Count of sensors is %d, sensors are %s" % (len(self.sensor), self.sensor))
            return len(self.sensor)>0


    @property
    def notconnected(self):
        if self.sensor is None:
            print("not connected is True %s" % self.sensor)
            return True
        else:
            print("not connected is False %s"% self.sensor)
            return False


    @pyqtSlot(dict)
    def arrival(self, device):

        if len(device) == 0:
            self.sensor = None
            print("Detected disconnect in arrival")
            self.nanData.FileName = None
            self.nanData.connected = False
        else:
            self.sensor = device

        if self.connected:
            print("Received  %d sensors (%s) in arrival with doRecord= %s" % (
            len(self.sensor), self.sensor, self.doRecord))
            if self.doRecord:
                print("Skip")
                pass
            else:
                print("Show buttons in sensor arrival")
                self.btnState["Start"] = True
                self.btnState["Stop"] = False
                self.btnState["Clear"] = False
                self.btnState["Save"] = False
                self.updateConnected()
            # log arrival
            if self.conf is None:
                self.conf = configuration(self.yoctoTask)
                p2r = self.conf.getP2RFunction
                self.r2p = self.conf.getR2PFunction
                alwaysTrue = lambda: True
                onlyNan = lambda: not self.connected
                print("Current not connected is %s" % self.notconnected)
                self.cData = DataSet("", alwaysTrue, p2r, self.r2p)
                self.nanData = DataSet("nan", self.notconnected, p2r, self.r2p)
                self.eData = DataSet("eData", alwaysTrue, p2r, self.r2p)
            print("Device connected in Datarecorder onGoing %s" % (self.onGoing))
            self.sIntVal_edit.setText("%d" % self.conf.SampleInterval["time"])
            sunit = {"ms": 0, "s": 1}
            idx = sunit[self.conf.SampleInterval["unit"]]
            self.sampleUnit.setCurrentIndex(idx)
            cunit = {"s": 0, "m": 1, "h": 2}
            self.captime_edit.setText("%d" % self.conf.CaptureTime["time"])
            idx = cunit[self.conf.CaptureTime["unit"]]
            self._doSaveConfig = False
            self.sampcapDur.setCurrentIndex(idx)
            self._doSaveConfig = True
            if self.onGoing:
                print("Show old buttons")
            print("DR Registered Sensors %s" % self.sensor)
        self.onTimingChanged()
    def oarrival(self, device):
        self.oSensor = device
        print("Received output device in DataRecorder %s" % self.oSensor)

    @pyqtSlot(dict)
    def removal(self, device):
        # log removal
        if len(device)==0:
            # keep button state
            print("Detected onGoing in removal")
            self.nanData.FileName = None
        self.sensor = None
        self.nanData.connected = self.connected
        print("Device disconnected:", device)

    def updateConnected(self):
        if self.cData is not None:
            self.cData.connected = self.connected
        if self.nanData is not None:
            self.nanData.connected = self.connected
        if self.connected:
            label = self.showGen1CB.text()
            self.showGen1CB.setText(label)
            label = self.showGen2CB.text()
            self.showGen2CB.setText(label)
            self.showGen1CB.setStyleSheet("background-color:green")
            self.showGen2CB.setStyleSheet("background-color:red")
            self.frame1.setStyleSheet("background-color:green")
            self.frame2.setStyleSheet("background-color:red")

        else:
            self.showGen1CB.setStyleSheet("background-color:white")
            self.showGen2CB.setStyleSheet("background-color:white")
            self.frame1.setStyleSheet("background-color:white")
            self.frame2.setStyleSheet("background-color:white")
        if self.btnState["Start"]:
            self.btn["Start"].show()
        else:
            self.btn["Start"].hide()

        if self.btnState["Stop"]:
            self.btn["Stop"].show()
        else:
            self.btn["Stop"].hide()

        if self.btnState["Save"]:
            self.btn["Save"].show()
        else:
            self.btn["Save"].hide()

        if self.btnState["Clear"]:
            self.btn["Clear"].show()
        else:
            self.btn["Clear"].hide()

    def doStart(self):
        self.capture()
        print("Show buttons in doStart Thread %s" % (self.yoctoTask))
        self.onTimingChanged()
        self.btnState["Start"] = False
        self.btnState["Stop"] = True
        self.btnState["Clear"] = False
        self.btnState["Save"] = False
        if self.yoctoTask is None:
            print("No sensor connected")
        if self.yoctoTask.capture_start():
            self.onGoing = True
            self.doRecord = True
            print("Set doRecord in doStart")
            self.cData.FileName = None
            self.intervalFrame.hide()
            self.syncData()
            self.updatePlots()
        self.updateConnected()

    def stopRemote(self):
        print("Stop Remote in %s" % currThread())
        self.subSigThread.stopTask.emit()

    def doReplay(self):
        if self.sync.isChecked():
            print("Use intervall from recorder")
        else:
            print("Use intervall from datafile ")
        pass
    def stopCapture(self):
        print("DataRecorder stopCapture received in %s" % currThread())
        print("Show buttons in stopCapture")
        print("Reset doRecord in stopCapture")

        self.doRecord = False
        self.onGoing = False
        self.btnState["Start"] = False
        self.btnState["Stop"] = False
        self.btnState["Clear"] = True
        self.btnState["Save"] = True
        self.updateConnected()
        self.progressBar.setValue(int(100))
        self.intervalFrame.show()

    def doStop(self):
        # Ask for really Stop
        dlg = StopRecordingDlg(self)
        res = dlg.exec_()
        if dlg:
            state = dlg.state()
            if state:
                self.stopRemote()
            else:
                print("doStop: Continue recording")

    def doClear(self):
        self.recorderGraph.clear()
        print("doClear: Show only Start button")
        self.btnState["Start"] = True
        self.btnState["Stop"] = False
        self.btnState["Clear"] = False
        self.btnState["Save"] = False
        self.updateConnected()
        self.progressBar.setValue(0)
        self.cData.clear()
        self.sensor = None

    @property
    def doRecord(self):
        return self._doRecord
    @doRecord.setter
    def doRecord(self, val):
        self._doRecord = val
        self.cData.doRecord= val
        self.nanData.doRecord = val
        self.yoctoTask.doRecord = val
    @property
    def onGoing(self):
        return self._onGoing

    @onGoing.setter
    def onGoing(self, val):
        self._onGoing = val
        self.cData.onGoing= val
        self.nanData.onGoing = val



    def doSave(self):
        fmt = ["CSV Files (*.csv)", "Excel Files (*.xslc)"]
        fname, ftype = QFileDialog.getSaveFileName(
            self, "Store captured data", self.QFilename.text(), fmt[0]
        )
        if fname is None:
            fname = self.QFilename.text()

        if len(fname) > 0:
            self.cData.FileName = fname
            self.cData.save()
            print("Save data to %s" % fname)
        if len(fname) > 0:
            self.cData.FileName = fname
            self.cData.save()

    def help_about(self):
        dlg = QMessageBox()
        dlg.setWindowTitle("Datarecorder")
        dlg.setText("This is a datalogger/emulator application")
        button = dlg.exec_()
        if button == QMessageBox.Ok:
            print("OK")

    @pyqtSlot(str)
    def showMsg(self, text, time=5000):
        self.message.showMessage(text, time)

    def onTimingChanged(self):
        if not self.doRecord:
            # print("Call onTimingChanged in recording %s do Save %s" % ( self.sampleUnit.currentIndex(), self._doSaveConfig))
            self.sampInt = {"time": 0, "unit": "ms"}
            if self.sampleUnit.currentIndex() == 0:
                self.sampInt["unit"] = "ms"
                self.setSampleInterval_ms = 1
            elif self.sampleUnit.currentIndex() == 1:
                self.sampInt["unit"] = "s"
                self.setSampleInterval_ms = 1000
            sInt = (
                1 if self.sIntVal_edit.text() == None else int(self.sIntVal_edit.text())
            )
            self.sampInt["time"] = sInt
            if self.conf != None and self._doSaveConfig == True:
                self.conf.SampleInterval = self.sampInt
            self.setSampleInterval_ms *= sInt
            if self.yoctoTask is not None:
                self.yoctoTask.setSampleInterval_ms(self.setSampleInterval_ms)
            # print("Sample intervall is %d %s" % (  self.sampInt["time"],  self.sampInt["unit"]))

            self.capTime = {"time": 0, "unit": "m"}
            if self.sampcapDur.currentIndex() == 0:
                self.capTime["unit"] = "s"
                self.captureTime_s = 1
            elif self.sampcapDur.currentIndex() == 1:
                self.capTime["unit"] = "m"
                self.captureTime_s = 60
            else:
                self.capTime["unit"] = "h"
                self.captureTime_s = 3600
            cTi = (
                1 if self.captime_edit.text() == None else int(self.captime_edit.text())
            )
            self.capTime["time"] = cTi
            self.captureTime_s *= cTi

            if self.conf != None and self._doSaveConfig:
                self.conf.CaptureTime = self.capTime

            self.capture_size = ceil(
                float(1000 * self.captureTime_s) / (float(self.setSampleInterval_ms))
            )
            print(
                "Set capture time %d %s; Size: is %d samples; Interval @ %f %s"
                % (
                    self.captureTime_s,
                    self.capTime["unit"],
                    self.capture_size,
                    self.setSampleInterval_ms,
                    self.sampInt["unit"],
                )
            )
            if self.yoctoTask is not None:
                if not self.doRecord:
                    self.yoctoTask.set_capture_size(self.capture_size)
            if self._doSaveConfig and self.conf != None:
                print("Save config")
                self.conf.save(self._doSaveConfig)
            else:
                print("Do not save")
        else:
            print("Skip in onTimingChanged as do record")

    def tabChanged(self, index):
        self.syncData()
        self.updatePlots()
        print("Tab changed %d" % (index))

    def updatecb(self):
        if self.showGen1CB.checkState():
            self.frame1.show()
        else:
            self.frame1.hide()
        if self.showGen2CB.checkState():
            self.frame2.show()
        else:
            self.frame2.hide()
        self.updatePlots()

    def syncData(self):
        if self.cData is not None:
            self.cData.sync()
        if self.nanData is not None:
            self.nanData.sync()
        if self.eData is not None:
            self.eData.sync()

    def updatePlots(self):
        if self.cData is not None:
            if (self.cData.data1 is not None) or (self.cData.data2 is not None):
                if len(self.cData) > 0:
                    x = self.cData.data1[:, 0]
                    self.recorderGraph.clear()
                    if self.showGen1CB.isChecked():
                        self.gen1Label.setText("generic1")
                        g1 = self.cData.data1[:, 1]
                        g1Pure = g1[np.logical_not(np.isnan(g1))]
                        g1Raw = self.cData.data1[:, 2]
                        g1RawPure = g1Raw[np.logical_not(np.isnan(g1Raw))]
                        g1RawLast = 0

                        if len(g1RawPure) == 0:
                            g1min = 0
                            g1max = 0
                            g1Rawmin = 0
                            g1Rawmax = 0
                        else:
                            g1min = g1Pure.min()
                            g1max = g1Pure.max()
                            g1Rawmin = g1RawPure.min()
                            g1Rawmax = g1RawPure.max()
                        self._actVal1.setText("%.2f" % g1[-1])
                        self._actmin1.setText("%.2f" % g1min)
                        self._actmax1.setText("%.2f" % g1max)

                        self._actRawVal1.setText("%.2f" % g1RawLast)
                        self._actRawMin1.setText("%.2f" % g1Rawmin)
                        self._actRawMax1.setText("%.2f" % g1Rawmax)
                        pl = self.recorderGraph.plot(
                            x, g1, name="generic1", pen=pg.mkPen("green")
                        )
                        self.egr.addItem(pg.PlotCurveItem(g1Raw))
                        self.egr.setGeometry(self.egp.vb.sceneBoundingRect())
                        self.egr.linkedViewChanged(self.egp.vb, self.egr.XAxis)

                        vp = self.recorderGraph.getViewBox()
                        if self.xaxisScale.currentIndex() == 1:
                            tmin = int(self.minTime.text())
                            tmax = int(self.maxTime.text())
                            self.recorderGraph.setXRange(tmin, tmax, padding=0)
                            vp.disableAutoRange(axis="x")
                        else:
                            vp.enableAutoRange(axis="x")

                        if self.yaxisScale.currentIndex() == 1:
                            minY = int(self.miny.text())
                            maxY = int(self.maxy.text())
                            self.recorderGraph.setYRange(minY, maxY, padding=0)
                            vp.disableAutoRange(axis="y")
                        else:
                            vp.enableAutoRange(axis="y")
                    else:
                        self.frame1.hide()

                    if self.showGen2CB.isChecked():
                        self.gen2Label.setText("generic2")
                        g2 = self.cData.data2[:, 1]
                        g2Pure = g2[np.logical_not(np.isnan(g2))]
                        g2Raw = self.cData.data2[:, 2]
                        g2RawPure = g2Raw[np.logical_not(np.isnan(g2Raw))]
                        if len(g2RawPure) == 0:
                            g2min = 0
                            g2max = 0
                            g2Rawmin = 0
                            g2Rawmax = 0
                        else:
                            g2min = g2Pure.min()
                            g2max = g2Pure.max()
                            g2Rawmin = g2RawPure.min()
                            g2Rawmax = g2RawPure.max()
                        self._actVal2.setText("%.2f" % g2[-1])
                        self._actmin2.setText("%.2f" % g2min)
                        self._actmax2.setText("%.2f" % g2max)
                        self._actRawVal2.setText("%.2f" % g2Raw[-1])
                        self._actRawMin2.setText("%.2f" % g2Rawmin)
                        self._actRawMax2.setText("%.2f" % g2Rawmax)
                        self.recorderGraph.plot(x, g2, name="generic2", pen=pg.mkPen("red"))
                    else:
                        self.frame2.hide()
                    self.pUnit.setText(self.punit)
                    self.rawUnit.setText(self.rawunit)
                    self.recorderGraph.setTitle(self.QPlotname.text())
                    self.recorderGraph.addLegend()
                progress = 100.0 * len(self.cData) / float(self.capture_size)
                print("Progress %.1f of %d " % (progress, self.capture_size))
                self.progressBar.setValue(int(progress))
            else:
                print("Skip recorder as there is no Data in data1/2")
        #
        # Emulator graph
        #
        if self.eData is not None:
            if len(self.eData) > 0 and self.emulatorGraph is not None:

                x = self.eData.data1[:, 0]
                y1 = self.eData.data1[:, 1]
                g1Pure = y1[np.logical_not(np.isnan(y1))]
                g1Raw = self.eData.data1[:, 2]
                g1RawPure = g1Raw[np.logical_not(np.isnan(g1Raw))]

                y2 = self.eData.data2[:, 1]
                g2Raw = self.eData.data1[:, 2]
                g2RawPure = g2Raw[np.logical_not(np.isnan(g2Raw))]
                print("Show emulator graph of len = %d/%d data" % (len(self.eData.data2),len(self.eData.data1)))

                if len(g1RawPure) == 0:
                    g1min = 0
                    g1max = 0
                    g1Rawmin = 0
                    g1Rawmax = 0
                else:
                    g1min = g1Pure.min()
                    g1max = g1Pure.max()
                    g1Rawmin = g1RawPure.min()
                    g1Rawmax = g1RawPure.max()

                self._acteVal.setText("%.2f" % y1[-1])
                self._actemin.setText("%.2f" % g1min)
                self._actemax.setText("%.2f" % g1max)
                self._acteRawVal.setText("%.2f" % g1Raw[-1])
                self._acteRawMin.setText("%.2f" % g1Rawmin)
                self._acteRawMax.setText("%.2f" % g1Rawmax)

                self.emulatorGraph.clear()

                self.emulatorGraph.addLegend()
                if self.showeGen1.checkState():
                    p1 = self.emulatorGraph.plot(
                        x, y1, name="generic1", pen=pg.mkPen("red")
                    )
                if self.showeGen2.checkState():
                    p2 = self.emulatorGraph.plot(
                        x, y2, name="generic2", pen=pg.mkPen("green")
                    )
                self.emulatorGraph.setTitle(self.eData.FileName)
        else:
            print("Skip emulator graph as eData is %s" % self.eData)


if __name__ == "__main__":
    # #print("Initalize class")
    # app  = QApplication(sys.argv)
    # window = App()
    # translator = QTranslator(app)

    # defaultLocale = QLocale.system().name()
    # translator.load(defaultLocale)
    # app.installTranslator(translator)
    # print(defaultLocale)
    app = QApplication(sys.argv)
    window = SensorDisplay()
    window.show()
    sys.exit(app.exec())
