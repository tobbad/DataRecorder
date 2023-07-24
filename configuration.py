# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 09:11:56 2023

Handles the configuration of the programm

@author: tobias.badertscher
"""
import math
import sys, os
import numpy as np
import xml.etree.ElementTree as ET
import xml.dom.minidom

addPath = os.path.join("..", "yoctolib_python", "Sources")
sys.path.append(addPath)
# print(sys.path)
from yocto_api import *
from yocto_genericsensor import *


# from YoctopuceTask import YoctopuceTask


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
        xml_str = xml.dom.minidom.parseString(
            ET.tostring(root, xml_declaration=True)
        ).toprettyxml()

        with open(name, "wb") as f:
            f.write(bytes(xml_str, "utf-8"))
        print("Wrote %s" % name)

    def load(self, confFile):
        print("Load conf file %s " % (confFile))
        self.et = ET.parse(confFile).getroot()
        self._yfunction = {}

        for c in self.et.iter():
            # print("\t", c.tag, c. attrib)
            if c.tag == "capturetime":
                self._captureTime = {
                    "time": int(c.attrib["time"]),
                    "unit": c.attrib["unit"],
                }
                # print("Set capture time to %s" % (self._captureTime))
            if c.tag == "sampleinterval":
                self._sampleInterval = {
                    "time": int(c.attrib["time"]),
                    "unit": c.attrib["unit"],
                }
                # print("Set capture rate to %s" % (self.sampleInterval))
            if c.tag == "source":
                self._source = c.attrib["host"]
            if c.tag == "yfunction":
                self._yfunction[c.attrib["id"].replace("Sensor", "")] = {
                    "signalName": c.attrib["signalName"],
                    "type": c.attrib["type"],
                    "rawMin": float(c.attrib["rawMin"]),
                    "rawMax": float(c.attrib["rawMax"]),
                    "min": float(c.attrib["min"]),
                    "max": float(c.attrib["max"]),
                    "unit": str(c.attrib["unit"]),
                }

        # print("Yfunction added %s" % (self._yfunction))
        # print("source added %s" % (self._source))
        # print("Configured Capture data during %d %s with datarate of %d %s " %(self._captureTime["time"], self._captureTime["unit"], self._sampleInterval["time"], self._sampleInterval["unit"]))

    def save(self, doSave):
        print("Save configuration", (self._captureTime, self._sampleInterval))
        root = ET.Element("configuration")

        child = ET.SubElement(root, "targetfolder", {"path": "."})
        child = ET.SubElement(
            root,
            "capturetime",
            {
                "time": "{}".format(self._captureTime["time"]),
                "unit": "{}".format(self._captureTime["unit"]),
            },
        )
        child = ET.SubElement(
            root,
            "sampleinterval",
            {
                "time": "{}".format(self._sampleInterval["time"]),
                "unit": "{}".format(self._sampleInterval["unit"]),
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
                "rawMin": "{}".format(self._yfunction["generic1"]["rawMin"]),
                "rawMax": "{}".format(self._yfunction["generic1"]["rawMax"]),
                "min": "{}".format(self._yfunction["generic1"]["min"]),
                "max": "{}".format(self._yfunction["generic1"]["max"]),
                "unit": "{}".format(self._yfunction["generic1"]["unit"]),
            },
        )
        ET.SubElement(
            subChild,
            "yfunction",
            {
                "id": "genericSensor2",
                "signalName": "Temperatur",
                "type": "input",
                "rawMin": "{}".format(self._yfunction["generic2"]["rawMin"]),
                "rawMax": "{}".format(self._yfunction["generic2"]["rawMax"]),
                "min": "{}".format(self._yfunction["generic2"]["min"]),
                "max": "{}".format(self._yfunction["generic2"]["max"]),
                "unit": "{}".format(self._yfunction["generic2"]["unit"]),
            },
        )
        xml_str = xml.dom.minidom.parseString(
            ET.tostring(root, xml_declaration=True)
        ).toprettyxml()
        if doSave:
            with open(configuration.configuration_file, "wb") as f:
                f.write(bytes(xml_str, "utf-8"))
            print("Wrote %s" % configuration.configuration_file)
        else:
            print("Inhibited save of %s" % configuration.configuration_file)

    @property
    def CaptureTime(self):
        return self._captureTime

    @CaptureTime.setter
    def CaptureTime(self, capTime):
        print("Set captureTime %d %s " % (capTime["time"], capTime["unit"]))
        self._captureTime = capTime

    @property
    def SampleInterval(self):
        return self._sampleInterval

    @SampleInterval.setter
    def SampleInterval(self, dr):
        print("Set Sample interval to %d %s " % (dr["time"], dr["unit"]))
        self._sampleInterval = dr

    @property
    def getR2PFunction(self):
        def convert1(val, unit):
            val = float(val)
            if np.isnan(val):
                res = [np.nan, "mA"]
                print("Is Nan")

            else:
                if val > 0:
                    if unit == "mA":
                        res = [
                            (val - self._yfunction["generic1"]["rawMin"])
                            / (
                                    self._yfunction["generic1"]["rawMax"]
                                    - self._yfunction["generic1"]["rawMin"]
                            )
                            * (
                                    self._yfunction["generic1"]["max"]
                                    - self._yfunction["generic1"]["min"]
                            ),
                            self._yfunction["generic1"]["unit"],
                        ]
                    else:
                        raise ValueError("Unknown conversion to %s" % unit)
                else:
                    print("Value <0" )
                    res = [val, unit]

            return res

        def convert2(val, unit):

            val = float(val)
            if np.isnan(val):
                res = [np.nan, "mA"]
            else:
                if unit == "mA":
                    res = [
                        (val - self._yfunction["generic2"]["rawMin"])
                        / (
                                self._yfunction["generic2"]["rawMax"]
                                - self._yfunction["generic2"]["rawMin"]
                        )
                        * (
                                self._yfunction["generic2"]["max"]
                                - self._yfunction["generic2"]["min"]
                        ),
                        self._yfunction["generic2"]["unit"],
                    ]
                    tunit = self._yfunction["generic2"]["unit"]
                else:
                    raise ValueError("Unknown conversion to %s" % unit)

            return res
        print("Converted Raw(mA) to Physical (%s) "% ( self._yfunction["generic2"]["unit"]))
        fnDict = {"generic1": convert1, "generic2": convert2}
        print("getR2PFunction", fnDict)
        return fnDict

    @property
    def getP2RFunction(self):
        def convert1(val, unit):

            val = float(val)
            if np.isnan(val):
                res = [np.nan, "mA"]
            else:
                if val > 0:
                    if unit == "°C":
                        res = [
                            (val - self._yfunction["generic1"]["min"])
                            / (
                                    self._yfunction["generic1"]["max"]
                                    - self._yfunction["generic1"]["min"]
                            )
                            * (
                                self._yfunction["generic1"]["rawMax"]
                            ),
                            "mA",
                        ]
                    else:
                        print("Received unit %s to convert " % unit)
                        res = [val, "mA"]
                else:
                    print("Negativ value  %d %s  " % (val, unit))
                    res = [val, unit]
            return res
        def convert2(val, unit):

            val = float(val)
            if np.isnan(val):
                res = [np.nan, "mA"]
            else:
                if val > 0:
                    if unit == "°C":
                        res = [
                            (val - self._yfunction["generic2"]["min"])
                            / (
                                    self._yfunction["generic2"]["max"]
                                    - self._yfunction["generic1"]["min"]
                            )
                            * (
                                self._yfunction["generic2"]["rawMax"]
                            ),
                            "mA",
                        ]
                    else:
                        print("Received unit %s to convert ")
                        res = [val, unit]
                else:
                    print("Negativ value  %d %s  " % (val, unit))
                    res = [val, unit]

            return res
        print("Converted Physical(%s) to -> mA "% ( self._yfunction["generic2"]["unit"]))

        fnDict = {"generic1": convert1, "generic2": convert2}
        print("getP2RFunction", fnDict)
        return fnDict


if __name__ == "__main__":
    print("Create file")
    configuration()
