# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse
import qrc_resources

sys.path.append(os.sep.join(["C:","ProgramData","Anaconda3","sip"]))
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QTimer, QTranslator, QLocale

for item in sys.path:
    print("\t %s" % item)
    
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

        button = QPushButton("Press Me!")
        button.setCheckable(True)
        button.clicked.connect(self.the_button_was_clicked)

        # Set the central widget of the Window.
        self.setCentralWidget(button)
        self.sizeLabel = QLabel()
        
        self.sizeLabel.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.sizeLabel)
        status.showMessage("Ready", 5000)
        
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
        f = open(fname)
        self.data = f.read()
        f.close()
        self.filename= fname
        print("Load file %s  "% (fname))
            
    def help_about(self):
        print("About)")
        
    def the_button_was_clicked(self):
        print("Clicked!")

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
        
    