#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 18:51:51 2023

@author: badi
"""
import os, sys
import csv
import math
import threading
from datetime import *
from time import *
import copy
import numpy as np
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
        self.checkDevices = 0
        self._sampleCnt = 0
        self.file = None
        self.initAPI()
        self.reportFrequncy = "1s"
        self.sampel_interval_ms = 1000
        self.superVisorTimer = None
        self.timeout_add = 10
        self.takeOver = False
        self.lastTime = 0
        self.connected = False
        self.doCapture = False
        self.startTime = None
        self.initAPI()


    @pyqtSlot()
    def initAPI(self):
        print('Yoctopuce task started', currThread())
        self.yocto_err = YRefParam()
        YAPI.RegisterLogFunction(self.logfun)
        # Setup the API to use Yoctopuce devices on localhost
        if YAPI.RegisterHub("usb", self.yocto_err) != YAPI.SUCCESS:            
            self.statusMsg.emit('Failed to init Yoctopuce API: ' +
                                self.yocto_err.value)
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
        print("Y: Device arrival SerNr %s %s, " % (serialNumber, m))
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
        self.connected = True
        print("Registered %d Sensors %s" % (len(self.sensor), self.sensor))
        if self.connected:
            print("Y: device Arrival, setUpCapture")
            self.SetUpCapture()
        self.connected = True
        self.arrival.emit(self.sensor)
        if len(self.sensor) == 0:
            print("No sensors detected")
            sys.exit()

    def deviceRemoval(self, m: YModule):
        print("Removed %s" % m)
        self.sensor = {}
        self.connected = False
        # pass the disconnect to the UI thread via the removal signal
        self.removal.emit({})
 
    def capture_start(self):
        self.doCapture = True
        return self.doCapture
    def SetUpCapture(self):
        print("Capture in Yoctopuc Task started (cnt = %d  with %d ms)" % (self.capture_size, self.sampel_interval_ms))
        if self.capture_size > 0 and self.sampel_interval_ms > 0:
            for s in self.sensor.values():
                print("Register cb on %s with samples cnt %d" % (s, self.capture_size))
                s.registerTimedReportCallback(self.new_data)
                s.set_reportFrequency(self.reportFrequncy)
            print("Yoctopuc Capture started on %s" % (self.sensor))

    def new_data(self, fct, measure=None):
        if self.superVisorTimer == None:
            self.fb_sampel_interval_ms = self.sampel_interval_ms+self.timeout_add
            self.superVisorTimer = QTimer(self)
            self.superVisorTimer.setInterval(self.fb_sampel_interval_ms)
            self.superVisorTimer.timeout.connect(self.new_data_superVisor)
            self.superVisorTimer.start()
            print("Initial timer to %d ms" % self.fb_sampel_interval_ms)
        #print("%s  %s" %(type(fct), type(measure)))
        if self.doCapture:
            if self.startTime is None:
                # Set up capture
                self.SetUpCapture()
                # Set up start time
                self.startTimedt = datetime.datetime.now()
                self.startTime = self.startTimedt.now()
                print("Capture started on %s with time %s" % (self.sensor, self.startTime))
                self._sampleCnt = 0
             # Get currrent time
            now = datetime.datetime

            newdata = None
            if isinstance(measure, list):
                newdata = measure
                measureTime = now.now()
            else:
                measureTime = datetime.datetime.fromtimestamp(measure.get_startTimeUTC())
            delta = measureTime - self.startTime
            #print("connected state in new_data is %s/rel Time %s" % (self.connected, delta))

            #print("measureTime %s, start: %s/%s" % (measureTime.now(), self.startTimedt, measureTime.now()))
            absTime = now.now().strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
            self.lastTime = now.now()
            #print("Now is %s" %self.lastTime)
            delta = (measureTime - self.startTime).total_seconds()
            data = [absTime, delta]
            if fct is not None:
                d1 = self.sensor["generic1"].get_values()
                if math.isclose(d1[1], -29999.0):
                    d1 = [d1[0], np.nan, "mA"]
                d2 = self.sensor["generic2"].get_values()
                if math.isclose(d2[1], -29999.):
                    d2 = [d2[0], np.nan, "mA"]
                data.extend(d2)
                data.extend(d1)
            else:
                data.extend([newdata[0],np.nan, "mA", newdata[1], np.nan, "mA"])
            self.updateSignal.emit(data)
            self._sampleCnt += 1
            #print("New data on connected state to %s/rel Time %s" % (self.connected, delta))
            #self.logfun("Remaining cap %d" % self.capture_size)
            self.capture_size -= 1
            if self.capture_size == 0:
                self.logfun("Finished cap %d samples" % self._sampleCnt)
                self.updateSignal.emit([None,None])
                print("Finished capture in yoctopuc")

    def fakeCB(self):
        if self.connected == False and self.doCapture:
            measureTime = datetime.datetime.now()
            delta = (measureTime - self.startTime).total_seconds()
            print("\tConnected False: Send fake data  delta %s, connected %s" % (delta, self.connected))
            if not self.connected:
                self.new_data(None, ['generic2','generic1'])


    def new_data_superVisor(self, retrigger=True):
        if self.doCapture:
            # If this is called we have to take over regulary sending data to new_data
            measureTime = datetime.datetime.now()
            delta = (measureTime - self.startTime).total_seconds()
            #print("new_data_superVisor fired connected: %d RTime = %s ?"% (self.connected,delta ))
            if self.sampel_interval_ms != self.fb_sampel_interval_ms :
                self.fb_sampel_interval_ms = self.fb_sampel_interval_ms
                self.fb_sampel_interval_ms = self.sampel_interval_ms
                print("Reset fallback intervall to %d ms -> connect to fakeCB"  % self.sampel_interval_ms)
                self.superVisorTimer.setInterval(self.sampel_interval_ms)
                self.superVisorTimer.timeout.connect(self.fakeCB)
                self.superVisorTimer.stop()
                self.superVisorTimer.start()

    @property
    def sampleCnt(self):
        print("Sample count %d" % self._sampleCnt)
        return self._sampleCnt
    
    def capture_stop(self):
        print("Capture in Yoctopuc Task finished ")
        for s in self.sensor.values():
            s.capture_stop()
        print("Capture finished on sensors")
        if self.file is not None:
            self.file.close()
            print("Removed file reference")
            self.file = None
        self.superVisorTimer.stop()
        del self.superVisorTimer
        #self.freeAPI()

    def setSampleInterval_ms(self, sampel_interval_ms):
        self.sampel_interval_ms = sampel_interval_ms
        self.fb_sampel_interval_ms = copy.copy(sampel_interval_ms)
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
        print("Sensor functionname is %s ;ModuleId is: %s"% (self.function, self.moduleId))
        self.functionType = self.sen.get_module().functionType(0)

    def __str__(self):
        return self.function
    
    @property
    def moduleId(self):
        return self.type 

    @property
    def function(self):
        return self._name

    def fullfunName(self):
        return str(self.sen).split("=")[1].split(".")[1]

    def get_values(self):
        val = self.sen.get_currentValue()
        res = [self.function, val, self.sen.get_unit()]
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
