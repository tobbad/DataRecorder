# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""

import sys, os
import csv
import numpy as np

class DataSet:
    def __init__(self, r2p):
        self.rData = []   # data as it is (raw) / unconcverted
        self.dData = [] # Physical data
        self.r2p = r2p
        self.doRecord = False
        self.onGoing = False
        self.nanFile = None
        self.file = None
        self.cvsFile = None
        self.gen1 =None
        self.gen2 =None

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
            if self.cvsFile is not None:
                self.csvFile.writerow(pData)

    @property
    def dataSize(self):
        if self.rData is not None:
            print("rawdata size is %d" % len(self.rData))
            return len(self.rData)
        else:
            return 0

    def doRecord(self):
        return self.doRecord
   @doRecord.setter
    def doRecord(self, val):
        self.doRecord = val

    @property
    def onGoing(self):
        return self.onGoing

    @onGoing.setter
    def onGoing(self, onGoing):
        self.onGoing = onGoing

    def sync(self):
            if len(rData)> 0:
                print("Set new data of size cData %d" % (self.dataSize))
                self.gen1 = np.zeros([self.dataSize, 3])
                self.gen2 = np.zeros([self.dataSize, 3])
                for i in range(self.dataSize):
                    self.gen1[i][0] = float(self.pData][i][1])
                    self.gen1[i][1] = float(self.pData][i][1])
                    self.gen1[i][2] = float(self.pData][i][1])

                    self.gen1[i][1] = float(self.cData["generic1"][i][2])
                    self.gen1[i][2] = float(self.rawdata[0][6])
                    self.gen2[i][0] = float(self.cData["generic2"][i][1])
                    self.gen2[i][1] = float(self.cData["generic2"][i][2])
                    self.gen2[i][2] = float(self.rawdata[0][3])
                    self.cData["generic1_u"] = self.cData["generic1"][i][3]
                    self.cData["generic2_u"] = self.rawdata[0][7]

    def load(self, fname):
        if self.file is not None:
            print("!!! File in save is %s !!! " % self.file)
        self.file = open(fname)
        self.cvsFile = csv.writer(self.file, lineterminator="\n")
        self.emUnit =[]
        for idx, line in enumerate(self.cvsFile):
            if line[0].startswith("#"):
                print("Skip line %s  " % line)
            else:
                # print("Load line %d %s " % (idx,  line))
                time = line[0]
                relTime = float(line[1])
                val1 = float(line[2])
                self.emUnit.append(line[3])
                val2 = float(line[4])
                self.emUnit.append(line[5])
                self.rData.append(
                    [time, relTime, val1, self.emUnit[0], val2, self.emUnit[1]]
                )
        self.file.close()
        self.sync()

    def save(self, fname):
        self.setFileName(None)
    def setFileName(self, filename):
        if filename is None:
            self.file.close()
            self.file = None
            self.cvsFile = None
        else:
            self.file = open(filename)
            self.cvsFile = self.csvFile = csv.writer(self.file, lineterminator="\n")
            self.writeCsvHeader(self.cvsFile)

    def setNanFileName(self, filename):
        if filename is None:
            self.nanCvsFile.close()
            self.nanCvsFile = None
        else:
            self.nanFile = open(filename)
            self.cvsNanFile = self.csvFile = csv.writer(self.nanFile, lineterminator="\n")
            self.writeCsvHeader(self.cvsNanFile)

    def writeCsvHeader(self, csvFile):
        data = self.cData["generic2"][0]
        print("Set csv Header")

        res = self.r2p["generic2"](data[2], data[3])
        header = "# generic2 %s" % (res[1])
        csvFile.writerow([header])
        print("\tSet header 2 to %s" % header)

        data = self.cData["generic1"][0]
        res = self.r2p["generic1"](data[2], data[3])
        header = "# generic1 %s" % (res[1])
        csvFile.writerow([header])
        print("\tSet header 1 to %s " % header)

    def clear(self):
        self.pData = {"generic1":[], "generic2":[] }


    def __len__(self):
        return len(self.rawdata)
