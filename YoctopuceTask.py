#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 18:51:51 2023

@author: badi
"""
import os, sys
import csv
import threading
from time import *
sys.path.append(os.sep.join(["C:","Users","tobias.badertscher","AppData","Local","miniconda3","Lib","site-packages"]))
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QTimer

# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))
from yocto_api import *
from yocto_genericsensor import *

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
sys.excepthook = except_hook

def currThread():
    return '[thread-' + str(int(QThread.currentThreadId())) + ']'

class YoctopuceTask(QObject):

    startTask = pyqtSignal()        # in: start the task
    stopTask = pyqtSignal()         # in: stop the task
    getData = pyqtSignal(str)       # get Data
    statusMsg = pyqtSignal(str)     # out: publish the task status
    arrival = pyqtSignal(dict)      # out: publish a new device arrival
    newValue = pyqtSignal(str,str)  # out: publish a new function value
    removal = pyqtSignal(dict)      # out: publish a device disconnect

    def __init__(self):
        super(YoctopuceTask, self).__init__()
        # connect incoming signals
        self.startTask.connect(self.initAPI)
        self.stopTask.connect(self.freeAPI)

    @pyqtSlot()
    def initAPI(self):
        print('Yoctopuce task started', currThread())
        errmsg = YRefParam()
        YAPI.RegisterLogFunction(self.logfun)
        # Setup the API to use Yoctopuce devices on localhost
        if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:            
            self.statusMsg.emit('Failed to init Yoctopuce API: ' +
                                errmsg.value)
            return
        YAPI.RegisterDeviceArrivalCallback(self.deviceArrival)
        YAPI.RegisterDeviceRemovalCallback(self.deviceRemoval)
        self.statusMsg.emit('Yoctopuce task ready')
        # prepare to scan Yoctopuce events periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.handleEvents)
        self.checkDevices = 0
        self.timer.start(50)

    @pyqtSlot()
    def freeAPI(self):
        self.timer.stop()
        YAPI.FreeAPI()
        self.statusMsg.emit('Yoctopuce task stopped')

    @pyqtSlot()
    def handleEvents(self):
        if self.checkDevices <= 0:
            YAPI.UpdateDeviceList()
            self.checkDevices = 10
        else:
            self.checkDevices -= 1
        YAPI.HandleEvents()

    def deviceArrival(self, m: YModule):
        serialNumber = m.get_serialNumber()
        print("Device arrival SerNr %d" % (serialNumber))
        # build a description of the device as a dictionnary
        device = { 'serial': serialNumber, 'functions': {} }
        fctcount = m.functionCount()
        for i in range(fctcount):
            device['functions'][m.functionId(i)] = m.functionType(i)
        m.set_userData(device)
        # pass it to the UI thread via the arrival signal
        self.arrival.emit(device)
        # make sure to get notified about each new value
        for functionId in device['functions']:
            bt = YFunction.FindFunction(serialNumber + '.' + functionId)
            bt.registerValueCallback(self.functionValueChangeCallback)

    def functionValueChangeCallback(self, fct: YFunction, value: str):
        hardwareId = fct.get_hardwareId()
        self.newValue.emit(hardwareId, value)

    def deviceRemoval(self, m: YModule):
        # pass the disconnect to the UI thread via the removal signal
        self.removal.emit(m.get_userData())

    def logfun(self, line: str):
        msg = line.rstrip()
        print("API Log: " + msg, currThread())
        # show low-level API logs as status
        self.statusMsg.emit(msg)


class sensori:
    def __init__(self, sensor):
        self.sen = sensor
        self._seconds = None
        self.type = self.sen.get_module().get_serialNumber()
        self.functionType = self.sen.get_module().functionType(0)
        print("Create %s" % self)

    def __str__(self):
        res = "type=%s " % (self.type)
        return res

    def get_values(self):
        res = None
        value = self.sen.get_currentValue()
        if value > 0:
            res = [(value - 4.0) / 16.0 * 100, "°C"]
        else:
            res = [self.sen.get_currentValue(), self.sen.get_unit()]
        return res

    def set_reportFrequency(self, seconds):
        self._seconds = seconds
        self.sen.set_reportFrequency(seconds)

    def registerTimedReportCallback(self, cb):
        if cb is None:
            print("Unregistered CB on %s" % self.sen)
        else:
            print("Registered CB on %s" % self.sen)
        self.sen.registerTimedReportCallback(cb)


conf = {
    "prod": None,
    "file": None,
    "csv": None,
    "cnt": 0,
    "max": 0,
    "thread": None,
    "start": None,
}

c = None
cb = None


def yocto_cb(sensor, value):
    if conf["prod"] is None:
        print("Producer is None")
        return
    if c["cnt"] < c["max"] + 1:
        now = datetime.datetime.now()
        absTime = now.strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
        delta = (now - conf["start"]).total_seconds()
        data = [absTime, delta]
        supData = c["prod"].get_values()
        if supData is None:
            print("Terminate with None Datacapture")
            data = None
        else:
            data.extend(supData)
        if cb is not None:
            cb(data)
            print("Write line %d %s to callback" % (c["cnt"], data))
        else:
            if c["cnt"] < c["max"]:
                if data is not None:
                    c["csv"].writerow(data)
                    print("Write line %d %s to file" % (c["cnt"], data))
            else:
                print("Capture finished")
        c["cnt"] += 1
        print("cnt is now %d" % c["cnt"])
    else:
        print("Thread join cnt %s" % c["cnt"])


def YoctoMonitor(data):
    print("YoctoMonitor started")
    while True:
        if conf["cnt"] < conf["max"] + 1:
            print(
                "YoctoMonitor cnt = %d/ max= %d Thread %s"
                % (conf["cnt"], conf["max"], threading.current_thread().name)
            )
            YAPI.Sleep(500)
        else:
            print("Good bye %d" % conf["cnt"])
            return


class sensors:
    def __init__(self):
        errmsg = YRefParam()
        print("Set up sensors")
        self.iSen = []
        if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
            sys.exit("init error" + errmsg.value)
        sensor = YGenericSensor.FirstGenericSensor()
        while sensor != None:
            newSensor = sensori(sensor)
            self.iSen.append(newSensor)
            print("Added sensor %s" % newSensor)
            sensor = YGenericSensor.nextGenericSensor(sensor)
            if sensor is None:
                break
        print("Added %s input sensors" % (len(self.iSen)))
        if len(self.iSen) == 0:
            print("No sensors detected")
            sys.exit()
        self.oSen = []
        conf["start"] = datetime.datetime.now()
        self._cb = None
        # sensor = YCurrentLoopOutput.FindCurrentLoopOutput("TX420MA1-123456.currentLoopOutput")
        # print(sensor)
        # while sensor is not None:
        #     print(sensor)
        #     self.oSen.append(sensori(sensor))
        #     if sensor is None:
        #         break
        #     sensor =  YGenericSensor.nextGenericSensor(sensor)

    def __str__(self):
        res = "\nIn\n"
        for i in self.iSen:
            res += "\t%s\n" % i
        res += "Out"
        for o in self.oSen:
            res += "\t%s\n" % i
        return res

    def get_values(self):
        res = []
        print("Check %d<%d" % (conf["cnt"], conf["max"]))
        if conf["cnt"] < conf["max"] + 1:
            if conf["cnt"] == conf["max"]:
                print("Terminate capture in get_values")
                return None
            else:
                res.extend(self.iSen[0].get_values())
                res.extend(self.iSen[1].get_values())
        return res

    def register_callback(self, fn):
        print("Register cb %s in sensor" % fn)
        global cb
        cb = fn
        self._cb = fn

    def capture_start(self, sample_cnt, sample_intervall, file_name=None):
        conf["prod"] = self
        if self._cb is None:
            conf["file"] = open(file_name, "w")
            conf["csv"] = csv.writer(conf["file"], lineterminator="\n")
        conf["cnt"] = 0
        conf["max"] = sample_cnt
        conf["thread"] = threading.Thread(target=YoctoMonitor, args=(conf,))
        print("Capture started with sample inmterval %s" % sample_intervall)
        self._set_reportFrequency(sample_intervall)
        self.iSen[0].registerTimedReportCallback(yocto_cb)
        self.iSen[1].registerTimedReportCallback(yocto_cb)
        global c
        c = conf
        conf["thread"].start()
        print("Started thread: %s" % (threading.current_thread().name))

    def capture_stop(self):
        print("Capture stop")
        if file_name is not None:
            conf["file"].close()
            conf["file"] = None
        self.iSen[0].registerTimedReportCallback(None)
        self.iSen[1].registerTimedReportCallback(None)
        self.iSen[0].set_reportFrequency("OFF")
        res = self.iSen[1].set_reportFrequency("OFF")
        print("Close Yoctopuc")
        self._close()

    def _set_reportFrequency(self, sample_intervall):
        self.iSen[0].set_reportFrequency(sample_intervall)
        self.iSen[1].set_reportFrequency(sample_intervall)

    def _close(self):
        YAPI.FreeAPI()

    def sensors(self):
        res = self.iSen
        res.append(self.oSen)
        return res


def pri(res):
    print(res)


if __name__ == "__main__":
    s = sensors()
    s.capture_start(1440, "20/s", "data.csv")
    print("wait for acquisition finished")
    while conf["cnt"] < conf["max"]:
        print("Stil receve %d" % conf["cnt"])
        sleep(1)
    print("Aqistion stop")
    s.capture_stop()
    conf["thread"].join()
    sys.exit()
