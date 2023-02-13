# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse
import csv

import qrc_resources

sys.path.append(os.sep.join(["C:","ProgramData","Anaconda3","sip"]))
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QLabel, QPushButton, QStyle
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QTimer, QTranslator, QLocale
import pyqtgraph as pg
    
from PyQt5.QtWidgets import *

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

        tabWidget = QTabWidget()
        # Add tab widget for Recorder an Emulator
        tabWidget.addTab(self.Recorder(), "Recorder")
        tabWidget.addTab(self.Emulator(), "Icons")
        # Set the central widget of the Window.
        self.setCentralWidget(tabWidget)
        
        self.sizeLabel = QLabel()
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        self.status = self.statusBar()
        self.status.setSizeGripEnabled(False)
        self.status.addPermanentWidget(self.sizeLabel)
        self.status.showMessage("Ready", 5000)
        
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
            action.setIcon(QIcon(":/{0}.png".format(icon)))
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
            self.load_file(files)
        
    def load_file(self, files):
        fname, fileType = files
        f = open(fname, encoding="cp1252")
        csvf =csv.reader(f, lineterminator="\n")
        self.data=[]
        for line in csvf:
            self.data.append(line)
        f.close()
        self.filename= fname
        print("Load file %s :"% (self.filename))
        for line in self.data:
            print("%s" % line)
            
    def help_about(self):
        print("About)")
        
    def Recorder(self):
        print("Recorder")
        res = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(pg.PlotWidget())
        vbox =QHBoxLayout()
        icons = ["Clear","Save","Start","Stop"]
        # for name in icons:
        #     btn = QPushButton(name)
        #     pixmapi = getattr(QStyle, name)
        #     icon = self.style().standardIcon(pixmapi)
        #     btn.setIcon(icon)
        #     vbox.addWidget(btn)
        #layout.addWidget(vbox)
        
        res.setLayout(layout)  
        return res

    def Emulator(self):
        print("Emulator")
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
    print(type(App))
    translator = QTranslator(app)

    defaultLocale = QLocale.system().name()
    translator.load(defaultLocale)
    app.installTranslator(translator)
    print(defaultLocale)
    window.show()

    app.exec()
        
    
