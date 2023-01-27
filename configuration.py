# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 09:11:56 2023

Handles the configuration of the programm

@author: tobias.badertscher
"""
import sys, os

addPath=os.path.join("..", "yoctolib_python", "Sources")
sys.path.append(addPath)
#print(sys.path)
import   xml.etree.ElementTree as ET 
from yocto_api import *
from yocto_genericsensor import *
from sensors import sensors

class configuration:
    def __init__(self):
        self.createNewConf("Example.xml")

    def createNewConf(self, name):

        #ElementTree.Comment("Bla bla")
        sen = sensors()
        self.sensors = sen.sensors()
        print(self.sensors[0].type)
        xml = ET.Element('configuration')

        child = ET.SubElement(xml,'targetfolder', {"path":"."})
        child = ET.SubElement(xml,'capturetime', {"time":"24","unit":"h", })
        child = ET.SubElement(xml,'datarate', {"time":"1","unit":"m", })
        child = ET.SubElement(xml,'yoctopuc')
        child = ET.SubElement(xml,'source', {"host":"usb"})
        subChild = ET.SubElement(xml, "ymodule", {"id":"RX420MA1-123456", "type":"Yocto-4-20mA-Rx"})
        ET.SubElement(subChild, "yfunction",  {"id":"genericSensor1", "signalName":"refTemperatur", "type":"input", "rawMin":"4.0", "rawMax":"20.0","min":"0", "max":"100", "unit":"C"})
        ET.SubElement(subChild, "yfunction",  {"id":"genericSensor2", "signalName":"Temperatur", "type":"input", "rawMin":"4.0", "rawMax":"20.0","min":"0", "max":"100", "unit":"C"})
        xml_str =ET.tostring(xml)
        
        with open(name, "wb") as f:
            f.write(ET.tostring(xml_str))
        print("Wrote %s" % name)


if __name__ == '__main__':
    print("Create file")
    configuration()
