# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse
import csv
from math import *
import numpy as np
from datetime import *
import numpy as np
from sensors import sensors


sys.path.append(os.sep.join(["C:","Users","tobias.badertscher","AppData","Local","miniconda3","Lib","site-packages"]))
from PyQt5.QtWidgets import QFileDialog, QWidget, QMainWindow, QApplication, QAction, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtWidgets import QLabel, QSpinBox, QComboBox, QProgressBar, QLineEdit, QGridLayout, QFrame
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QColor, QPalette
from PyQt5.QtCore import *
import pyqtgraph as pg
#import mkl
import qrc_resources
wd = os.sep.join(["C:","Users","tobias.badertscher","source", "repos", "python", "DataRecorder"])

#print("PYTHONPATH:", os.environ.get('PYTHONPATH'))
#print("PATH:", os.environ.get('PATH'))

class App(QMainWindow):
    def __init__(self):
        print("Create app")
        super().__init__()
        self.setWindowTitle("DataRecorder")
        self.status = self.statusBar()
        self._addMenuBar()
        self.dirty = False
        self.filename = "./"
        self.data = None
        self.btn = {}
        self.doRecord = False
        self.sensor = sensors()
        self.sensor.register_callback(self.append_data)
        self.doRecord = False
        self.sampleIntervall_ms = 0
        self.captureTime_s = 0
        self.capture_size = 0
        self.sampleIntervall_ms =1
        self.captureTime_s = 1
        self.mydata = []
        
        
        tabWidget = QTabWidget()
        # Add tab widget for Recorder an Emulator
        tabWidget.addTab(self.Recorder(), "Recorder")
        #tabWidget.addTab(self.Icons(), "Icons")
        tabWidget.addTab(self.Emulator(), "Proberecorder")
        tabWidget.currentChanged.connect(self.tabChanged)
        # Set the central widget of the Window.
        self.setCentralWidget(tabWidget)
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.status = self.statusBar()
        self.status.setSizeGripEnabled(False)
        self.status.addPermanentWidget(self.sizeLabel)
        self.set_status("Ready")
        # self.sampleUnit  = None
        # self.sampcapDur  = None


    def append_data(self, data):
        self.dirty = True
        print("Append data")
        if data is None:
            print(self.mydata)
            print("Finished capturing (%d, %d)" % (len(self.mydata), len(self.mydata[0])))
            print(self.mydata)
            self.updatePlots()
            self.sensor.capture_stop()
        else:
            print("Data %s append to\n %s" % (data, self.mydata))
            self.mydata.append([data[0], data[1]] )            
        
    def _addMenuBar(self):
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

    def file_open(self):
        if not self.okToContinue():
            return
        local_dir = (os.path.dirname(self.filename)
               if self.filename is not None else ".")
        fmt =  ["CSV Files (*.csv)", "Excel Files (*.xslc)"]
        files = QFileDialog.getOpenFileName(self,
                "Load data", local_dir,
                fmt[0])
        if files:
            self.load_file(files[0])
        
    def load_file(self, fname):
        f = open(fname, encoding="cp1252")
        csvf =csv.reader(f, lineterminator="\n")
        self.datal=[]
        for idx, line in enumerate(csvf):
            time = line[0]
            relTime= float(line[1])
            val1 = float(line[2])
            unit1 = line[3]
            val2 = float(line[4])
            unit2 = line[5]
            self.datal.append([time, relTime, val1, unit1, val2, unit2])
        f.close()
        self.data = np.zeros([idx+1,2])
        print("Create numpy array of length %d" % (idx))
        self.filename= fname
        print("Load file %s :"% (self.filename))
        for idx, line in enumerate(self.datal):
            self.data[idx][0]  = line[1]
            self.data[idx][1]  = line[2]
        #print(self.data)
        self.storeFName = self.filename
        self.updatePlots()
        
            
    def doStart(self):
        now = datetime.now()
        nowS = now.strftime("%Y%m%d_%H%M%S.csv")
        self.filename = nowS
        self.fNameQL.setText(nowS)
        self.storeFName = nowS
        print("Set time to %s" %nowS)
        self.doRecord = True
        if self.sampleIntervall_ms > 1000:
            sampInt = "%ds" % (self.sampleIntervall_ms/1000)
            self.sensor.capture_start(self.capture_size, sampInt)
        else:
            sampInt = "%d/s" % (1000/self.sampleIntervall_ms)
            print("%d ms %s" %(self.sampleIntervall_ms, sampInt))
            self.sensor.capture_start(self.capture_size, sampInt)
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
        self.mydata= None
     
    def doSave(self):
         if self.data is None:
             print("No data captured")
             return
         fmt =  ["CSV Files (*.csv)", "Excel Files (*.xslc)"]
         fname, ftype = QFileDialog.getSaveFileName(self, "Save File",
                 self.storeFName, fmt[0])
         print("doSave  all %s of size %d" % (fname, len(self.mydata)))
         f = open(fname,"w", encoding="cp1252")
         csvf =csv.writer(f, lineterminator="\n")
         for i in range(len(self.mydata)):
             csvf.writerow([self.mydata[0][i],self.mydata[1][i]])
         self.dirty = False
         f.close()
        
    def help_about(self):
        print("About")

         
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
        siLabel = QLabel("Sample interval")
        self.sampleIntervall_ms = 200
        self.captureTime_s = 1
        self.sIntVal = QSpinBox()
        self.sIntVal.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        self.sIntVal.setRange(1,1000)
        siLabel.setBuddy(self.sIntVal)
        hbox.addWidget(siLabel)
        hbox.addWidget(self.sIntVal)
        
        self.sampleUnit = QComboBox()
        self.sampleUnit.addItems(["s","ms"])
        hbox.addWidget(self.sampleUnit)
        print("sampleUnit created %s" % (type(self.sampleUnit)))
        duration = QLabel("Capture Time")
        self.captime = QSpinBox()
        self.captime.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        self.captime.setRange(1,1000)
        duration.setBuddy(self.captime)
        hbox.addWidget(duration)
        hbox.addWidget(self.captime)
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
        self.sIntVal.valueChanged.connect(self.onTimingChanged)
        self.captime.valueChanged.connect(self.onTimingChanged)
        self.sampleUnit.currentIndexChanged.connect(self.onTimingChanged)
        self.sampcapDur.currentIndexChanged.connect(self.onTimingChanged)

        print("Recorder created")
        return res
    
    def set_status(self, text, time=5000):
        self.status.showMessage(text, time)
    
    def onTimingChanged(self):
        print("Call onSampleIntvalChanged %s" % ( self.sampleUnit.currentIndex()))
        if self.sampleUnit.currentIndex()==0:
            self.sampleIntervall_ms =1000
        else:
            self.sampleIntervall_ms =1
        self.sampleIntervall_ms *= self.sIntVal.value()
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
        self.captureTime_s *= self.captime.value()
        print("Capture time is %d s" % self.captureTime_s)
        self.set_capture_size()

    def set_capture_size(self):
        self.capture_size =  int(ceil(self.captureTime_s*1000/self.sampleIntervall_ms))
        self.set_status("Capture size %d" % self.capture_size)   
        print("Capture size is now %d: captureTime %d s, sampleInterval %d ms" % (self.capture_size, self.captureTime_s, self.sampleIntervall_ms))
       
    

    def Icons(self):
        print("Icon")
        res = QWidget()
        icons = sorted([attr for attr in dir(QStyle) if attr.startswith("SP_")])
        layout = QGridLayout()

        for n, name in enumerate(icons):
            btn = QPushButton(name)

            pixmapi = getattr(QStyle.StandardPixmap, name)
            icon = self.style().standardIcon(pixmapi)
            btn.setIcon(icon)
            layout.addWidget(btn, int(n/4), int(n%4))
        res.setLayout(layout)
        return res


    def Emulator(self):
        print("Emulator")
        res = QWidget()
        layout = QGridLayout()
        self.emulatorGraph = pg.PlotWidget()
        layout.addWidget(self.emulatorGraph)
        res.setLayout(layout)   
        if len(self.mydata) ==0:
            print(self.mydata)
            self.updatePlots()
        return res
    
    def updatePlots(self):
        print("Updata plot with data of size %d" % len(self.mydata))
        if len(self.mydata) >0:
            self.data = np.zeros([3, len(self.mydata)])
            for i in range(len(self.mydata)):
                self.data[0][i] = float(self.mydata[i][1])
                self.data[1][i] = float(self.mydata[i][2])
                self.data[2][i] = float(self.mydata[i][4])
            print("Updat plots on %s"% self.data)
            x = self.data[:,0]
            y = self.data[:,1]
            minimum = y.min()
            maximum = y.max()
            self._actVal.setText("%.2f" % y[0])
            self._min.setText("%.2f" % minimum)
            self._max.setText("%.2f" % maximum)

            print(minimum, maximum)
            self.recorderGraph.setTitle(self.filename.split("/")[-1])
            self.emulatorGraph.setTitle(self.filename.split("/")[-1])
         
            self.emulatorGraph.plot(x,y)
            self.recorderGraph.plot(x,y)
        

    def tabChanged(self, index):
        self.updatePlots()
        print("Tab changed %d" %(index))

    def okToContinue(self):
        if self.dirty:
            reply = QMessageBox.question(self,
                    "Image Changer - Unsaved Changes",
                    "Save unsaved changes?",
                    QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.fileSave()
        return True


        





if __name__ == "__main__":
    #print("Initalize class")
    app  = QApplication(sys.argv)
    window = App()
    translator = QTranslator(app)

    defaultLocale = QLocale.system().name()
    translator.load(defaultLocale)
    app.installTranslator(translator)
    print(defaultLocale)
    window.show()

    app.exec()
        
    
