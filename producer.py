# -*- coding: utf-8 -*-
"""
Created on Tue Jan 10 10:34:56 2023

Obtain data from the souce given by the constructors parameter
(either list of USB devices or a file) and return
a list of raw data for given parameters.

@author: tobias.badertscher
"""
import os, sys
# add ../../Sources to the PYTHONPATH
sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))

from yocto_api import *
from yocto_genericsensor import *


class producer:
    """
     According tom the parameter set up device
    """
    def __init__(self, parameter):
        self. errmsg = YRefParam()
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
    
    sen = []
    sensor = YGenericSensor.FirstGenericSensor()
    
    serial = sensor.get_module().get_serialNumber()
    #print(serial)
    channel1 = YGenericSensor.FindGenericSensor(serial + '.genericSensor1')
    channel2 = YGenericSensor.FindGenericSensor(serial + '.genericSensor2')
    sen.append(channel1)
    sen.append(channel2)
    p =  producer(sen)
    #print(sen[0].get_currentValue())
    print(p.get_values())
    
    