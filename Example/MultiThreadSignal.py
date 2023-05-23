
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
    return '\n\t[thread-' + str(int(QThread.currentThreadId())) + ']\n\t[thread-' + str(QThread.currentThread()) + ']'
    #return '[thread-' + str(QThread.currentThread()) + ']'


class SignalHubThread(QThread):
    startTask = pyqtSignal()      # in: start the task
    stopTask = pyqtSignal()       # in: stop the task
    m2s = pyqtSignal(str)         # out: publish a message main to sub
    s2m = pyqtSignal(str)         # out: publish from sub to main

    def __init__(self):
        super().__init__()
        print("SignalHubThread created in \t%s" % currThread())

    def start(self):
        print("SignalHubThread start in %s" % currThread())
        super().start()




class SubClass(QObject):

    def __init__(self, thread):
        super().__init__(None)
        self.thread = thread
        print("Set up sub class %s" % currThread())
        self.thread.startTask.connect(self.start)
        self.thread.stopTask.connect(self.stop)
        self.thread.m2s.connect(self.fromMain)
        self.cnt=0
        print("Timer created")
        self.timer = QTimer(self)
        print("Timer in Subclass is created")


    def start(self):
        print("SubClass received start (%s)" % currThread())
        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.send)
        print("Timer about to start")
        self.timer.start()
        print("Started")

    def stop(self):
        print("Other side  received stop %s"% currThread())
        self.timer.stop()

    def send(self):
        self.cnt+=1
        msg = "%d" % self.cnt
        self.thread.s2m.emit(msg)
        print("Remote%s send msg: %s" %( currThread(), msg))

    def fromMain(self, msg):
        print("Message received in Sub (Thread%s) from Main: %s" %(currThread(), msg))

class MainThread(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("Set up main thread %s" % currThread())
        self.thread = SignalHubThread()
        res = self.SetUpGui()
        self.setCentralWidget(res)

        print("GUI is set up")
        self.sc = SubClass(self.thread)
        print("SubClass is set up")
        self.thread.startTask.connect(self.start)
        self.thread.stopTask.connect(self.stop)
        self.thread.s2m.connect(self.receive)
        self.thread.moveToThread(self.thread)
        self.thread.start()

        print("Emit start")
        self.thread.startTask.emit()


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
        self.stopb.clicked.connect(self.remoteStop)
        hbox.addWidget(self.stopb)
        self.layout.addLayout(hbox)

        res.setLayout(self.layout)
        return res

    def sendfn(self):
        text = self.line.text()
        print("Main send signal \"%s\" in %s " % (text, currThread() ))
        self.thread.m2s.emit(text)
    def receive(self, msg):
        self.remote.setText(msg)

    def fromRemote(self, msg):
        print("Main\n%s received: Msg\t%s" % (currThread(), msg))

    def start(self):
        print("Main %s received start in " % (currThread()))

    def stop(self):
        print('Main %s received stop in' % (currThread()))

    def remoteStop(self):
        print('Main %s send stop to remote' % (currThread()))
        self.thread.stopTask.emit()





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainThread()
    window.show()
    sys.exit(app.exec())



