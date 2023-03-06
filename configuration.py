# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 09:11:56 2023

Handles the configuration of the programm

@author: tobias.badertscher
"""
import sys, os

addPath = os.path.join("..", "yoctolib_python", "Sources")
sys.path.append(addPath)
# print(sys.path)
import xml.etree.ElementTree as ET
import xml.dom.minidom
from yocto_api import *
from yocto_genericsensor import *
#from YoctopuceTask import YoctopuceTask


class configuration:
    def __init__(self, yocto):
        self.yocto = yocto
        self.createNewConf("configuration.xml")

    def createNewConf(self, name):

        # ElementTree.Comment("Bla bla")
        self.sensors = self.yocto.getSensors()
        root = ET.Element("configuration")

        child = ET.SubElement(root, "targetfolder", {"path": "."})
        child = ET.SubElement(
            root,
            "capturetime",
            {
                "time": "24",
                "unit": "h",
            },
        )
        child = ET.SubElement(
            root,
            "datarate",
            {
                "time": "1",
                "unit": "m",
            },
        )
        child = ET.SubElement(root, "yoctopuc")
        child = ET.SubElement(root, "source", {"host": "usb"})
        subChild = ET.SubElement(
            root, "ymodule", {"id": "RX420MA1-123456", "type": "Yocto-4-20mA-Rx"}
        )
        ET.SubElement(
            subChild,
            "yfunction",
            {
                "id": "genericSensor1",
                "signalName": "refTemperatur",
                "type": "input",
                "rawMin": "2.0",
                "rawMax": "20.0",
                "min": "0",
                "max": "120",
                "unit": "C",
            },
        )
        ET.SubElement(
            subChild,
            "yfunction",
            {
                "id": "genericSensor2",
                "signalName": "Temperatur",
                "type": "input",
                "rawMin": "4.0",
                "rawMax": "20.0",
                "min": "0",
                "max": "100",
                "unit": "°C",
            },
        )
        xml_str = xml.dom.minidom.parseString(ET.tostring(root, xml_declaration=True)).toprettyxml()

        with open(name, "wb") as f:
             f.write(bytes(xml_str, 'utf-8'))
        print("Wrote %s" % name)

    def getR2PFunction(self):
        def convert(val, unit):
            if val>0:
                res = [(val-4.0)/16.0*100, "°C"]
            else:
                res = [val, unit]      
            return res
        return convert
        
    def getP2RFunction(self):
        def convert(val, unit):
            res = [[float(val)/100.0*16.0+4.0, "°C"], [val, unit]]
            return res
        return convert
        
    

if __name__ == "__main__":
    print("Create file")
    configuration()
