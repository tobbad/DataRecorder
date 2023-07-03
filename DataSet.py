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
    def __init__(self, name,  p2r, r2p):
        self.rData = [] # data as it is (raw) / unconconverted
        self.data = {} # Physical data
        self.r2p = r2p
        self.p2r = p2r
        self._doRecord = False
        self._onGoing = False
        self.nanFile = None
        self.nanCvsFile = None
        self.file = None
        self.csvFile = None
        self.data = {"generic1": [], "generic2": [], "unit_raw": None, "unit_phy": None}
        self._data1 = None
        self._data2 = None
        self._name = name
        self.clear()

    def __len__(self):
        return len(self.rData)

    def append(self, data):
        if self.onGoing:
            if self._name == "cData":
                print("Received cData"  %data)
            self.rData.append(data)
            pData = [data[0], data[1], data[2]]
            pData.extend(self.r2p[data[2]](data[3], data[4]))
            pData.append(data[2])
            pData.extend( self.r2p[data[5]](data[6],data[7] ))
            gen1 = [ data[1], pData[6], data[6]]
            gen2 = [ data[1], pData[3], data[3]]
            self.data["generic1"].append(gen1)
            self.data["generic2"].append(gen2)
            if self.csvFile is None:
                self.file = open(self._filename, "w")
                self.csvFile = csv.writer(self.file, lineterminator="\n")
                self.writeCsvHeader(self.csvFile)
            else:
                self.csvFile.writerow(pData)


    @property
    def dataSize(self):
        if self.rData is not None:
            #print("\t DS: rawdata size is %d in %s" % (len(self.rData), self._name))
            return len(self.rData)
        else:
            #print("\t DS: rawdata size is None in %s" %(0, self._name))
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

    def sync(self):
        # Synchronize data to data1, data2
        self._data1 = np.zeros([self.dataSize, 3])
        self._data2 = np.zeros([self.dataSize, 3])
        for i in range(self.dataSize):
            self._data1[i][0]= self.data["generic1"][i][0]
            self._data1[i][1]= self.data["generic1"][i][1]
            self._data1[i][2]= self.data["generic1"][i][2]
            self._data2[i][0]= self.data["generic2"][i][0]
            self._data2[i][1]= self.data["generic2"][i][1]
            self._data2[i][2]= self.data["generic2"][i][2]

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
        self.sync()

    def save(self, fname):
        self.setFileName(None)
        self.setFileName(fname)
        print("Save")
        for i in range(self.dataSize):
            self.csvFile.writerow(self.pData[i])
            print(self.pData[i])
        self.setFileName(None)

    def setFileName(self, filename):
        # Set filename to current time if None is given
        # otherwise store it in a file with the given namename
        if filename is None:
            if self.file is not None:
                self.file.close()
            now = datetime.datetime.now()
            self._filename = now.strftime("%Y%m%d_%H%M%S.csv")
        else:
            self._filename = filename
        print("Set csv Filename to %s" % filename)
        self.file = open(filename, "w")
        self.csvFile = csv.writer(self.file, lineterminator="\n")
        self.writeCsvHeader(self.csvFile)

    def setNanFileName(self, filename):
        if filename is None:
            if self.nanFile is not None:
                self.nanFile.close()
            self.nanFile = None
            self.nanCvsFile = None
            now = datetime.datetime.now()
            filename = now.strftime("%Y%m%d_%H%M%S_NaN.csv")
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


