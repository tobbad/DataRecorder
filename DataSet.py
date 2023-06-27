# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""

import sys, os
import csv
import numpy as np
import configuration
from datetime import *
from YoctopuceTask import *
class DataSet:
    def __init__(self, p2r, r2p):
        self.rData = [] # data as it is (raw) / unconconverted
        self.pData = {} # Physical data
        self.r2p = r2p
        self.p2r = p2r
        self._doRecord = False
        self._onGoing = False
        self.nanFile = None
        self.nanCvsFile = None
        self.file = None
        self.csvFile = None
        self.data = {"generic1": None, "generic2": None, "unit_raw": None, "unit_phy": None}
        self._data1 = None
        self._data2 = None

    def append(self, data):
        if self.onGoing:
            self.rData.append(data)
            pData = [data[0], data[1]]
            pData.extend(self.r2p[data[2]](data[3], data[4]))
            if len(data) > 5:
                pData.extend(self.r2p[data[5]](data[6], data[7]))
            if self.nanFile is not None:
                self.nanFile.close()
                self.nanFile = None
            self.pData.append(pData)
            if self.csvFile is not None:
                self.csvFile.writerow(pData)

    @property
    def dataSize(self):
        if self.rData is not None:
            print("rawdata size is %d" % len(self.rData))
            return len(self.rData)
        else:
            return 0

    @property
    def doRecord(self):
        return self._doRecord
    @doRecord.setter
    def doRecord(self, val):
        self._doRecord = val

    @property
    def onGoing(self):
        return self._onGoing

    @onGoing.setter
    def onGoing(self, onGoing):
        self._onGoing = onGoing

    @property
    def data1(self):
        return self._data1

    @property
    def data2(self):
        return self._data2

    def sync(self, setPData= False):
        if setPData:
            self.data = {"generic1": None, "generic2": None, "unit_raw": None, "unit_phy": None}
        else:
            if self.dataSize>0:
                print("Set new data of size cData %d" %(self.dataSize))

    def load(self, fname):
        if fname is not None:
            file = open(fname)
            self.csvFile = csv.reader(file, lineterminator="\n")
            for idx, line in enumerate(self.csvFile):
                if line[0].startswith("#"):
                    print("Skip line %s  " % line)
                else:
                    # print("Load line %d %s " % (idx,  line))
                    time = line[0]
                    relTime = float(line[1])
                    rval1 = self.r2p(line[2], line[3])
                    rval2 =  self.r2p(line[4], line[5])
                    self.rData.append([time, relTime])
                    self.rData.append( [rval1, rval2 ])
                    print(self.rdata[-1])
            file.close()
        self.sync(True)

    def save(self, fname):
        self.setFileName(None)
        for i in range(dataSize):
            print(self.pdata[i])


    def setFileName(self, filename):
        if self.file is not None:
            self.file.close()
            self.file = None
            self.csvFile = None
        else:
            now = datetime.datetime.now()
            filename = now.strftime("%Y%m%d_%H%M%S.csv")
            print("Set csv Filename to %s" %filename)
        self.file = open(filename, "w")
        self.csvFile = csv.writer(self.file, lineterminator="\n")
        self.writeCsvHeader(self.csvFile)

    def setNanFileName(self, filename):
        if self.nanFile is None:
            return
        if filename is None:
            self.nanFile.close()
            self.nanFile = None
            self.nanCvsFile = None
        else:
            self.nanFile = open(filename)
            self.nanCvsFile = self.csvFile = csv.writer(self.nanFile, lineterminator="\n")
            self.writeCsvHeader(self.cvsNanFile)

    def writeCsvHeader(self, csvFile):
        data = self.data["generic2"][0]
        print("Set csv Header")

        res = self.r2p["generic2"](data[2], data[3])
        header = "# generic2 %s" % (res[1])
        csvFile.writerow([header])
        print("\tSet header 2 to %s" % header)

        data = self.data["generic1"][0]
        res = self.r2p["generic1"](data[2], data[3])
        header = "# generic1 %s" % (res[1])
        csvFile.writerow([header])
        print("\tSet header 1 to %s " % header)

    def clear(self):
        self.data = {"generic1":[], "generic2":[] }


