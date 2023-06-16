# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""

import sys, os
import csv

class DataSet:
    def __init__(self, r2p):
        self.rawdata = []
        self.r2p = r2p
        self.onGoing = False
        self.pData = {"generic1":[], "generic2":[] }
        self.nanFilename = None
        self.nanCvsFile = None
        self.filename = None
        self.nanFile = None
        self.cvsFile = None

    def append(self, data):
        if self.onGoing:
            self.rawdata.append(data)
            pData = [data[0], data[1]]
            pData.extend(self.r2p[data[2]](data[3], data[4]))
            if len(data) > 5:
                pData.extend(self.r2p[data[5]](data[6], data[7]))
            if self.nanCvsFile is not None:
                self.nanCvsFile.close()
                self.nanCvsFile = None
                self.nanFilename = None
            if self.cvsFile is not None:
                csvFile.writerow(pData)

    def sync(self):
        pass

    def setFileName(self, filename):
        if filename is None:
            self.file.close()
            self.file = None
            self.cvsFile = None
        else:
            file = open(filename)
            self.cvsFile = self.csvFile = csv.writer(file, lineterminator="\n")
            self.writeCsvHeader(self.cvsFile)
        self.filename = filename

    def setNanFileName(self, filename):
        if filename is None:
            self.file.close()
            self.nanFile = None
        else:
            self.nanFilename = filename
            nanFile = open(filename)
            self.cvsNanFile = self.csvFile = csv.writer(nanFile, lineterminator="\n")
            self.writeCsvHeader(self.cvsNanFile)
    @property.setter
    def onGoing(self, onGoing):
        self.onGoing = onGoing
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
