# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse
import qrc_resources

sys.path.append(os.sep.join(["C:","ProgramData","Anaconda3","sip"]))

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

        button = QPushButton("Press Me!")
        button.setCheckable(True)
        button.clicked.connect(self.the_button_was_clicked)

        # Set the central widget of the Window.
        self.setCentralWidget(button)
        
    def _addMenuBar(self):
        menu = self.menuBar()
        self.setMenuBar(menu)
        fileMenu = QMenu("&File", self)
        menu.addMenu(fileMenu)
        saveMenu = QMenu(QIcon(":save.svg"),"&Save", self)
        menu.addMenu(saveMenu)
        aboutMenu = QMenu("&About", self)
        menu.addMenu(aboutMenu)
       
    def _createToolBars(self):
        # Using a title
        fileToolBar = self.addToolBar("File")
        # Using a QToolBar object
        editToolBar = QToolBar("Edit", self)
        self.addToolBar(editToolBar)
        # Using a QToolBar object and a toolbar area
        helpToolBar = QToolBar("Help", self)
        self.addToolBar(Qt.LeftToolBarArea, helpToolBar)


    def the_button_was_clicked(self):
        print("Clicked!")


        





if __name__ == "__main__":
    #print("Initalize class")
    #app =  QApplication(sys.argv)

    app  = QApplication(sys.argv)
    window = App()
    window = App()
    window.show()
    app.exec()
        
    