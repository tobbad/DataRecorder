# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse
import csv
from math import ceil, isnan
import numpy as np
from datetime import *
import numpy as np
from configuration import configuration
from YoctopuceTask import YoctopuceTask

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
            "site-packages",
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
    QSpinBox, 
    QComboBox, 
    QProgressBar, 
    QLineEdit, 
    QGridLayout, 
    QFrame,
    QCheckBox,
    QRadioButton,
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
    QPainter

)

from PyQt5.QtCore import *
import pyqtgraph as pg
#import matplotlib as pg # Maybe matplot lib can handle NaN?
#import mkl
import qrc_resources
wd = os.sep.join(["C:","Users","tobias.badertscher","source", "repos", "python", "DataRecorder"])


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook


def currThread():
    return '[thread-' + str(int(QThread.currentThreadId())) + ']'


class StopRecordingDlg(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = True

        self.setWindowTitle("StopRecording!")

        QBtn = {"Yes":QDialogButtonBox.Yes, "No": QDialogButtonBox.No}
        print(QBtn.values())
        btn = 0
        for b in  QBtn.values():
            btn |= b
        
        self.buttonBox = QDialogButtonBox(btn)
        self.buttonBox.clicked.connect(self.clicked)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
    
    def clicked(self, btn):
        if btn.text()=="&Yes":
            print("Set stop to True")
            self._state = True
        elif btn.text() == "&No":
            print("Set stop to False")
            self._state = False
        else:
            print("Unknown btn text %s" % btn.text())
        print("Stop Record %s" %("Yes" if self._state else "No"))
        self.done(self._state)
 
    def state(self):
        print("Return _state %d" % self._state)
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
        self._stat= True
         
    def reject(self):
        print("Set to False")
        self._state= False
    
    @property
    def state(self):
        print("Dialog state %d" % self.state)
        return self._state


class SensorDisplay(QMainWindow):
    def __init__(self):
        print("Create app")
        super().__init__()
        self.dirty = False
        self.emFile = ""
        self.filename = "./"
        self.emdata=None
        self.btn = {}
        self.doRecord = False
        self.capture_size = 0
        self.setSampleInterval_ms =1
        self.captureTime_s = 1
        self.rawdata = []
        self.pData = None
        self.unit  =[]
        self.rawunit = None
        self.punit = None
        self.functionValues = {}
        self.yoctoTask = None
        self.data1 = None
        self.data2 = None
        self.emData = []
        self.onGoing = True
        self.btnState = {"Start":False, "Clear":False, "Stop":False, "Save":False}
        self.setUpGUI()
        self.plotname = ""
        self.closeOk = False
        self.sensor = None
        self.YoctopuceTask= None
        self.capture()
        self.isConnected = True

    def setUpGUI(self):    
        self.setWindowTitle("DataRecorder")
        self.setWindowIcon(QIcon(":/stop.svg"))
        self.addMenuBar()
        
        self.layout = QVBoxLayout()
        tabWidget = QTabWidget()
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.message = self.statusBar()
        self.message.setSizeGripEnabled(False)
        self.message.addPermanentWidget(self.sizeLabel)
        # Add tab widget for Recorder an Emulator
        tabWidget.addTab(self.Recorder(), "Recorder")
        #tabWidget.addTab(self.Icons(), "Icons")
        tabWidget.addTab(self.Emulator(), "Emulator")
        tabWidget.currentChanged.connect(self.tabChanged)
        
        widget = QWidget()
        widget.setLayout(self.layout)
        # Set the central widget of the Window.
        self.layout.addWidget(tabWidget)
        self.setCentralWidget(widget)
        self.showMsg("Ready")
        print("Gui Ready")

    def addMenuBar(self):
        fileOpenAction = self.createAction("&Open...", self.file_open)

        helpAboutAction = self.createAction("&AboutDataRecorder",
                self.help_about)
        
        self.fileMenu = self.menuBar().addMenu("&File")     
        fileMenueAction=(fileOpenAction,helpAboutAction)

        self.addActions(self.fileMenu,  fileMenueAction)
       
    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False):
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
        elif self.xaxisScale.currentIndex()==0:
            self.frameXMinMax.hide()
        if self.yaxisScale.currentIndex() == 1:
            self.frameYMinMax.show()
        elif self.xaxisScale.currentIndex()==0:
            self.frameYMinMax.hide()


    def Recorder(self):
        print("Recorder")
        res = QWidget()
        
        layout = QVBoxLayout()
        self.recorderGraph = pg.PlotWidget()
        self.recorderGraph.setLabel('left', "<span style=\"color:white;font-size:10px\">Temperature (°C)</span>")
        #self.recorderGraph.setLabel('right', "<span style=\"color:white;font-size:10px\">Current (mA)</span>")
        self.recorderGraph.setLabel('bottom', "<span style=\"color:white;font-size:10px\">Time (s)</span>")
        layout.addWidget(self.recorderGraph)
 
        
        hbox =QHBoxLayout()
        hbox.addWidget(QLabel("X AxisScale"))
        self.xaxisScale = QComboBox()
        self.xaxisScale.addItems(["variabel","fixed", ])
        self.xaxisScale.currentIndexChanged.connect(self.fixedUpdate)
        hbox.addWidget(self.xaxisScale)
        hbox.addWidget(QLabel("Y AxisScale"))
        self.yaxisScale = QComboBox()
        self.yaxisScale.addItems(["variabel","fixed", ])
        self.yaxisScale.currentIndexChanged.connect(self.fixedUpdate)
        hbox.addWidget(self.yaxisScale)
        self.showGen1CB = QCheckBox('generic1', self)
        self.showGen1CB.setChecked(True)
        self.showGen1CB.setStyleSheet("background-color:white")
        self.showGen1CB.stateChanged.connect(self.updatecb)
        hbox.addWidget(self.showGen1CB)
        self.showGen2CB = QCheckBox('generic2', self)
        self.showGen2CB.setChecked(True)
        self.showGen2CB.setStyleSheet("background-color:white")
        self.showGen2CB.stateChanged.connect(self.updatecb)
        hbox.addWidget(self.showGen2CB) 
        
        layout.addLayout(hbox)

        
        onlyUInt = QIntValidator( 1, 65535, self)
        self.frameXMinMax = QFrame()
        hbox =QHBoxLayout()

        self.minLabel =QLabel("Showed minimal time")
        hbox.addWidget(self.minLabel)
        self.minTime = QLineEdit()
        self.minTime.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        self.minTime.setText("0")
        self.minTime.setValidator(onlyUInt)
        hbox.addWidget(self.minTime)
        
        self.maxLabel =QLabel("Showed maximal time")
        hbox.addWidget(self.maxLabel)
        self.maxTime = QLineEdit()
        self.maxTime.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        self.maxTime.setText("0")
        self.maxTime.setValidator(onlyUInt)
        hbox.addWidget(self.maxTime)
        self.frameXMinMax.setLayout(hbox)
        layout.addWidget(self.frameXMinMax)

        self.frameYMinMax = QFrame()
        hbox =QHBoxLayout()
        self.minyLabel =QLabel("Showed minimal Y Axis")
        hbox.addWidget(self.minyLabel)
        self.miny = QLineEdit()
        self.miny.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        self.miny.setText("0")
        self.miny.setValidator(onlyUInt)
        hbox.addWidget(self.miny)
        
        self.maxyLabel =QLabel("Showed maximal Y Axis")
        hbox.addWidget(self.maxyLabel)
        self.maxy= QLineEdit()
        self.maxy.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        self.maxy.setText("0")
        self.maxy.setValidator(onlyUInt)
        hbox.addWidget(self.maxy)
        self.frameYMinMax.setLayout(hbox)
        layout.addWidget(self.frameYMinMax)
        
        self.fixedUpdate()
        
        
        hbox =QHBoxLayout()
        icons = [["Start", self.doStart, False], ["Stop", self.doStop, False], ["Clear", self.doClear, False], ["Save", self.doSave, False]]
        for name, fn, show  in icons:
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
            print("Add %s button"% name)
        layout.addLayout(hbox)


        
        hbox =QHBoxLayout()
        self.setSampleInterval_ms = 200
        self.captureTime_s = 1
        onlyInt0_1000 = QIntValidator( 1, 1000, self)
        
        siLabel = QLabel("Sample interval")
        
        self.sIntVal_edit = QLineEdit()
        self.sIntVal_edit.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        self.sIntVal_edit.setText("1")
        self.sIntVal_edit.setValidator(onlyInt0_1000)
        siLabel.setBuddy(self.sIntVal_edit)
        hbox.addWidget(siLabel)
        hbox.addWidget(self.sIntVal_edit)
        
        self.sampleUnit = QComboBox()
        self.sampleUnit.addItems(["s","ms"])
        hbox.addWidget(self.sampleUnit)
        duration = QLabel("Capture Time")
        self.captime_edit = QLineEdit()
        self.captime_edit.setText("1")
        self.captime_edit.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
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
        self.progressBar.resize(300,100)
        hbox.addWidget(self.progressBar)
        layout.addLayout(hbox)
               
        self.frame1 = QFrame()
        self.frame1.setStyleSheet("QFrame {background-color: rgb(255, 255, 255);"
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
        self._actmax1 = QLabel("%.2f" %120)
        gLayout.addWidget(self._actmax1, 0, 7)
        self.pUnit = QLabel("°C")
        gLayout.addWidget(self.pUnit, 0, 8)

        
        label = QLabel("Rohwert")
        gLayout.addWidget(label, 1, 2)
        self._actRawVal1 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actRawVal1, 1, 3)
        label = QLabel("Min:")
        gLayout.addWidget(label, 1, 4)
        self._actRawMin1 = QLabel("%.2f" %0)
        gLayout.addWidget(self._actRawMin1, 1, 5)
        label = QLabel("Max:")
        gLayout.addWidget(label, 1, 6)
        self._actRawMax1 = QLabel("%.2f" %120)
        gLayout.addWidget(self._actRawMax1, 1, 7)
        self.rawUnit = QLabel("mA")
        gLayout.addWidget(self.rawUnit, 1, 8)
        self.frame1.setLayout(gLayout)
        #self.frame1.hide()
        layout.addWidget(self.frame1)
        
        self.frame2 = QFrame()
        self.frame2.setStyleSheet("QFrame {background-color: rgb(255, 255, 255);"
                                "border-width: 1;"
                                "border-radius: 3;"
                                "border-style: solid;"
                                "border-color: rgb(0, 0, 0)}"
                                )
        self.frame2.setFrameShape(QFrame.StyledPanel)
        self.frame2.setLineWidth(3)
        #frame1.setStyleSheet("background-color: blue")
        #frame1.setFrameStyle(QFrame.VLine|QFrame.Sunken)
        
        gLayout = QGridLayout()
        
        self.gen2Label = QLabel("generic2")
        gLayout.addWidget(self.gen2Label, 0, 0)
        #gLayout.addWidget(self.conState, 0, 1)
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
        self._actmax2 = QLabel("%.2f" %120)
        gLayout.addWidget(self._actmax2, 0, 7)
        self.pUnit = QLabel("°C")
        gLayout.addWidget(self.pUnit, 0, 8)

        
        label = QLabel("Rohwert")
        gLayout.addWidget(label, 1, 2)
        self._actRawVal2 = QLabel("%.2f" % 0)
        gLayout.addWidget(self._actRawVal2, 1, 3)
        label = QLabel("Min:")
        gLayout.addWidget(label, 1, 4)
        self._actRawMin2 = QLabel("%.2f" %0)
        gLayout.addWidget(self._actRawMin2, 1, 5)
        label = QLabel("Max:")
        gLayout.addWidget(label, 1, 6)
        self._actRawMax2 = QLabel("%.2f" %120)
        gLayout.addWidget(self._actRawMax2, 1, 7)
        self.rawUnit = QLabel("mA")
        gLayout.addWidget(self.rawUnit, 1, 8)
        self.frame2.setLayout(gLayout)
        #self.frame2.hide()
        layout.addWidget(self.frame2)

        
        
        hbox =QHBoxLayout()
        
        hbox.addWidget(QLabel("File name"))
        self.QFilename = QLineEdit()
        print("Line edit %s" % self.QFilename)
        self.QFilename.setText("")
        
        hbox.addWidget(self.QFilename)
        hbox.addWidget(QLabel("Plot name"))
        self.QPlotname = QLineEdit()
        self.QPlotname.setText("")
        hbox.addWidget(self.QPlotname)

        layout.addLayout(hbox)
        
               
        self.onTimingChanged()
        layout.addLayout(hbox)
 
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
        print("Set plotname to %s" %(self.plotname))
    
    def recorderFileNameChanged(self):
        print("Recorder file channge %s" %( self.QFilename.text()))


    def Emulator(self):
        print("Emulator")
        res = QWidget()
        layout =QVBoxLayout()
        self.emulatorGraph = pg.PlotWidget()
        self.emulatorGraph.setLabel('left', "<span style=\"color:white;font-size:10px\">Temperature (°C)</span>")
        self.emulatorGraph.setLabel('bottom', "<span style=\"color:white;font-size:10px\">Time (s)</span>")
        layout.addWidget(self.emulatorGraph)
        
        
        hbox =QHBoxLayout()
        self.showeGen1 = QCheckBox('Show generic1', self)
        self.showeGen1.stateChanged.connect(self.updatePlots)
        self.showeGen1.setChecked(True)
        self.showeGen1.setStyleSheet("color: rgb(255, 0, 0);")
        
        hbox.addWidget(self.showeGen1)
        self.showeGen2 = QCheckBox('Show generic2', self)
        self.showeGen2.setChecked(True)
        self.showeGen2.stateChanged.connect(self.updatePlots)
        self.showeGen2.setStyleSheet("color: rgb(0, 255, 0);")
        hbox.addWidget(self.showeGen2) 
        layout.addLayout(hbox)
        
        gLayout = QGridLayout()
        label = QLabel("Aktueller Wert")
        gLayout.addWidget(label, 0, 0)
        self._acteVal = QLabel("%.2f" % 0)
        gLayout.addWidget(self._acteVal, 0, 1)
        label = QLabel("Min:")
        gLayout.addWidget(label, 0, 2)
        self._acetmin = QLabel("%.2f" % 0)
        gLayout.addWidget(self._acetmin, 0, 3)
        label = QLabel("Max:")
        gLayout.addWidget(label, 0, 4)
        self._actemax = QLabel("%.2f" %120)
        gLayout.addWidget(self._actemax, 0, 5)
        self.peUnit = QLabel("°C")
        gLayout.addWidget(self.peUnit, 0, 6)
        
        label = QLabel("Aktueller Rohwert")
        gLayout.addWidget(label, 1, 0)
        self._acteRawVal = QLabel("%.2f" % 0)
        gLayout.addWidget(self._acteRawVal, 1, 1)
        label = QLabel("Min:")
        gLayout.addWidget(label, 1, 2)
        self._acteRawMin = QLabel("%.2f" %0)
        gLayout.addWidget(self._acteRawMin, 1, 3)
        label = QLabel("Max:")
        gLayout.addWidget(label, 1, 4)
        self._acteRawMax = QLabel("%.2f" %120)
        gLayout.addWidget(self._acteRawMax, 1, 5)
        self.raweUnit = QLabel("mA")
        gLayout.addWidget(self.raweUnit, 1, 6)
        layout.addLayout(gLayout)
        
        res.setLayout(layout)   
        if self.emData is not None:
            self.setNewData()
            self.updatePlots()
        return res

    def append_data(self, data):
       if self.doRecord:
           if data[0] is None:
                print("Finished capturing (%d, %d)" % (len(self.rawdata), len(self.rawdata[0])))
                self.setNewData()
                self.updatePlots()
                self.stopCapture()
           else:
                self.rawdata.append(data)
                pData = [data[0], data[1]]
                self.onGoing = self.onGoing and (not (isnan(data[3])))
                #print("onGoing %s; data %f is nan: %s" % (self.onGoing, data[3], isnan(data[3]) ) )
                print(data[3],data[3])
                if not self.onGoing:
                    print("Detected connection loss")
                    self.sensor = None
                pData.extend( self.r2p[data[2]]( data[3], data[4]))
                if len(data)>5:
                    pData.extend( self.r2p[data[5]](data[6], data[7]) )
                if len(self.pData)== 0:
                    self.pData[data[2]] = []
                    if len(data)>5:
                        self.pData[data[5]] = []
                self.pData[data[2]].append(([pData[0], pData[1], pData[2], pData[3] ]))
                if len(data)>5:
                    self.pData[data[5]].append(([pData[0], pData[1], pData[4], pData[5] ]))
                self.csvFile.writerow(pData)
                print("Data %d/%d (size=%d) %s appended." % (len(self.rawdata), self.capture_size, len(pData), pData))
                if len(self.rawdata)%20 == 0:
                    self.setNewData()
                    self.updatePlots()

    def file_open(self):
        local_dir = (os.path.dirname(self.filename)
               if self.filename is not None else ".")
        fmt =  ["CSV Files (*.csv)", "Excel Files (*.xslc)"]
        files = QFileDialog.getOpenFileName(self,
                "Load data", local_dir,
                fmt[0])
        if files:
            self.emulatorFile = files[0]
            self.load_file(self.emulatorFile)

    def load_file(self, fname):
        f = open(fname, encoding="cp1252")
        csvf =csv.reader(f, lineterminator="\n")
        datal=[]
        self.emUnit = []
        for idx, line in enumerate(csvf):
            time = line[0]
            relTime= float(line[1])
            val1 = float(line[2])
            self.emUnit.append(line[3])
            val2 = float(line[4])
            self.emUnit.append(line[5])
            datal.append([time, relTime, val1, self.emUnit[0], val2, self.emUnit[1]])
        f.close()
        self.emData = np.zeros([idx+1,3])
        print("Create numpy array of length %d" % (idx))
        self.emUnit= []
        print("Load file %s :"% (fname))
        for idx, line in enumerate(datal):
            self.emData[idx][0]  = float(line[1])
            self.emData[idx][1]  = float(line[2])
            self.emData[idx][2]  = float(line[4])
        print("Set emData to \n%s" %(self.emData))
        self.emFile = fname
        print("Set emulator file name to %s" %self.emFile)
        self.setNewData()
        self.updatePlots()

    def capture(self):
         # Start Yoctopuce I/O task in a separate thread
         self.yoctoThread = QThread()
         self.yoctoThread.start()
         self.yoctoTask = YoctopuceTask()
         self.yoctoTask.statusMsg.connect(self.showMsg)
         self.yoctoTask.arrival.connect(self.arrival)
         self.yoctoTask.newValue.connect(self.newValue)
         self.yoctoTask.removal.connect(self.removal)
         self.yoctoTask.moveToThread(self.yoctoThread)
         self.yoctoTask.updateSignal.connect(self.append_data)
         self.yoctoTask.startTask.emit()

    @property
    def connected(self):
        return self.sensor != None


    @pyqtSlot(dict)
    def arrival(self, device):
        if self.sensor is None:
            # log arrival
            print("Device connected in Datarecorder (connected %s, onGoing %s)" % ( self.connected,self.onGoing))
            self.sensor = device
            if not self.onGoing:
                self.onGoing = True
                print("Show old buttons")
            else:
                print("Show buttons in arrival")
                self.btnState["Start"] = True
                self.btnState["Stop"] = False
                self.btnState["Clear"] = False
                self.btnState["Save"] = False

            if  self.btnState["Start"]:
                 self.btn["Start"].show()
            else:
                self.btn["Start"].hide()
            if  self.btnState["Stop"]:
                 self.btn["Stop"].show()
            else:
                self.btn["Stop"].hide()

            if self.btnState["Save"]:
                self.btn["Save"].show()
            else:
                self.btn["Save"].hide()
            print("Registered Sensors")
        else:
            print("%d Sensors are already connected" %len(self.sensor))
        self.updateConnected()

    @pyqtSlot(dict)
    def removal(self, device):
        # log removal
        if not self.onGoing:
            self.btnState["Start"] = True
            self.btnState["Stop"] = False
            self.btnState["Clear"] = False
            self.btnState["Save"] = False
        else:
            print("Detected onGoing in removal")

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

        self.sensor = None

        print('Device disconnected:', device)
        self.updateConnected()

    @pyqtSlot(str, str)
    def newValue(self, value1, value2, value3):
        print('newValue function called')
        # if hardwareId not in self.functionValues:
        #     # create a new label when first value arrives
        #     newLabel = QLabel(self)
        #     self.layout.addWidget(newLabel)
        #     self.functionValues[hardwareId] = newLabel
        # # then update it for each reported value
        # self.functionValues[hardwareId].setText(hardwareId + ": " + value)

    def updateConnected(self):
        print("Update connected to %s" % self.connected)
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



    def doStart(self):
        print("doStart")
        self.doRecord = True
        self.onTimingChanged()
        self.yoctoTask.startTask.emit()
        print("Show buttons in doStart/Task is %s" % (self.yoctoTask))
        self.btnState["Start"] = False
        self.btnState["Stop"] = True
        self.btnState["Clear"] = False
        self.btnState["Save"] = False
        self.btn["Start"].hide()
        self.btn["Stop"].show()
        self.btn["Clear"].hide()
        self.btn["Save"].hide()
        if self.yoctoTask is None:
            print("No sensor connected")
        if self.yoctoTask.capture_start():
            self.onGoing = True
            now = datetime.now()
            nowS = now.strftime("%Y%m%d_%H%M%S.csv")
            print("Set time to %s" %nowS)
            self.QFilename.setText(nowS)
            self.conf = configuration(self.yoctoTask)
            self.r2p = self.conf.getR2PFunction
            self.p2r = self.conf.getP2RFunction()
            self.filename = nowS
            self.rFile = open(nowS, "w")
            self.csvFile= csv.writer(self.rFile, lineterminator="\n")
            self.doRecord = True
            print("Start record on %s" %self.yoctoTask.startTask)
            self.setNewData()
            self.updatePlots()


    def stopCapture(self):
        print("Stop recording")
        self.doRecord = False

        self.yoctoTask.capture_stop()
        print("Show buttons in stopCapture")

        self.rFile.close()
        self.btnState["Start"] = False
        self.btnState["Stop"] = False
        self.btnState["Clear"] = True
        self.btnState["Save"] = True

        self.btn["Start"].hide()
        self.btn["Stop"].hide()
        self.btn["Clear"].show()
        self.btn["Save"].show()

    def doStop(self):
        print("doStop")

        # Ask for really Stop
        dlg =  StopRecordingDlg(self)
        res = dlg.exec_()
        print("Yoctopuc Task is %s" % self.yoctoTask)
        if dlg:
            state = dlg.state()
            print("Returned by dlg: %d " % state)
            if state:
                self.yoctoTask.capture_stop()
                print("Yoctopuc Task stop" )

                self.rFile.close()
                print("Show buttons in doStop")
                self.btnState["Start"] = False
                self.btnState["Stop"] = False
                self.btnState["Clear"] = True
                self.btnState["Save"] = True

                self.btn["Start"].hide()
                self.btn["Stop"].hide()
                self.btn["Clear"].show()
                self.btn["Save"].show()
                self.yoctoTask.stopTask.emit()
                self.doRecord = False
            else:
                print("Continue recording")

    def doClear(self):
        print("doClear")
        self.recorderGraph.clear()
        print("Show butons in doClear")
        self.btnState["Start"] = True
        self.btnState["Stop"] = False
        self.btnState["Clear"] = False
        self.btnState["Save"] = False

        self.btn["Stop"].hide()
        self.btn["Clear"].hide()
        self.btn["Save"].hide()
        self.btn["Start"].show()
        self.progressBar.setValue(0)
        self.pData = None
        self.rawdata= []
        self.sensor = None

    def doSave(self):
         if self.pData is None:
             print("No data captured")
             return
         fmt =  ["CSV Files (*.csv)", "Excel Files (*.xslc)"]

         fname, ftype = QFileDialog.getSaveFileName(self, "Store captured data",
                 self.QFilename.text(), fmt[0])
         if fname is None:
             fname = self.QFilename.text()
         print("doSave  all %s of size %d" % (fname, self.pDataSize))
         f = open( fname,"w", encoding="cp1252")
         csvf =csv.writer(f, lineterminator="\n")
         for i in range(self.pDataSize):
             data = [self.rawdata[i][0], self.pData['generic1'][i][0], self.pData['generic1'][i][1], self.pData['generic1'][i][2]]
             data.extend([ self.pData['generic2'][i][1],  self.pData['generic2'][i][2] ])
             print(data)
             csvf.writerow(data)
         self.dirty = False
         f.close()

    def help_about(self):
        dlg = QMessageBox()
        dlg.setWindowTitle("Datarecorder")
        dlg.setText("This is a datalogger application")
        button = dlg.exec_()
        print(button)
        if button == QMessageBox.Ok:
            print("OK")


    @pyqtSlot(str)
    def showMsg(self, text, time = 5000):
        self.message.showMessage(text, time)

    def onTimingChanged(self):
        if not self.doRecord:
            print("Call onSampleIntvalChanged %s" % ( self.sampleUnit.currentIndex()))
            if self.sampleUnit.currentIndex():
                print("Sample interval 1")
                self.setSampleInterval_ms =1
            else:
                print("Sample interval 1000")
                self.setSampleInterval_ms =1000
            sInt =  1 if self.sIntVal_edit.text() == None else self.sIntVal_edit.text()
            print("Sample Int str \"%s\"" % sInt)
            self.setSampleInterval_ms *= int(sInt)
            if self.yoctoTask is not None:
                self.yoctoTask.setSampleInterval_ms(self.setSampleInterval_ms)
            print("Sample intervall is %d ms" % self.setSampleInterval_ms)
            print("Call onSampleIntvalChanged %s" % (self.sampcapDur.currentIndex() ))
            if self.sampcapDur.currentIndex()==0:
                print("s")
                self.captureTime_s = 1
            elif self.sampcapDur.currentIndex()==1:
                print("min")
                self.captureTime_s = 60
            else:
                print("h")
                self.captureTime_s = 3600
            capTime = 1 if self.captime_edit.text() == None else self.captime_edit.text()
            self.captureTime_s *= int(capTime)
            self.capture_size = ceil(float(1000*self.captureTime_s)/(float(self.setSampleInterval_ms)))
            print("Set capture time %d s; Size: is %d samples; Interval @ %f ms" % ( self.captureTime_s, self.capture_size ,self.setSampleInterval_ms))
            if self.yoctoTask is not None:
                self.yoctoTask.set_capture_size(self.capture_size)
            print("Capture time is %d s/Size %d" % (self.captureTime_s, self.capture_size))
        else:
            print("Sample in progress: Can not update timing")


    def tabChanged(self, index):
        self.setNewData()
        self.updatePlots()
        print("Tab changed %d" %(index))

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

    @property
    def pDataSize(self):
        if self.pData is not None and len(self.pData['generic1'])>0:
            return  len(self.pData['generic1'])
        else:
            return 0

    def setNewData(self):
        if self.pData is None:
            print("Set up new generic data1/2")
            self.pData ={}
            self.pData['generic1'] = []
            self.pData['generic2'] = []
            self.data1 = np.zeros([ self.pDataSize, 3])
            self.data2 = np.zeros([ self.pDataSize, 3])
            self.unit = ["", ""]
            return
        if self.pDataSize > 0 :
            print("Set new data of size pData %d" %(self.pDataSize))
            self.data1 = np.zeros([ self.pDataSize, 3])
            self.data2 = np.zeros([ self.pDataSize, 3])
            for i in range(self.pDataSize):
                self.data1[i][0] = float(self.pData["generic1"][i][1])
                self.data1[i][1] = float(self.pData["generic1"][i][2])
                self.data1[i][2] = float(self.rawdata[i][6])
                self.data2[i][0] = float(self.pData["generic2"][i][1])
                self.data2[i][1] = float(self.pData["generic2"][i][2])
                self.data2[i][2] = float(self.rawdata[i][3])
                self.rawunit = self.rawdata[i][7]
                self.punit =  self.pData['generic1'][i][3]
        if self.emData is not None:
            self.emdata = np.zeros([ len(self.emData), 3])
            for i in range(len(self.emData)):
                self.emdata[i][0] = float(self.emData[i][0])
                self.emdata[i][1] = float(self.emData[i][1])
                self.emdata[i][2] = float(self.emData[i][2])


    def updatePlots(self):
        if (self.data1 is None) or (self.data2 is None):
            print("Skip plot as there is no data")
            return
        if self.pDataSize >0:
            x = self.data1[:, 0]
            self.recorderGraph.clear()
            if self.showGen1CB.isChecked():
                self.gen1Label.setText("generic1")
                g1 = self.data1[:, 1]
                g1Pure = g1[np.logical_not( np.isnan(g1))]
                g1Raw = self.data1[:, 2]
                g1RawPure = g1Raw[np.logical_not( np.isnan(g1Raw))]
                g1min = g1RawPure.min()
                g1max = g1Pure.max()
                g1Rawmin = g1RawPure.min()
                g1Rawmax = g1RawPure.max()
                g1Raw = self.data1[:, 2]
                self._actVal1.setText("%.2f" % g1Pure[-1])
                self._actmin1.setText("%.2f" % g1min)
                self._actmax1.setText("%.2f" % g1max)
                self._actRawVal1.setText("%.2f" % g1Raw[-1])
                self._actRawMin1.setText("%.2f" % g1Rawmin)
                self._actRawMax1.setText("%.2f" % g1Rawmax)
                self.recorderGraph.plot(x, g1, name="generic1", pen=pg.mkPen("green"))
            else:
                self.frame1.hide()

            if self.showGen2CB.isChecked():
                self.gen2Label.setText("generic2")
                g2 = self.data2[:, 1]
                g2Pure = g2[np.logical_not( np.isnan(g2))]
                g2Raw = self.data2[:, 2]
                g2RawPure = g2Raw[np.logical_not( np.isnan(g2Raw))]

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
            progress = 100.0*len(self.rawdata)/float(self.capture_size)
            print("Progress %.1f of %d " % (progress, self.capture_size))
            self.progressBar.setValue(int(progress))
            self.recorderGraph.setTitle(self.QPlotname.text())
            self.recorderGraph.addLegend()

        if self.emdata is not None:
            if self.emFile is None:
                fname = ""
            else:
                fname =self.emFile.split("/")[-1]
            x = self.emdata[:,0]
            y1 = self.emdata[:,1]
            y2 = self.emdata[:,2]
            self.emulatorGraph.clear()
            self.emulatorGraph.addLegend()
            if self.showeGen1.checkState():
                p1 = self.emulatorGraph.plot(x,y1, name="generic1", pen=pg.mkPen("red"))
                self.emulatorGraph.setTitle()
            if self.showeGen2.checkState():
                p2 = self.emulatorGraph.plot(x,y2, name="generic2",pen=pg.mkPen("green"))
            self.emulatorGraph.setTitle(self.emFile.split("/")[-1])
        else:
            print("Skip as emData size of %d" % (len(self.emData)))

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
        
    
