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
    def __init__(self, name, doStore ,  p2r, r2p):
        self.rData = [] # data as it is (raw) / unconconverted
        self.data = {} # Physical data
        self.r2p = r2p
        self.p2r = p2r
        self._doRecord = False
        self._onGoing = False
        self._filename = None
        self.file = None
        self.csvFile = None
        self.data = {"generic1": [], "generic2": [], "unit_raw": None, "unit_phy": None}
        self._data1 = None
        self._data2 = None
        self._name = name
        self._doStore = doStore # Injected Function true when data is stored to file
        self.pData = []
        self._ext =""
        self.clear()

    def __len__(self):
        return len(self.rData)

    def append(self, data):
        self._doStore():
            self.rData.append(data)
            pData = [data[0], data[1], data[2]]
            pData.extend(self.r2p[data[2]](data[3], data[4]))
            pData.append(data[5])
            pData.extend( self.r2p[data[5]](data[6],data[7] ))
            gen1 = [ data[1], pData[6], pData[7], data[6], data[7]]
            gen2 = [ data[1], pData[3], pData[4], data[3], data[4]]
            self.data["generic1"].append(gen1)
            self.data["generic2"].append(gen2)
            #print("gen1 %s" % gen1)
            #print("gen2 %s" % gen2)
            if len(self._ext)==0:
                print("Append pData %s in %s" % (pData, self._name))
            self.data["generic2"].append(gen2)
            self.pData.append(pData)
            if self.csvFile is None:
                if  self._filename is None:
                    return
                self.file = open(self._filename, "w")
                self.csvFile = csv.writer(self.file, lineterminator="\n")
                self.writeCsvHeader(self.csvFile)
            else:
                self.csvFile.writerow(pData)
            self.sync()


    @property
    def dataSize(self):
        if self.rData is not None:
            #print("\t DS: rawdata size is %d in %s" % (len(self.rData), self._name))
            return len(self.rData)
        else:
            #print("\t DS: rawdata size is None in %s" %(0, self._name))
            return 0

    @property
    def ext(self):
        return self._ext
    @ext.setter
    def ext(self, val):
        self._ext = val

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
            self._data1[i][2]= self.data["generic1"][i][3]
            self._data2[i][0]= self.data["generic2"][i][0]
            self._data2[i][1]= self.data["generic2"][i][1]
            self._data2[i][2]= self.data["generic2"][i][3]
    def load(self, fname):
        og  = self.onGoing
        self.onGoing = True
        self.rData = []
        if fname is not None:
            file = open(fname)
            self._filename = None
            csvFile = csv.reader(file, lineterminator="\n")
            for idx, line in enumerate(csvFile):
                if line[0].startswith("#"):
                    print("Skip line %s  " % line)
                else:
                    data = []
                    # print("Load line %d %s " % (idx,  line))
                    time = line[0]
                    relTime = float(line[1])
                    rval2 = self.r2p["generic2"](line[2], line[3])
                    rval1 =  self.r2p["generic1"](line[4], line[5])
                    data.extend([time, relTime, "generic2"])
                    data.extend( rval2)
                    data.append( "generic1" )
                    data.extend(rval1)
                    self.append(data)
            self.onGoing= og
            file.close()
        self.sync()
        self.setFileName("tmp.csv")
        self.save()
    def save(self):
        file = open(self._filename, "w")
        csvFile =  csv.writer(file, lineterminator="\n")
        self.writeCsvHeader(csvFile)
        for i in range(self.dataSize):
            csvFile.writerow(self.pData[i])
            print("Saved %s "%self.pData[i])
        file.close()
        print("Saved %s in %s" %( self._filename, os.getcwd()))
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

    def writeCsvHeader(self, csvFile):
        header = "# generic2 %s" % (self.data["generic2"][0][2])
        csvFile.writerow([header])
        print("\tSet header 2 to %s" % header)

        header = "# generic1 %s" % (self.data["generic1"][0][2])
        csvFile.writerow([header])
        print("\tSet header 1 to %s " % header)

    def clear(self):
        self.data = {"generic1":[], "generic2":[] }
        self.pData = []
