# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 10:34:56 2023

Obtain data from the souce given by the constructors parameter
(either list of USB devices or a file) and return
a list of raw data for given parameters.

@author: tobias.badertscher
"""
import os, sys
import csv
from datetime import datetime
import time
from threading import *

# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))
dir(datetime)
from yocto_api import *
from yocto_genericsensor import *


class producer:
    """
    According tom the parameter set up device
    """

    def __init__(self, parameter, addTime=False):
        self.__devices = []
        # print(parameter)
        self.__addTime = addTime
        self.__start = datetime.datetime.now()
        if isinstance(parameter, list):
            # print("Check list")
            for d in parameter:
                print(d)
                if not d.isOnline():
                    print("Device %s is not online" % d)
                self.__devices.extend(parameter)
            # print(self.__devices[0])

    def get_values(self):
        res = []
        now = datetime.datetime.now()
        delta = now - self.__start
        nowS = now.strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
        deltaS = delta.total_seconds()
        data = []
        if self.__addTime:
            res.extend([nowS, deltaS])
        for ch in self.__devices:
            data.append([ch.get_currentValue(), ch.get_unit()])
        res.extend(
            [(data[0][0] - 4.0) / 16 * 100, "C", (data[1][0] - 4.0) / 16 * 100, "C"]
        )
        return res

    def close(self):
        YAPI.FreeAPI()

    def __str__(self):
        return "Producer"


conf = {"prod": None, "file": None, "csv": None, "cnt": 0, "thread": None}

c = None


def yocto_cb(sensor, value):
    print("Registerd cb on %s" % sensor)
    if c["prod"] is None:
        return
    if c["cnt"] < conf["max"]:
        data = c["prod"].get_values()
        c["csv"].writerow(data)
        print("Write line %d %s" % (c["cnt"], data))
        c["cnt"] += 1
    else:
        print("Thread join %s" % c["thread"])
        if c["thread"] is not None:
            c["thread"].join()
            c["thread"] = None
        print(c["thread"])


def YoctoMonitor():
    while True:
        YAPI.Sleep(1000)
        print("cnt = %d/ max= %d" % (conf["cnt"], conf["max"]))
        if conf["cnt"] > conf["max"]:
            print("Break %s" % conf["file"])
            conf["file"].close()
            return
        
if __name__ == "__main__":

    channel = []
    errmsg = YRefParam()
    if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
        sys.exit("init error" + errmsg.value)
    sensor = YGenericSensor.FirstGenericSensor()
    print(sensor)
    serial = sensor.get_module().get_serialNumber()
    # print(serial)

    channel.append(YGenericSensor.FindGenericSensor(serial + ".genericSensor1"))
    channel.append(YGenericSensor.FindGenericSensor(serial + ".genericSensor2"))
    channel[0].set_reportFrequency("1s")
    channel[1].set_reportFrequency("1s")
    channel[0].registerTimedReportCallback(yocto_cb)
    channel[1].registerTimedReportCallback(yocto_cb)
    start = datetime.datetime.now()
    f = open("data.csv", "w")
    w = csv.writer(f, lineterminator="\n")
    p = producer(channel, True)
    conf["prod"] = p
    conf["file"] = f
    conf["csv"] = w
    conf["cnt"] = 0
    conf["max"] = 1440
    conf["thread"] = Thread(target=YoctoMonitor)
    conf["thread"].deamon = True
    conf["thread"].start()
    c = conf
    # conf["thread"].run()
    while conf["cnt"] < conf["max"]:
        pass
    channel[0].registerTimedReportCallback(None)
    channel[1].registerTimedReportCallback(None)
    f.close()
    print("Wait for %s" % conf["thread"])
    YAPI.FreeAPI()
    conf["thread"].join()
    del p
