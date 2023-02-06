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

def getOpt():
    p = optparse.OptionParser()
    opt, args = p.parse_args()
    return opt, args

class App(QApplication):
    def __init__(self, args):
        print("Create app")
        super().__init__(args)
        self.widget =self. QWidgets()
        self.setWindowTitle("DataRecorder")
        textLabel = QLabel(widget)
        textLabel.setText("Hello World!")
        textLabel.move(110,85)
        
        widget.setGeometry(50,50,320,200)
        widget.show()
        print("Widget show")
        sys.exit(app.exec_())


        





if __name__ == "__main__":
    #print("Initalize class")
    #app =  QApplication(sys.argv)
    app = QApplication(sys.argv)

    window = QPushButton("Push Me")
    window.show()
    
    app.exec()
        
    