# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import optparse

sys.path.append(os.sep.join(["C:","ProgramData","Anaconda3","sip"]))

for item in sys.path:
    print("\t %s" % item)
    
from PyQt5.QtWidgets import *

class App(QMainWindow):
    def __init__(self):
        print("Create app")
        super().__init__()
        self.setWindowTitle("DataRecorder")

        button = QPushButton("Press Me!")
        button.setCheckable(True)
        button.clicked.connect(self.the_button_was_clicked)

        # Set the central widget of the Window.
        self.setCentralWidget(button)

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
        
    