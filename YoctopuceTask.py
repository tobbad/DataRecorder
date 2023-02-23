#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 18:51:51 2023

@author: badi
"""
import os, sys
import csv
import threading
from datetime import *
from time import *
sys.path.append(os.sep.join(["C:","Users","tobias.badertscher","AppData","Local","miniconda3","Lib","site-packages"]))
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QTimer

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
    updateSignal = pyqtSignal(list) # out: Send data to th gui
    sensor = None

    def __init__(self):
        super(YoctopuceTask, self).__init__()
        # connect incoming signals
        self.startTask.connect(self.initAPI)
        self.stopTask.connect(self.freeAPI)
        self.sensor = []
        self.sampelInterval_ms  = None
        self.capture_size = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.handleEvents)
        self.checkDevices = 0
        self.timer.start(50)
        self._sampleCnt = 0
        self.file = None
        self.initAPI()


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
        
    def setFilename(self, fname):
        if self.file is None:
            self.file = open(fname, "w")
            self.cvsfile = csv.writer(self.file, lineterminator="\n")
  
    def deviceArrival(self, m: YModule):
        serialNumber = m.get_serialNumber()
        print("Device arrival SerNr %s %s, " % (serialNumber, m))
        pSensor = YGenericSensor.FirstGenericSensor()
        print("Sensor %s" %pSensor )
        while pSensor != None:
            newSensor = sensor(pSensor)
            self.sensor.append(newSensor)
            print("Added sensor %s" % newSensor)
            pSensor = YGenericSensor.nextGenericSensor(pSensor)
        print("Added %s input sensors" % (len(self.sensor)))
        if len(self.sensor) == 0:
            print("No sensors detected")
            sys.exit()
 
    def capture_start(self):
        print("Capture in Yoctopuc Task started (cnt = %d  with %d ms)" %(self.capture_size, self.sampelInterval_ms))
        if self.capture_size is not None and self.sampelInterval_ms is not None:
            for s in self.sensor:
                s.registerTimedReportCallback(self.new_data)
                s.set_reportFrequency(sample_intervall)
            print("Capture started")
            self.start = now = datetime.datetime.now()
            self._sampleCnt = 0

 
    def new_data(self, value1, value2): 
        now = datetime.datetime.now()
        absTime = now.strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
        delta = (now - self.start).total_seconds()
        data = [absTime, delta]
        for s in self.sensor:
            data.extend([s.get_values()[0],s.get_values()[1]])
        self.updateSignal.emit(data)
        if self.file is not None:
            self.cvsfile.writerow(data)
            
        self._sampleCnt += 1
        self.capture_size -= 1
        print("New Data %s" % data)           
        if self.capture_size == 0:
            self.capture_stop()
            self.updateSignal.emit([None,None])
            print("Finished capture in yoctopuc")
            
    @property
    def sampleCnt(self):
        print("Sample couut %d" % self._sampleCnt)
        return self._sampleCnt
    
    def capture_stop(self):
        print("Capture in Yoctopuc Task finished ")
        for s in self.sensor:
            s.registerTimedReportCallback(None)
        print("Capture finished")
        if self.file is not None:
            self.file.close()
            self.file = None
        YAPI.FreeAPI()
      
    def setSampleInterval_ms(self, sample_interval_ms):
        if sample_interval_ms > 1000:
            sampInt = "%ds" % (sample_interval_ms/1000)
        else:
            sampInt = "%d/s" % (1000/sample_interval_ms)
        self.reportFrequncy = sampInt
        for s in self.sensor:
            s.set_reportFrequency(sampInt)
        self.sampelInterval_ms = sample_interval_ms
        self.logfun("Sample interval  %d ms" % (sample_interval_ms ))
        print("Sample frequency:  %s" % (sampInt ))

    def set_capture_size(self, capture_size):
        self.capture_size = capture_size
        self.logfun("Capture size is set to  %d" % (capture_size))
        print("Capture size is set to %d" % (capture_size))
        self._sampleCnt = 0
        self.capture_size =capture_size

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


class sensor:
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

    def capture_stop(self):
        self.sen.registerTimedReportCallback(None)
        self.set_reportFrequency("OFF")



if __name__ == "__main__":
    cnt = 1440
    
    s = YoctopuceTask()
    
    s.setFilename("data.csv")
    s.setSampleInterval_ms(200)
    s.set_capture_size(cnt)
    
    s.capture_start()
    print("wait for acquisition finished")
    while s.sampleCnt < cnt:
        print("Stil receve %d" % cnt)
        sleep(1)
    print("Aqistion stop")
    s.capture_stop()
    sys.exit()
