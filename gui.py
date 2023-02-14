# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse
import csv
import numpy as np

import qrc_resources

sys.path.append(os.sep.join(["C:","Users","tobias.badertscher","AppData","Local","miniconda3","Lib","site-packages"]))
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QLabel, QPushButton, QStyle, QAction, QTabWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QFrame, QFileDialog
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QColor, QPalette
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QTimer, QTranslator, QLocale, QTimer 
import pyqtgraph as pg
import mkl
import qrc_resources
wd = os.sep.join(["C:","Users","tobias.badertscher","source", "repos", "python", "DataRecorder"])

#print("PYTHONPATH:", os.environ.get('PYTHONPATH'))
#print("PATH:", os.environ.get('PATH'))

class Color(QWidget):

    def __init__(self, color):
        super(Color, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

class App(QMainWindow):
    def __init__(self):
        print("Create app")
        super().__init__()
        self.setWindowTitle("DataRecorder")
        self.status = self.statusBar()
        self._addMenuBar()
        self.dirty = False
        self.filename = None
        self.data = None
        self.btn = {}
        self.data=None
        self.doRecord = False
        
        self.timer  = QTimer()
        self.timer.timeout.connect(self.StopRecord)
        
        tabWidget = QTabWidget()
        # Add tab widget for Recorder an Emulator
        #tabWidget.addTab(self.Recorder(), "Recorder")
        tabWidget.addTab(self.Recorder(), "Recorder")
        tabWidget.addTab(self.Icons(), "Icons")
        tabWidget.addTab(self.WebExample(), "Web")
        tabWidget.addTab(self.Emulator(), "Emulator")
        tabWidget.currentChanged.connect(self.tabChanged)
        # Set the central widget of the Window.
        self.setCentralWidget(tabWidget)
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.status = self.statusBar()
        self.status.setSizeGripEnabled(False)
        self.status.addPermanentWidget(self.sizeLabel)
        self.status.showMessage("Ready", 5000)
        #self.load_file(wd+"\data.cvs")
        
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
        print(self.data)
        
            
    def StartRecord(self):
        self.timer.start(800)
        self.doRecord = True
        print("Start record")
        
        
    def StopRecord(self):
        self.timer.stop()
        self.doRecord = False
        self.doStop()
        print("Stop recording")
        
    def help_about(self):
        print("About)")
        
    def Recorder(self):
        print("Recorder")
        res = QWidget()
        
        layout = QVBoxLayout()
        self.recorderGraph = pg.PlotWidget()
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
        res.setLayout(layout)
        res.setLayout(layout)  
        self.btn["Stop"].hide()
        return res
    
    def doStart(self):
        print("doStart")
        self.btn["Start"].hide()
        self.btn["Stop"].show()
        
    
    def doStop(self):
        if self.doRecord:
            print("doStop")
    
    def doClear(self):
        print("doClear")
    
    def doSave(self):
        print("doSave")
    
    def WebExample(self):
        res = QWidget()

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

    def doStart(self):
        print("doStart")
        self.btn["Stop"].show()
        self.StartRecord()
        
    def doStop(self):
        print("doStop")
        

    def doClear(self):
        print("doClear")
        
    def doSave(self):
        print("doSave")
        

    def Emulator(self):
        print("Emulator")
        res = QWidget()
        layout = QGridLayout()
        self.emulatorGraph = pg.PlotWidget()
        layout.addWidget(self.emulatorGraph)
        res.setLayout(layout)   
        if self.data is not None:
            self.updateEmulator()
        return res
    
    def updateEmulator(self):
        print("Updat emulator graph")
        if self.data is not None:
            x = self.data[:,0]
            y = self.data[:,1]
            print(x,y)
            self.emulatorGraph.plot(x,y)
        

    def tabChanged(self, index):
        print("Tab changed %d" %(index))
        if index == 0:
            pass
        elif index == 1:
            pass
        elif index == 2:
            self.updateEmulator()

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
        
    
