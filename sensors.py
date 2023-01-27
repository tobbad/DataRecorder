#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 18:51:51 2023

@author: badi
"""
import os, sys
import csv
import threading

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
        print(self.functionType)
        
    def __str__(self):
        res = "type=%s " % (self.type)
        return res
    
    def get_values(self):
            return [self.sen.get_currentValue(), self.sen.get_unit()]
    
    def set_sample_intervall(self, seconds):
        self._seconds = seconds
        self.sen.set_reportFrequency("%ss"% seconds)

    def registerTimedReportCallback(self, cb):
        self.sen.registerTimedReportCallback(cb)

conf = {
    "prod":None,
    "file": None,
    "csv": None,
    "cnt":0,
    "max":0,
    "thread":None
}

c=None

def yocto_cb(sensor, value):
    print("yocto_cb %s, thread %s" % (c, (threading.currentThread().getName() )))
    if c["prod"] is None:
        return
    if c["cnt"]<conf["max"]:
        data = c["prod"].get_values()
        c["csv"].writerow(data)
        print("Write line %d %s"% (c["cnt"],data))
        c["cnt"]+=1
    else:
        print("Thread join %s" % c["thread"])
        if  c["thread"] is not None:
            c["thread"].join()
            c["thread"]=None
        print(c["thread"])
       

def YoctoMonitor():
    while True:
      print("cnt = %d/ max= %d Thread %s" % (conf["cnt"], conf["max"], threading.currentThread().getName()))
      YAPI.Sleep(1000)
      sys.exit()
      if conf["cnt"]>conf["max"]:
          print("Break %s" % conf["file"])
          break


class sensors():
    def __init__(self):
        errmsg = YRefParam()
        self.iSen = []
        if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
            sys.exit("init error" + errmsg.value)
        sensor = YGenericSensor.FirstGenericSensor()
        while sensor != None:
            print(sensor)
            self.iSen.append(sensori(sensor))
            if sensor is None:
                break
            sensor =  YGenericSensor.nextGenericSensor(sensor) 
        self.oSen=[]
            

    def __str__(self):
        res = "In\n"
        for i in self.iSen:
            res += "\t%s\n"%i
        res += "Out"  
        for o in self.oSen:
            res += "\t%s\n"%i
        return res
    
    def get_values(self):
        res = []
        res.extend(self.iSen[0].get_values())
        res.extend(self.iSen[1].get_values())
        return res
    
    def capture_start(self, sample_cnt, sample_intervall, file_name):
        self._set_sample_interval(sample_intervall)
        conf["prod"] = self
        conf['file'] = open(file_name, "w")
        conf["csv"] = csv.writer(conf['file'], lineterminator='\n')
        conf["cnt"] = 0
        conf["max"] = sample_cnt
        self.iSen[0].registerTimedReportCallback(yocto_cb)
        self.iSen[1].registerTimedReportCallback(yocto_cb)
        conf["thread"] = threading.Thread(target=YoctoMonitor)
        c =  conf
        print("capture start %s" % c)
        conf["thread"].run()
        print("Working in thread %s" % (threading.currentThread().getName()) )


    def capture_stop(self):
        self._close()
        self.iSen[0].registerTimedReportCallback(None)
        self.iSen[1].registerTimedReportCallback(None)
        conf["file"].close()
        YoctoUnregisterHub()

    def _set_sample_interval(self, seconds):
        self.iSen[0].set_sample_intervall(seconds)
        self.iSen[1].set_sample_intervall(seconds)
        
    def _close(self):
        YAPI.FreeAPI()

    
    def sensors(self):
        res =self.iSen
        res.append(self.oSen)
        return res
            
if __name__ == "__main__":
    s = sensors()
    s.capture_start(14, 1, "sdata.csv")
    while conf["cnt"] < conf["max"]:
        pass
    s.capture_stop()
     
    
