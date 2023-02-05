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

# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))
from yocto_api import *
from yocto_genericsensor import *


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
        value =self.sen.get_currentValue()
        if value >0:
            return [(value-4.0)/16.0*100, "°C"]
        else:
            return[self.sen.get_currentValue(),self.sen.get_unit()]
            

    def set_reportFrequency(self, seconds):
        self._seconds = seconds
        self.sen.set_reportFrequency(seconds)

    def registerTimedReportCallback(self, cb):
        if cb is None:
            print("Unregistered CB on %s" % self.sen)
        else:
            print("Registered CB on %s" % self.sen)
        self.sen.registerTimedReportCallback(cb)


conf = {"prod": None, "file": None, "csv": None, "cnt": 0, "max": 0, "thread": None, "start": None}

c = None


def yocto_cb(sensor, value):
    #print("yocto_cb thread %s" % (threading.current_thread().name))
    if conf["prod"] is None:
        return
    if c["cnt"] < c["max"]:
        now = datetime.datetime.now()
        absTime = now.strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
        delta =(now - conf["start"]).total_seconds()
        data = [absTime, delta]
        data.extend(c["prod"].get_values())
        c["csv"].writerow(data)
        print("Write line %d %s" % (c["cnt"], data))
        c["cnt"] += 1
    else:
        print("Thread join cnt %s" % c["cnt"])


def YoctoMonitor(data):
        print("YoctoMonitor started")
        while True:
            if conf["cnt"] < conf["max"]:
                print(
                    "YoctoMonitor cnt = %d/ max= %d Thread %s"
                    % (conf["cnt"], conf["max"], threading.current_thread().name)
                     )
<<<<<<< HEAD
<<<<<<< HEAD
                YAPI.Sleep(500)
=======
                YAPI.Sleep(1)
>>>>>>> 31c8b6a (Sensor seems to work)
=======
                YAPI.Sleep(500)
>>>>>>> 2b8eb2e (Sensor/Producer  seems to work)
            else:
                print("Good bye")
                return
            


class sensors:
    def __init__(self):
        errmsg = YRefParam()
        print("Set up sensors" )
        self.iSen = []
        if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
            sys.exit("init error" + errmsg.value)
        sensor = YGenericSensor.FirstGenericSensor()
        while sensor != None:
            newSensor = sensori(sensor)
            self.iSen.append(newSensor)
            print("Added sensor %s" % newSensor )
            sensor = YGenericSensor.nextGenericSensor(sensor)
            if sensor is None:
                break
        print("Added %s input sensors" % (len(self.iSen)))
        if len(self.iSen) == 0:
            print("No sensors detected")
            sys.exit()
        self.oSen = []
        conf["start"] = datetime.datetime.now()
        # sensor = YCurrentLoopOutput.FindCurrentLoopOutput("TX420MA1-123456.currentLoopOutput")
        # print(sensor)
        # while sensor is not None:
        #     print(sensor)
        #     self.oSen.append(sensori(sensor))
        #     if sensor is None:
        #         break
        #     sensor =  YGenericSensor.nextGenericSensor(sensor)

    def __str__(self):

        res = "In\n"
        for i in self.iSen:
            res += "\t%s\n" % i
        res += "Out"
        for o in self.oSen:
            res += "\t%s\n" % i
        return res

    def get_values(self):
        res = []
        res.extend(self.iSen[0].get_values())
        res.extend(self.iSen[1].get_values())
        print(res)
        return res

    def capture_start(self, sample_cnt, sample_intervall, file_name):
        conf["prod"] = self
        conf["file"] = open(file_name, "w")
        conf["csv"] = csv.writer(conf["file"], lineterminator="\n")
        conf["cnt"] = 0
        conf["max"] = sample_cnt
        conf["thread"] = threading.Thread(target=YoctoMonitor, args=(conf,))
        print("Capture started\n")
        self._set_reportFrequency(sample_intervall)
        self.iSen[0].registerTimedReportCallback(yocto_cb)
        self.iSen[1].registerTimedReportCallback(yocto_cb)
        global c
        c = conf
        conf["thread"].start()
        print("Started thread: %s" % (threading.current_thread().name))

    def capture_stop(self):
        print("Capture stop")
        conf["file"].close()
        conf["file"] = None
        self.iSen[0].registerTimedReportCallback(None)
        self.iSen[1].registerTimedReportCallback(None)
        self.iSen[0].set_reportFrequency("OFF")
        res =self.iSen[1].set_reportFrequency("OFF") 
        print("Close Yoctopuc" )
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


if __name__ == "__main__":
    s = sensors()
    s.capture_start(1440,"20/s", "data.csv")
    print("wait for acquisition finished")
    while  conf["cnt"] < conf["max"]:
        print("Stilll receve %d" % conf["cnt"])
        sleep(1)
    print("Aqsition stop")
    s.capture_stop()
    conf["thread"].join()
    sys.exit()
