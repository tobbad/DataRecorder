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
# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))
dir(datetime)
from yocto_api import *
from yocto_genericsensor import *


class producer:
    """
     According tom the parameter set up device
    """
    def __init__(self, parameter):
        self.__devices = []
        #print(parameter)
        if isinstance(parameter, list):
            #print("Check list")
            for d in parameter:
                print(d)
                if not d.isOnline():
                    print("Device %s is not online" % d)
                self.__devices.extend(parameter)
            #print(self.__devices[0])
    
    def get_values(self):
        res = []
        
        for ch in self.__devices:
            #print("Check %s" % ch)
            res.append([ch.get_currentValue(), ch.get_unit()])
        return res
        
    def close(self):
        YAPI.FreeAPI()
    
    def __str__(self):
        return "Producer"



if __name__ == '__main__':
    
    channel = []
    errmsg = YRefParam()
    if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
        sys.exit("init error" + errmsg.value)
    sensor = YGenericSensor.FirstGenericSensor()
    print(sensor)
    serial = sensor.get_module().get_serialNumber()
    #print(serial)
    
    channel.append(YGenericSensor.FindGenericSensor(serial + '.genericSensor1'))
    channel.append(YGenericSensor.FindGenericSensor(serial + '.genericSensor2'))
    p =  producer(channel)
    start = datetime.datetime.now()
    f = open("data.csv", 'w')
    w = csv.writer(f, lineterminator='\n')
    for i in range(1440):
        now = datetime.datetime.now()
        nowStr  = now.strftime("%Y-%m-%dT%H:%M:%S+01:00")
        delta = now-start
        delta = (delta).total_seconds()
        to_write = [nowStr, delta]
        data = p.get_values()
        to_write.extend([ data[0][0], data[0][1], data[1][0], data[1][1] ])
        print(to_write)
        w.writerow(to_write)
        #time.sleep(0.5)
        YAPI.Sleep(1)
        if i%100==0:
            print(i)

    f.close()    
    print(errmsg)
    YAPI.FreeAPI()

    