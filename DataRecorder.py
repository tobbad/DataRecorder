# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse
import csv
from math import ceil
import numpy as np
from datetime import *
import numpy as np
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
    QFrame
)
from PyQt5.QtGui import (
    QIcon, 
    QKeySequence, 
    QPixmap, 
    QColor, 
    QPalette,
    QIntValidator
)

from PyQt5.QtCore import *
import pyqtgraph as pg
#import mkl
import qrc_resources
wd = os.sep.join(["C:","Users","tobias.badertscher","source", "repos", "python", "DataRecorder"])

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

def currThread():
    return '[thread-' + str(int(QThread.currentThreadId())) + ']'

#print("PYTHONPATH:", os.environ.get('PYTHONPATH'))
#print("PATH:", os.environ.get('PATH'))

class SensorDisplay(QMainWindow):
    def __init__(self):
        print("Create app")
        super().__init__()
        self.dirty = False
        self.filename = "./"
        self.data = None
        self.btn = {}
        self.doRecord = False
        self.sampleIntervall_ms = 0
        self.capture_size = 0
        self.sampleIntervall_ms =1
        self.captureTime_s = 1
        self.rawData = []        
        self.unit  =[]
        self.functionValues = {}
        self.yoctoTask = None
        self.emData = None
        self.setUpGUI()
        
    def setUpGUI(self):    
        self.setWindowTitle("DataRecorder")
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
        tabWidget.addTab(self.Emulator(), "Proberecorder")
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


    def Recorder(self):
        print("Recorder")
        res = QWidget()
        
        layout = QVBoxLayout()
        self.recorderGraph = pg.PlotWidget()
        self.recorderGraph.setLabel('left', "<span style=\"color:white;font-size:10px\">Temperature (°C)</span>")
        self.recorderGraph.setLabel('bottom', "<span style=\"color:white;font-size:10px\">Time (s)</span>")
        layout.addWidget(self.recorderGraph)
        
        hbox =QHBoxLayout()
        icons = [["Start", self.doStart], ["Stop", self.doStop], ["Clear", self.doClear], ["Save", self.doSave]]
        for name, fn  in icons:
            self.btn[name] = QPushButton(name)
            icon = QIcon(":/%s.svg" % name.lower())
            self.btn[name].setIcon(icon)
            self.btn[name].clicked.connect(fn)
            self.btn[name].show()
            hbox.addWidget(self.btn[name])
            print("Add %s button"% name)
        layout.addLayout(hbox)
        
        hbox =QHBoxLayout()
        self.sampleIntervall_ms = 200
        self.captureTime_s = 1
        onlyInt0_1000 = QIntValidator( 1, 999, self)
        
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
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.resize(300,100)
        hbox.addWidget(self.progressBar)
        layout.addLayout(hbox)
               
        hbox =QHBoxLayout()
        hbox.addWidget(QLabel("Plot name"))
        self.fNameQL = QLineEdit()
        hbox.addWidget(self.fNameQL)

        hbox =QHBoxLayout()
        hbox.addWidget(QLabel("Aktueller Wert (°C)"))
        self._actVal = QLabel("%.2f" % 0)
        hbox.addWidget(self._actVal)
        hbox.addWidget(QLabel("Min:"))
        self._min = QLabel("%.2f" %0)
        hbox.addWidget(self._min)
        hbox.addWidget(QLabel("Max:"))
        self._max = QLabel("%.2f" %120)
        hbox.addWidget(self._max)
        layout.addLayout(hbox)
        
        hbox =QHBoxLayout()
        hbox.addWidget(QLabel("Aktueller Rohwert (mA)"))
        self._actMeasVal = QLabel("%.2f" % 0)
        hbox.addWidget(self._actVal)
        hbox.addWidget(QLabel("Min:"))
        self._min = QLabel("%.2f" %0)
        hbox.addWidget(self._min)
        hbox.addWidget(QLabel("Max:"))
        self._max = QLabel("%.2f" %20)
        hbox.addWidget(self._max)
        layout.addLayout(hbox)
               
        self.set_capture_size()
        layout.addLayout(hbox)
 
        res.setLayout(layout)
        self.sIntVal_edit.textChanged.connect(self.onTimingChanged)
        self.captime_edit.textChanged.connect(self.onTimingChanged)
        self.sampleUnit.currentIndexChanged.connect(self.onTimingChanged)
        self.sampcapDur.currentIndexChanged.connect(self.onTimingChanged)

        print("Recorder created")
        return res


    def Emulator(self):
        print("Emulator")
        res = QWidget()
        layout = QGridLayout()
        self.emulatorGraph = pg.PlotWidget()
        layout.addWidget(self.emulatorGraph)
        res.setLayout(layout)   
        if self.emData is not None:
            self.setNewData()
            self.updatePlots()
        return res

    def append_data(self, data):
        self.dirty = True
        if data[0] is None:
            print("Finished capturing (%d, %d)" % (len(self.rawData), len(self.rawData[0])))
            self.setNewData()
            self.updatePlots()
            self.doStop()
            self.yoctoTask.capture_stop()
            self.yoctoTask = None
        else:
            print("Data %s appended." % (data))
            self.rawData.append(data)
       
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
        #print(self.data)
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
         
    @pyqtSlot(dict)
    def arrival(self, device):
        # log arrival
        print('Device connected:', device, currThread())
        # for relay functions, create a toggle button
               
    @pyqtSlot(str, str)
    def newValue(self, value1, value2, value3):
        print(value1, value2, value3)
        # if hardwareId not in self.functionValues:
        #     # create a new label when first value arrives
        #     newLabel = QLabel(self)
        #     self.layout.addWidget(newLabel)
        #     self.functionValues[hardwareId] = newLabel
        # # then update it for each reported value
        # self.functionValues[hardwareId].setText(hardwareId + ": " + value)

    @pyqtSlot(dict)
    def removal(self, device):
        # log arrival
        print('Device disconnected:', device, currThread())
        # mark all reported values as disconnected
        for functionId in device['functions']:
            hardwareId = device['serial'] + '.' + functionId
            if hardwareId in self.functionValues:
                self.functionValues[hardwareId].setText(hardwareId + ": disconnected")
              
    def doStart(self):
        now = datetime.now()
        nowS = now.strftime("%Y%m%d_%H%M%S.csv")
        self.filename = nowS
        self.fNameQL.setText(nowS)
        self.storeFName = nowS
        print("Set time to %s" %nowS)
        self.yoctoTask.capture_start()
        self.doRecord = True
        self.btn["Start"].hide()
        self.btn["Stop"].show()
        print("Start record")
        
    def doStop(self):
        self.doRecord = False
        print("Stop recording")
        self.btn["Start"].show()

    def doClear(self):
        print("doClear")
        self.rawData= []
     
    def doSave(self):
         if self.data is None:
             print("No data captured")
             return
         fmt =  ["CSV Files (*.csv)", "Excel Files (*.xslc)"]
         
         fname, ftype = QFileDialog.getSaveFileName(self, "Store captured data",
                 self.storeFName, fmt[0])
         print("doSave  all %s of size %d\n%s" % (fname, self.dataSize, self.data))
         self.cFileName = fname
         f = open( self.cFileName,"w", encoding="cp1252")
         csvf =csv.writer(f, lineterminator="\n")
         for i in range(self.dataSize):
             csvf.writerow([self.data[i][0], self.data[i][1], self.data[i][2]])
         self.dirty = False
         f.close()
        
    def help_about(self):
        print("About")

    @pyqtSlot(str)
    def showMsg(self, text, time = 5000):
        self.message.showMessage(text, time)
    
    def onTimingChanged(self):
        print("Call onSampleIntvalChanged %s" % ( self.sampleUnit.currentIndex()))
        if self.sampleUnit.currentIndex()==0:
            self.sampleIntervall_ms =1000
        else:
            self.sampleIntervall_ms =1
        sInt =  1 if self.sIntVal_edit.text() == None else self.sIntVal_edit.text()
        print("Sample Int str \"%s\"" % sInt)
        self.sampleIntervall_ms *= int(sInt)
        self.yoctoTask.setSampleInterval_ms(self.sampleIntervall_ms)
        print("Sample intervall is %d ms" % self.sampleIntervall_ms)
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
        print("Set capture time to \"%s\"" % (capTime))
        self.captureTime_s *= int(capTime)
        print("Capture time is %d s" % self.captureTime_s)
        self.set_capture_size()

    def set_capture_size(self):
        self.capture_size =  int(ceil(self.captureTime_s*1000/self.sampleIntervall_ms))
        self.showMsg("Capture size %d" % self.capture_size)   
        if self.yoctoTask is not None:
            self.yoctoTask.set_capture_size(self.capture_size)
        print("Capture size is now %d: captureTime %d s, sampleInterval %d ms" % (self.capture_size, self.captureTime_s, self.sampleIntervall_ms))
       
    def tabChanged(self, index):
        self.setNewData()
        
        self.updatePlots()
        print("Tab changed %d" %(index))
    
    @property
    def rawDataSize(self):
        return  len(self.rawData)

    def setNewData(self):
        print("Set new data of size %d/%d" %( self.rawDataSize, len(self.emData)))
        if len(self.rawData) > 0 :
            self.data = np.zeros([ self.rawDataSize, 3])
            for i in range(self.rawDataSize):
                self.data[i][0] = float(self.rawData[i][1])
                self.data[i][1] = float(self.rawData[i][2])
                self.data[i][2] = float(self.rawData[i][4])
        if self.emData is not None:
            print("Show emulator data")
            self.emdata = np.zeros([ len(self.emData), 3])
            for i in range(len(self.emData)):
                self.emdata[i][0] = float(self.emData[i][0])
                self.emdata[i][1] = float(self.emData[i][1])
                self.emdata[i][2] = float(self.emData[i][2])
            print(self.emdata)
            
    def updatePlots(self):
        print("Updat plots on \n%s  and \n %s " %( self.data, self.emData))
        if self.data is not None:
            x = self.data[:,0]
            y = self.data[:,1]
            minimum = y.min()
            maximum = y.max()
            self._actVal.setText("%.2f" % y[0])
            self._min.setText("%.2f" % minimum)
            self._max.setText("%.2f" % maximum)
            self.recorderGraph.setTitle(self.filename.split("/")[-1])
        if self.emdata is not None:
            print("Plot emulator data %s" % self.emFile.split("/")[-1])
            x = self.emdata[:,0]
            y = self.emdata[:,1]
            self.emulatorGraph.plot(x,y)
            self.emulatorGraph.setTitle(self.emFile.split("/")[-1])
     



        





if __name__ == "__main__":
    # #print("Initalize class")
    # app  = QApplication(sys.argv)
    # window = App()
    # translator = QTranslator(app)

    # defaultLocale = QLocale.system().name()
    # translator.load(defaultLocale)
    # app.installTranslator(translator)
    # print(defaultLocale)
    # window.show()
    app = QApplication(sys.argv)
    window = SensorDisplay()
    window.capture()
    window.show()
    sys.exit(app.exec())
        
    
