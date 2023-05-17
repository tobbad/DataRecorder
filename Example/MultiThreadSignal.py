
import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QWidget,
)
from PyQt5.QtCore import *

def currThread() -> object:
    return '[thread-' + str(int(QThread.currentThreadId())) + ']'



class SubClass(QObject):
    startTask = pyqtSignal()      # in: start the task
    stopTask = pyqtSignal()       # in: stop the task
    m2t = pyqtSignal(str)     # out: publish a message
    t2m = pyqtSignal(str)

    def __init__(self, parent= None):
        super().__init__(parent)
        print("Set up sub class %s" % currThread())
        self.startTask.connect(self.start)
        self.stopTask.connect(self.stop)
        self.m2t.connect(self.fromRemote)
        self.cnt=0
        self.timer = QTimer(self)



    def start(self):
        print("SubClass received start (%s)" % currThread())
        #self.timer = QTimer(self)
        print("Timer created")

        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.send)
        print("Timer about to start")
        self.timer.start()
        print("Started")

    def stop(self):
        print("Other side stopped (%s)"% currThread())
        self.timer.stop()

    def send(self):
        self.cnt+=1
        msg = "%d" % self.cnt
        self.t2m.emit(msg)
        print("Remote in %s send %s" %( currThread(), msg))

    def fromRemote(self, msg):
        print("Received in R (Thread = %s) from Main: %s" %(currThread(),msg))

class MainThread(QMainWindow):
    def __init__(self, parent= None):
        super().__init__(parent)
        print("Set up main thread %s" % currThread())
        self.otherT = QThread()
        self.otherT.start()
        res = self.SetUpGui()
        self.setCentralWidget(res)

        print("GUI is set up")
        self.oc = SubClass()
        print("SubClass is set up")
        self.oc.startTask.connect(self.start)
        self.oc.stopTask.connect(self.stop)
        self.oc.m2t.connect(self.sendfn)
        self.oc.t2m.connect(self.receive)
        self.oc.moveToThread(self.otherT)
        print("Emit start")
        self.oc.startTask.emit()


    def SetUpGui(self):
        self.setWindowTitle("ThreadExample in Thread %s" % currThread())
        res = QWidget()

        self.layout = QVBoxLayout()
        hbox = QHBoxLayout()
        label = QLabel("To send")
        hbox.addWidget(label)
        self.line = QLineEdit()
        hbox.addWidget(self.line)
        self.send = QPushButton("send")
        hbox.addWidget(self.send)
        self.send.clicked.connect(self.sendfn)
        self.layout.addLayout(hbox)

        hbox = QHBoxLayout()
        label = QLabel("From Remote")
        hbox.addWidget(label)
        self.remote = QLabel()
        hbox.addWidget(self.remote)
        self.layout.addLayout(hbox)

        hbox = QHBoxLayout()
        self.stopb = QPushButton("Remote Stop")
        self.stopb.clicked.connect(self.rstop)
        hbox.addWidget(self.stopb)
        self.layout.addLayout(hbox)

        res.setLayout(self.layout)
        return res

    def sendfn(self):
        text = self.line.text()
        print("Main send signal \"%s\"" % text )
        self.oc.m2t.emit(text)
    def receive(self, msg):
        self.remote.setText(msg)

    def fromRemote(self, msg):
        print("Main  %s received: Msg %s" % (currThread(), msg))

    def start(self):
        print("Main %s received start " % (currThread()))

    def stop(self):
        print("Main %s received stop" % (currThread()))
    def rstop(self):
        print("Main received stop from  %s" % (currThread()))





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainThread()
    window.show()
    sys.exit(app.exec())



