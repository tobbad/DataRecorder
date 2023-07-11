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

sys.path.append(
    os.sep.join(
        [
            "C:",
            "Users",
            "tobias.badertscher",
            "AppData",
            "Local",
            "miniconda3",
            "Lib",
            "site-packages",
        ]
    )
)
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QThread, QTimer

# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))
from yocto_api import *
from yocto_genericsensor import *
from yocto_currentloopoutput import *


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


sys.excepthook = except_hook


def currThread() -> object:
    return "[thread-" + str(int(QThread.currentThreadId())) + "]"


class SignalHubThread(QThread):
    startTask = pyqtSignal()  # in: start the task
    stopTask = pyqtSignal()  # in: stop the task
    getData = pyqtSignal(str)  # get Data
    statusMsg = pyqtSignal(str)  # out: publish the task status
    arrival = pyqtSignal(dict)  # out: publish a new device arrival
    newValue = pyqtSignal(str, str)  # out: publish a new function value
    removal = pyqtSignal(dict)  # out: publish a device disconnect
    updateSignal = pyqtSignal(list)  # out: Send data to the gui

    def __init__(self):
        super().__init__()
        print("SignalHubThread created from \t%s" % currThread())

    def start(self):
        print("SignalHubThread start in %s" % currThread())
        super().start()


class YoctopuceTask(QObject):
    def __init__(self, subSigThread):
        super(YoctopuceTask, self).__init__()
        # connect incoming signals
        self.subSigThread = subSigThread
        self.subSigThread.startTask.connect(self.initAPI)
        self.subSigThread.stopTask.connect(self.capture_stop)
        self.sensor = None
        self.oSensor = None
        self.capture_size = 0
        self.checkDevices = 0
        self._sampleCnt = 0
        self.file = None
        self.reportFrequncy = "1s"
        self.sampel_interval_ms = 1000
        self.superVisorTimer = None
        self.timeout_add = 10
        self.takeOver = False
        self.lastTime = 0
        self.connected = False
        self.doRecord = False
        self.startTime = None
        self.printUpdate = False

    @pyqtSlot()
    def initAPI(self):
        print("Yoctopuce initAPI in %s" % currThread())
        self.timer = QTimer()
        self.timer.timeout.connect(self.handleEvents)
        self.timer.start(50)
        self.yocto_err = YRefParam()
        YAPI.RegisterLogFunction(self.logfun)
        # Setup the API to use Yoctopuce devices on localhost
        if YAPI.RegisterHub("usb", self.yocto_err) != YAPI.SUCCESS:
            self.subSigThread.statusMsg.emit(
                "Failed to init Yoctopuce API: " + self.yocto_err.value
            )
            return
        YAPI.RegisterDeviceArrivalCallback(self.deviceArrival)
        YAPI.RegisterDeviceRemovalCallback(self.deviceRemoval)
        self.subSigThread.statusMsg.emit("Yoctopuce task ready")
        # prepare to scan Yoctopuce events periodically

    @pyqtSlot()
    def freeAPI(self):
        print("freeAPI")
        self.capture_stop()
        print("Yoctopuce task stopped")
        YAPI.FreeAPI()
        self.statusMsg.emit("Yoctopuce task stopped")
        print("Sensors are stopped")

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
    def ReceiveAndEmulate(self):
        newSensorList = []
        if len(self.sensor) > 3:
            return
        pSensor = YGenericSensor.FirstGenericSensor()
        while pSensor != None:
            newSensor = sensor(pSensor)
            newSensorList.append(newSensor)
            print("Added sensor %s " % (newSensor))
            pSensor = YGenericSensor.nextGenericSensor(pSensor)
        sen = {}
        for s in newSensorList:
            print("Added function %s" % s.function)
            sen[s.function] = s
        self.sensor = sen
        self.connected = True
        print("Registered %d Sensors %s" % (len(self.sensor), self.sensor))
        if self.connected:
            print("Y: device Arrival, setUpCapture")
            self.SetUpCapture()
        self.connected = True
        self.subSigThread.arrival.emit(self.sensor)
        if len(self.sensor) == 0:
            print("No sensors detected")
            sys.exit()


    def deviceArrival(self, m: YModule):
        print("Received Module %s" % m)
        serialNumber = m.get_serialNumber()
        if self.sensor is None:
            newSensorList = []
            print("Y: Input Device arrival SerNr %s %s" % (serialNumber, m))
            if serialNumber == "RX420MA1-16CAEA":
                pSensor = YGenericSensor.FirstGenericSensor()
                while pSensor != None:
                    newSensor = sensor(pSensor)
                    newSensorList.append(newSensor)
                    print("Added sensor %s " % (newSensor))
                    pSensor = YGenericSensor.nextGenericSensor(pSensor)
                sen = {}
                for s in newSensorList:
                    sen[s.function] = s
                self.sensor = sen
                self.connected = True
                # print("Registered %d Sensors %s" % (len(self.sensor), self.sensor))
                if self.connected:
                    print("Y: setUpCapture")
                    self.SetUpCapture()
                self.connected = True
                self.subSigThread.arrival.emit(self.sensor)
                if len(self.sensor) == 0:
                    print("No sensors detected")
                    sys.exit()
        if self.oSensor is None:
            if serialNumber == "TX420MA1-151ECE":
                pSensor = YCurrentLoopOutput.FirstCurrentLoopOutput()
                print("Output Sensor %s" % pSensor)
                if len(self.oSensor) > 3:
                    return
                while pSensor != None:
                    newSensor = sensor(pSensor)
                    newSensorList.append(newSensor)
                    print("Added sensor %s " % (newSensor))
                    pSensor = YCurrentLoopOutput.nextCurrentLoopOutput(pSensor)
                sen = {}
                for s in newSensorList:
                    print("Added function %s" % s.function)
                    sen[s.function] = s
                self.oSensor = sen
                self.connected = True
                print("Registered %d Sensors %s" % (len(self.oSensor), self.oSensor))
                if self.connected:
                    print("Y: device Arrival, setUpPlayback")
                    self.SetUpPlayback()
                self.connected = True
                self.subSigThread.arrival.emit(self.oSensor)
                if len(self.oSensor) == 0:
                    print("No sensors detected")
                    sys.exit()

    def deviceRemoval(self, m: YModule):
        print("Removed %s" % m)
        self.sensor = None
        self.osensor = None
        self.connected = False
        # pass the disconnect to the UI thread via the removal signal
        self.subSigThread.arrival.emit({})

    def SetUpCapture(self):
        if self.printUpdate:
            print(
                "Update capture in Yoctopuc Task (%s) (cnt = %d  with %d ms)"
                % (currThread(), self.capture_size, self.sampel_interval_ms)
            )
        if self.capture_size > 0 and self.sampel_interval_ms > 0:
            for k, v in self.sensor.items():
                if self.printUpdate:
                    print(
                        "\tRegister cb on %s with samples cnt %d"
                        % (k, self.capture_size)
                    )
                v.registerTimedReportCallback(self.new_data)
                v.set_reportFrequency(self.reportFrequncy)
        self.printUpdate = False

    def SetUpPlayback(self):
        print(
            "Set up play back in Yoctopuc Task started (cnt = %d  with %d ms)"
            % self.capture_size, self.sampel_interval_ms)

        if self.capture_size > 0 and self.sampel_interval_ms > 0:
            for k, v in self.outsensor:
                v.registerTimedReportCallback(self.new_data)
                v.set_reportFrequency(self.reportFrequncy)

    def new_data(self, fct, measure=None):
        if self.superVisorTimer == None:
            self.sampleIntervalUpdate = True
            self.superVisorTimer = QTimer(self)
            sampleIntfb = self.sampel_interval_ms + self.timeout_add
            self.superVisorTimer.setInterval(sampleIntfb)
            self.superVisorTimer.timeout.connect(self.new_data_superVisor)
            self.superVisorTimer.start()
            print(
                "Create supervisor timer in thread= %s with %d ms sample intervall in %s"
                % (currThread(), sampleIntfb, currThread())
            )
        if self.doRecord:
            if self.startTime is None:
                # Set up start time
                self.startTimedt = datetime.datetime.now()
                self.startTime = self.startTimedt.now()
                print("Capture started @ %s" % (self.startTime))
                self._sampleCnt = 0
            # Get currrent time
            now = datetime.datetime

            newdata = None
            if isinstance(measure, list):
                newdata = measure
                measureTime = now.now()
            else:
                measureTime = datetime.datetime.fromtimestamp(
                    measure.get_startTimeUTC()
                )
            # print("connected state in new_data is %s/rel Time %s" % (self.connected, delta))

            absTime = now.now().strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
            self.lastTime = now.now()
            # print("Now is %s" %self.lastTime)
            delta = (measureTime - self.startTime).total_seconds()
            data = [absTime, delta]
            if fct is not None:
                d1 = self.sensor["generic1"].get_values()
                if math.isclose(d1[1], -29999.0):
                    d1 = [d1[0], np.nan, "mA"]
                d2 = self.sensor["generic2"].get_values()
                if math.isclose(d2[1], -29999.0):
                    d2 = [d2[0], np.nan, "mA"]
                data.extend(d2)
                data.extend(d1)
            else:
                data.extend([newdata[0], np.nan, "mA", newdata[1], np.nan, "mA"])
            self.subSigThread.updateSignal.emit(data)
            self._sampleCnt += 1
            # print("New data on connected state to %s/rel Time %s" % (self.connected, delta))
            # self.logfun("Remaining cap %d" % self.capture_size)
            self.capture_size -= 1
            if self.capture_size == 0:
                self.logfun("Finished cap %d samples" % self._sampleCnt)
                self.subSigThread.updateSignal.emit([None, None])
                self.capture_stop()
                print("Finished capture in yoctopuc")

    def fakeCB(self):
        if self.connected == False and self.doRecord:
            measureTime = datetime.datetime.now()
            delta = (measureTime - self.startTime).total_seconds()
            print(
                "\tConnected False: Send fake data  delta %s, connected %s"
                % (delta, self.connected)
            )
            if not self.connected:
                self.new_data(None, ["generic2", "generic1"])

    def new_data_superVisor(self, retrigger=True):
        if self.doRecord:
            # If this is called we have to take over regulary sending data to new_data
            # print("new_data_superVisor fired connected: %d RTime = %s ?"% (self.connected,delta ))
            if self.sampleIntervalUpdate:
                print(
                    "Reset fallback intervall to %d ms -> connect to fakeCB"
                    % self.sampel_interval_ms
                )
                self.superVisorTimer.stop()
                self.superVisorTimer.setInterval(self.sampel_interval_ms)
                self.superVisorTimer.timeout.connect(self.fakeCB)
                self.superVisorTimer.start()
                self.sampleIntervalUpdate = False

    @property
    def sampleCnt(self):
        print("Sample count %d" % self._sampleCnt)
        return self._sampleCnt

    def capture_start(self):
        print(
            "Start capture  %d samples with report freq %s in %s"
            % (self.capture_size, self.reportFrequncy, currThread())
        )
        self.doRecord = True
        for k, v in self.sensor.items():
                v.capture_start()
        return self.doRecord

    def capture_stop(self):
        if self.superVisorTimer != None:
            print("Yoctopuc API capture_stop in  %s" % currThread())
            self.superVisorTimer.stop()
            print("superVisorTimer is stopped ")
            for k, v in self.sensor.items():
                v.capture_stop()
            if self.file is not None:
                self.file.close()
                print("Removed file reference")
                self.file = None
            print("Stop supervise")


    def setSampleInterval_ms(self, sampel_interval_ms):
        self.sampel_interval_ms = sampel_interval_ms
        self.fb_sampel_interval_ms = copy.copy(sampel_interval_ms)
        if self.sampel_interval_ms > 0:
            if self.sampel_interval_ms > 1000:
                self.reportFrequncy = "%ds" % (self.sampel_interval_ms / 1000)
            else:
                self.reportFrequncy = "%d/s" % (1000 / self.sampel_interval_ms)
        else:
            self.reportFrequncy = "OFF"
        for k, v in self.sensor.items():
            v.set_reportFrequency(self.reportFrequncy)
        print("Y: Set Sample intervall to %d ms" % sampel_interval_ms)
        self.SetUpCapture()

    def set_capture_size(self, capture_size):
        self.capture_size = capture_size
        self.logfun("Capture size is set to %d" % (capture_size))
        print("Y: Set Capture size ito %d" % (capture_size))
        self.capture_size = capture_size
        self.printUpdate = True
        self.SetUpCapture()

    def functionValueChangeCallback(self, fct: YFunction, value: str):
        hardwareId = fct.get_hardwareId()
        self.newValue.emit(hardwareId, value)

    def logfun(self, line: str):
        msg = line.rstrip()
        # print("API Log: " + msg, currThread())
        # show low-level API logs as status
        self.subSigThread.statusMsg.emit(msg)

    def getSensors(self):
        return self.sensor


class sensor:
    def __init__(self, sensor):
        self.sen = sensor
        name = sensor.get_friendlyName()
        self._name = str(self.sen).split("=")[1].split(".")[1].replace("Sensor", "")
        self.type = self.sen.get_module().get_serialNumber()
        # print("Sensor functionname is %s ;ModuleId is: %s"% (self.function, self.moduleId))
        # print("Sensor class sensor friendly name %s" % self.sen.get_friendlyName())
        self.functionType = self.sen.get_module().functionType(0)
        self.secondsInStr = "OFF"
        print("Sensor Attached %s "% (str(self)))

    def initEmulator(self, sensor):
        self.sen = sensor
        name = sensor.get_friendlyName()
        self._name = "Nope"
        print("Attached %s" % str(self.sen).split("=")[1])
        if "generic" in str(self.sen).split("=")[1].split(".")[1]:
            self._name = str(self.sen).split("=")[1].split(".")[1].replace("Sensor", "")
            self.type = self.sen.get_module().get_serialNumber()
        elif "CurrentLoop" in str(self.sen).split("=")[1].split(".")[1]:
            print("Added transmitter")
            self._name = (
                str(self.sen)
                .split("=")[1]
                .split(".")[1]
                .replace("Transmitter", "trans")
            )
            self.type = self.sen.get_module().get_serialNumber()
        print(
            "Sensor functionType is %s ;ModuleId is: %s"
            % (self.functionType, self.moduleId)
        )
        print("Sensor class sensor friendly name %s" % self.sen.get_friendlyName())
        self.functionType = self.sen.get_module().functionType(0)

    def __str__(self):
        return self.sen.get_friendlyName()

    @property
    def moduleId(self):
        return self.type

    @property
    def function(self):
        return self._name

    def fullfunName(self):
        return str(self.sen).split("=")[1].split(".")[1]

    def get_values(self):
        if self.sen.isOnline():
            val = self.sen.get_currentValue()
            res = [self.function, val, self.sen.get_unit()]
        else:
            res = [self.function, -29999.0, "mA"]
        return res

    def capture_stop(self):
        self.secondsInStr = "OFF"
        self.registerTimedReportCallback(None)
        self.sen.muteValueCallbacks()
        self.sen.set_reportFrequency(self.secondsInStr)

    def capture_start(self):
        self.sen.unmuteValueCallbacks()
        print("S: Set report %s. Unmute Yoctopuc" % self.secondsInStr)
        self.sen.set_reportFrequency(self.secondsInStr)
        return True

    def set_reportFrequency(self, secondsInStr):
        print("S: Set report Frequency to %s" % secondsInStr )
        self.secondsInStr = secondsInStr
        self.sen.set_reportFrequency(self.secondsInStr)

    def registerTimedReportCallback(self, cb):
        if cb is None:
            print("S: Unregistered CB on %s" % self.sen)
        else:
            print("S: Registered CB on %s" % self.sen)
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
        print("Still receive %d" % cnt)
        sleep(1)
    print("Aqistion stop")
    s.capture_stop()
    sys.exit()
