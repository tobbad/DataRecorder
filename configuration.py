# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 09:11:56 2023

Handles the configuration of the programm

@author: tobias.badertscher
"""
import math
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
    
    configuration_file = "configuration.xml"
    
    def __init__(self, yocto):
        self.yocto = yocto
        fname = "./%s" % (configuration.configuration_file)
        if os.path.exists(fname):
            print("Configuration file exists -> load")
            self.load(fname)
        else:
            print("Configuration file does not exists -> Create")
            self.createNewConf(fname)

    def createNewConf(self, name):

        # ElementTree.Comment("Bla bla")
        self.sensors = self.yocto.getSensors()
        root = ET.Element("configuration")

        child = ET.SubElement(root, "targetfolder", {"path": "."})
        child = ET.SubElement(
            root,
            "capturetime",
            {
                "time": "288",
                "unit": "s",
            },
        )
        child = ET.SubElement(
            root,
            "datarate",
            {
                "time": "200",
                "unit": "m",
            },
        )
        child = ET.SubElement(root, "yoctopuc")
        schild = ET.SubElement(child, "source", {"host": "usb"})
        subChild = ET.SubElement(
            schild, "ymodule", {"id": "RX420MA1-123456", "type": "Yocto-4-20mA-Rx"}
        )
        ET.SubElement(
            subChild,
            "yfunction",
            {
                "id": "genericSensor1",
                "signalName": "refTemperatur",
                "type": "input",
                "rawMin": "4.0",
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

    def load(self, confFile):
        print("Load %s"%confFile )
        self.et = ET.parse(confFile).getroot()
        self._yfunction ={}
        
        for c in self.et.iter():
            print("\t", c.tag, c. attrib)
            if c.tag == "capturetime":
                self._captureTime= {"time":int(c.attrib["time"]), "unit":c.attrib["unit"]}
                #print("Set capture time to %s" % (self._captureTime))
            if c.tag == "datarate":
                self._dataRate= {"time":int(c.attrib["time"]), "unit":c.attrib["unit"]}
                #print("Set capture rate to %s" % (self._dataRate))
            if c.tag == "source":
                self._source = c.attrib["host"]
            if c.tag == "yfunction":
                print(c.attrib)
                self._yfunction[c.attrib["id"].replace("Sensor","")] = {"signalName":c.attrib["signalName"],
                                                "type": c.attrib["type"],
                                                "rawMin": float(c.attrib["rawMin"]),
                                                "rawMax": float(c.attrib["rawMax"]),
                                                "min":  float(c.attrib["min"]),
                                                "max":  float(c.attrib["max"]),
                                                "unit": str(c.attrib["unit"])
                                                }

        print("Yfunction added %s" % (self._yfunction))
        print("source added %s" % (self._source))
        print("Configured Capture data while %d %s with datarate of %d %s " %(self.captureTime["time"], self.captureTime["unit"], self.dataRate["time"], self.dataRate["unit"]))
          
    def save(self):

        # ElementTree.Comment("Bla bla")
        root = ET.Element("configuration")

        child = ET.SubElement(root, "targetfolder", {"path": "."})
        child = ET.SubElement(
            root,
            "capturetime",
            {
                "time": "%s" % self._captureTime["time"],
                "unit": "%s" % self._captureTime["unit"],
            },
        )
        child = ET.SubElement(
            root,
            "datarate",
            {
                "time": "%s" % self.dataRate["time"],
                "unit": "%s" % self.dataRate["unit"]
            },
        )
        child = ET.SubElement(root, "yoctopuc")
        schild = ET.SubElement(child, "source", {"host": "usb"})
        subChild = ET.SubElement(
            schild, "ymodule", {"id": "RX420MA1-123456", "type": "Yocto-4-20mA-Rx"}
        )
        ET.SubElement(
            subChild,
            "yfunction",
            {
                "id": "genericSensor1",
                "signalName": "refTemperatur",
                "type": "input",
                "rawMin": "4.0",
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
        print("Configuration saved")
        
        
    
    @property
    def captureTime(self):
        return self._captureTime

    @property
    def dataRate(self):
        return self._dataRate

    @property
    def getR2PFunction(self):
        def convert1(val, unit):
            if val != None:
                if val > 0:
                    if unit == "mA":
                        res = [(val - self._yfunction["generic1"]["rawMin"]) / (self._yfunction["generic1"]["rawMax"]-self._yfunction["generic1"]["rawMin"])
                        * (self._yfunction["generic1"]["max"]-self._yfunction["generic1"]["min"]), self._yfunction["generic1"]["unit"]]
                    else:
                        raise ValueError("Unknown conversion to %s" % unit)
                elif math.isclose(val, -1):
                    res = [-1, "mA"]
                else:
                    res = [val, unit]
                return res
            else:
                return [None, None]

            return convert1
        def convert2(val, unit):
            if val != None:
                if val > 0:
                    if unit == "mA":
                        res = [(val - self._yfunction["generic2"]["rawMin"]) / (
                                    self._yfunction["generic2"]["rawMax"] - self._yfunction["generic2"]["rawMin"])
                               * (self._yfunction["generic2"]["max"] - self._yfunction["generic2"]["min"]),
                               self._yfunction["generic2"]["unit"]]
                    else:
                        raise ValueError("Unknown conversion to %s" % unit)
                elif math.isclose(val, -1):
                    res = [-1, "mA"]
                else:
                    res = [val, unit]
                return res
            else:
                return [None, None]

            return convert2
        res = {"generic1": convert1,
               "generic2": convert2 }
        return res

    def getP2RFunction(self):
        def convert(val, unit):
            if val != None:
                res = [[float(val)/100.0*16.0+4.0, "°C"], [val, unit]]
                return res
            elif math.isclose(val, -1):
                res = [-1, "mA"]
            else:
                return [None, None]

        return convert
        
    

if __name__ == "__main__":
    print("Create file")
    configuration()
