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
from configuration import configuration

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

    def __init__(self):
        super(YoctopuceTask, self).__init__()
        # connect incoming signals
        self.startTask.connect(self.initAPI)
        self.stopTask.connect(self.freeAPI)
        self.sensor = {}
        self.capture_size = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.handleEvents)
        self.timer.start(50)
        self.conf = None
        self.checkDevices = 0
        self._sampleCnt = 0
        self.file = None
        self.initAPI()
        self.start = now = datetime.datetime.now()
        self.reportFrequncy = "1s"
        self.sampel_interval_ms = 1000
        


    @pyqtSlot()
    def initAPI(self):
        print('Yoctopuce task started', currThread())
        self.yocto_err = YRefParam()
        YAPI.RegisterLogFunction(self.logfun)
        # Setup the API to use Yoctopuce devices on localhost
        if YAPI.RegisterHub("usb", self.yocto_err) != YAPI.SUCCESS:            
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
        print("Set filename to %s" % fname)
        if self.file is None:
            self.file = open(fname, "w")
            self.cvsfile = csv.writer(self.file, lineterminator="\n")
  
    def deviceArrival(self, m: YModule):
        newSensorList = []
        serialNumber = m.get_serialNumber()
        print("Device arrival SerNr %s %s, " % (serialNumber, m))
        if self.conf == None:
            self.conf = configuration(self)
            
        pSensor = YGenericSensor.FirstGenericSensor()
        print("Sensor %s" %pSensor )
        if len(self.sensor)>3:
            return
        while pSensor != None:
            newSensor = sensor(pSensor)
            newSensorList.append(newSensor)
            print("Added sensor %s " %(newSensor))
            pSensor = YGenericSensor.nextGenericSensor(pSensor)
        sen = {}
        for s in newSensorList:
            sen[s.function] = s
        self.sensor = sen
        print("Registered %d Sensors %s" % (len(self.sensor), self.sensor))
        self.arrival.emit(self.sensor)
        if len(self.sensor) == 0:
            print("No sensors detected")
            sys.exit()

    def deviceRemoval(self, m: YModule):
        print("Removed %s" % m)
        self.sensor = {}
        # pass the disconnect to the UI thread via the removal signal
        self.removal.emit({})
 
    def capture_start(self):
        print("sensors is %s %d" %(self.sensor, len(self.sensor)))
        if len(self.sensor)==0:
            return False
            print("No sensors connected")
        else:
            print("Capture in Yoctopuc Task started (cnt = %d  with %d ms)" %(self.capture_size, self.sampel_interval_ms))
            if self.capture_size >0 and self.sampel_interval_ms>0:
                for s in self.sensor.values():
                    print("Register cb on %s with samples cnt %d" % (s, self.capture_size))
                    s.registerTimedReportCallback(self.new_data)
                    s.set_reportFrequency(self.reportFrequncy)
                print("Capture started on %s" % (self.sensor))
                self.start = now = datetime.datetime.now()
                self._sampleCnt = 0
            return True

 
    def new_data(self, value1, value2): 
        now = datetime.datetime.now()
        absTime = now.strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
        delta = (now - self.start).total_seconds()
        data = [absTime, delta]
        for s in self.sensor.values():
            data.extend(s.get_values())
        self.updateSignal.emit(data)
        self._sampleCnt += 1
        self.capture_size -= 1
        if self.capture_size == 0:
            self.updateSignal.emit([None,None])
            print("Finished capture in yoctopuc")
            
    @property
    def sampleCnt(self):
        print("Sample count %d" % self._sampleCnt)
        return self._sampleCnt
    
    def capture_stop(self):
        print("Capture in Yoctopuc Task finished ")
        for s in self.sensor.values():
            s.capture_stop()
        print("Capture finished")
        if self.file is not None:
            self.file.close()
            self.file = None
        self.freeAPI()
        
    def setSampleInterval_ms(self, sampel_interval_ms):
        self.sampel_interval_ms = sampel_interval_ms
        if self.sampel_interval_ms>0:
            if self.sampel_interval_ms > 1000:
                self.reportFrequncy = "%ds" % (self.sampel_interval_ms/1000)
            else:
                self.reportFrequncy = "%d/s" % (1000/self.sampel_interval_ms )
        else:
            self.reportFrequncy = "OFF"
        for s in self.sensor.values():
            s.set_reportFrequency(self.reportFrequncy)
        print("Y Set Sample interval to %d, Rep Freq to %s" %((sampel_interval_ms, self.reportFrequncy  )))
        self.logfun("Set Sample interval to %d, Rep Freq to %s" % (sampel_interval_ms, self.reportFrequncy  ))

    def set_capture_size(self, capture_size):
        self.capture_size = capture_size
        self.logfun("Capture size is set to  %d" % (capture_size))
        print("Capture size is set to %d" % (capture_size))
        self._sampleCnt = 0
        self.capture_size =capture_size

    def functionValueChangeCallback(self, fct: YFunction, value: str):
        hardwareId = fct.get_hardwareId()
        self.newValue.emit(hardwareId, value)

    def logfun(self, line: str):
        msg = line.rstrip()
        print("API Log: " + msg, currThread())
        # show low-level API logs as status
        self.statusMsg.emit(msg)
    
    def getSensors(self):
        return self.sensor


class sensor:
    def __init__(self, sensor):
        self.sen = sensor
        name = sensor.get_friendlyName()
        self._name = str(self.sen).split("=")[1].split(".")[1].replace("Sensor","")
        self.type = self.sen.get_module().get_serialNumber()
        print("Sensor f name is %s ;ModuleId is: %s"% (self.function, self.moduleId))
        self.functionType = self.sen.get_module().functionType(0)

    def __str__(self):
        return self.function
    
    @property
    def moduleId(self):
        return self.type 

    @property
    def function(self):
        return self._name

    def get_values(self):
        res = [self.function, self.sen.get_currentValue(), self.sen.get_unit()]
        return res

    def capture_stop(self):
        self.set_reportFrequency("OFF")
        self.sen.registerTimedReportCallback(None)

    def set_reportFrequency(self, secondsInStr):
        print("Sensor: Set report frequency to %s" % ( secondsInStr))
        self.sen.set_reportFrequency(secondsInStr)

    def registerTimedReportCallback(self, cb):
        if cb is None:
            print("Sensor: Unregistered CB on %s" % self.sen)
        else:
            print("Sensor: Registered CB on %s" % self.sen)
        self.sen.registerTimedReportCallback(cb)



if __name__ == "__main__":
    cnt = 1440
    
    s = YoctopuceTask()
    
    s.setFilename("sdata.csv")
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
