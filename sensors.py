#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 22 18:51:51 2023

@author: badi
"""
import os, sys

# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))
from yocto_api import *
from yocto_genericsensor import *

class sensori:
    def __init__(self, sensor):
        self.sen = sensor
        self.type = self.sen.get_module().get_serialNumber()
        self.functionType = self.sen.get_module().functionType(0)
        print("Create %s" % self)
        print(self.functionType)
        
    def __str__(self):
        res = "type=%s " % (self.type)
        return res
    
    def get_values(self):
            return [self.sen.get_currentValue(), self.sen.get_unit()]
        

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
        sensor = YCurrentLoopOutput.FindCurrentLoopOutput("TX420MA1-123456.currentLoopOutput")
        print(sensor)
        while sensor is not None:
            print(sensor)
            self.oSen.append(sensori(sensor))
            if sensor is None:
                    break
            sensor =  YGenericSensor.nextGenericSensor(sensor) 
            

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
    
        
    
    def sensors(self):
        res =self.iSen
        res.append(self.oSen)
        return res
            
if __name__ == "__main__":
    s = sensors()
    print(s)    
    print(s.get_values())
