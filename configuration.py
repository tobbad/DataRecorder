# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 09:11:56 2023

Handles the configuration of the programm

@author: tobias.badertscher
"""
import sys, os

sys.path.append(os.path.join("..", "yoctolib_python", "Sources"))
from xml.etree.ElementTree import ElementTree
from yocto_genericsensor import *


class configuration:
    def __init__(self, conf_file=None):
        if conf_file == None:
            print("Create %s", conf_file)
            self.createNewConf("Example.xml")

    def createNewConf(self, name):

        root = ElementTree()
        print(type(root))
        print(dir(root))

        root.Comment("Bla bla")
        xml = root.Element('configuration ')

        child = ElementTree.SubElement(xml,'targetfolder ')
        child.setAttribute("path", ".")
        xml.appendChild(child)

        child = ElementTree.SubElement(xml,'targetfolder ')
        child.setAttribute("time", "1")
        child.setAttribute("unit", "s")
        child.setAttribute("path", ".")
        xml.append(child)

        child = ElementTree.SubElement(xml,'yoctopuc')
        child.setAttribut("host", "usb")
        child.setAttribute("path", ".")

        xml.append(child)
        xml_str = xml.toprettyxml(indent="\t")
        with open(name, "w") as f:
            f.write(xml_str)
        print("Wrote %s", name)


if __name__ == '__main__':
    print("Create file")
    configuration()
