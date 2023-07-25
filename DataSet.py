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
        self.rawCsvFile =None
        self.data = {"generic1": [], "generic2": [], "unit_raw": None, "unit_phy": None}
        self._data1 = None
        self._data2 = None
        self._name = name
        self._doStore = doStore # Injected Function true when data is stored to file
        self.pData = []
        self.clear()


    def __len__(self):
        return len(self.rData)
    def __str__(self):
        res= "%s\n" % self._filename
        for k,v in self.data.items():
            res +="Data of %s is (len = %d)\n" % (k, len(self.data[k]))
            for idx in range(len(self.data[k])):
                res+= "data[%d] = %s\n" %(idx, self.data[k][idx])
        return res

    def append(self, data):
        if self._doRecord:
            if self.rawCsvFile is not None:
                self.rawCsvFile.writerow(data)
            self.rData.append(data)
            pData = [data[0], data[1], data[2]]
            pData.extend(self.r2p[data[2]](data[3], data[4]))
            pData.append(data[5])
            pData.extend( self.r2p[data[5]](data[6],data[7] ))
            gen1 = [ data[1], pData[6], pData[7], data[6], data[7]]
            #print("A Gen1 ", gen1)
            gen2 = [ data[1], pData[3], pData[4], data[3], data[4]]
            #print("A Gen2 ", gen2)

            self.data["generic1"].append(gen1)
            self.data["generic2"].append(gen2)
            #print("gen1 %s" % gen1)
            #print("gen2 %s" % gen2)
            if len(self._name)==0:
                print("Append pData %s in\"%s\"" % (pData, self._name))
            self.data["generic2"].append(gen2)
            #print("pData", pData)

            self.pData.append(pData)
            if self.csvFile is None:
                if  self._filename is None:
                    return
                self.file = open(self._filename, "w")
                self.csvFile = csv.writer(self.file, lineterminator="\n")
                self.writeCsvHeader(self.csvFile)
                print("Created file in %s" % self._name)
            else:
                self.csvFile.writerow(pData)
            self.sync()
        else:
            if self.csvFile is not None:
                print("Close file")
                self._filename = None
                self.file.close()
                self.csvFile = None



    @property
    def dataSize(self):
        if self.rData is not None:
            #if len(self._name)==0:
            #    print("\t DS: rawdata size is %d in %s" % (len(self.rData), self._name))
            return len(self.rData)
        else:
            #if len(self._name)==0:
            #    print("\t DS: rawdata size is None in %s" %(0, self._name))
            return 0


    @property
    def onGoing(self):
        return self._onGoing

    @onGoing.setter
    def onGoing(self, onGoing):
        self._onGoing = onGoing

    @property
    def doRecord(self):
        return self._doRecord

    @doRecord.setter
    def doRecord(self, val):
        self._doRecord = val

    @property
    def data1(self):
        return self._data1

    @property
    def data2(self):
        return self._data2

    def sync(self):
        # Synchronize data to data1, data2
        if self.dataSize>0:
            self._data1 = np.zeros([self.dataSize, 3])
            self._data2 = np.zeros([self.dataSize, 3])
            for i in range(self.dataSize):
                self._data1[i][0]= self.data["generic1"][i][0]
                self._data1[i][1]= self.data["generic1"][i][1]
                self._data1[i][2]= self.data["generic1"][i][3]
                self._data2[i][0]= self.data["generic2"][i][0]
                self._data2[i][1]= self.data["generic2"][i][1]
                self._data2[i][2]= self.data["generic2"][i][3]
        else:
            self._data1 = None
            self._data2 = None

    def load(self, fname):
        self.clear()
        og  = self.onGoing
        self.onGoing = True
        self._doRecord = True
        rawFile = open("rawData.csv", "w")
        self.rawCsvFile =csv.writer(rawFile, lineterminator="\n")
        #self.writeCsvHeader(self.rawCsvFile)

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
                    rval2 = self.p2r["generic2"](line[3], line[4])

                    rval1 =  self.p2r["generic1"](line[6], line[7])

                    data.extend([time, relTime, "generic2"])
                    data.extend( rval2)
                    data.append( "generic1" )
                    data.extend(rval1)
                    #print("To Raw" ,data, rval1, rval2)
                    self.append(data)
            self.onGoing= og
            file.close()
        self.sync()
        self._filename = "tmp.csv"
        self.save()
        rawFile.close()
        self._filename = fname
    def save(self):
        file = open(self._filename, "w")
        csvFile =  csv.writer(file, lineterminator="\n")
        self.writeCsvHeader(csvFile)
        for i in range(self.dataSize):
            csvFile.writerow(self.pData[i])
            #print("Saved %s"%(self.pData[i]))
        file.close()
        print("Saved %s in %s" %( self._filename, os.getcwd()))

    @property
    def FileName(self):
        return self._filename

    def getSampleIntervall_ms(self):
        if self.datasize == 0:
            return 0
        else:


    @FileName.setter
    def FileName(self, filename):
        # Set filename to current time if None is given
        # otherwise store it in a file with the given namename
        if filename is None:
            if self.file is not None:
                self.file.close()
                self.csvFile = None
            now = datetime.datetime.now()
            self._filename = now.strftime("%Y%m%d_%H%M%S")
            self._filename = self._filename+self._name+".csv"
        else:
            self._filename = filename
            self.csvFile = None
        print("Set filename in \"%s\" to %s" % (self._name, self._filename))

    def writeCsvHeader(self, csvFile):
        header = "# generic2 %s" % (self.data["generic2"][0][2])
        csvFile.writerow([header])
        print("\tSet header 2 to %s" % header)

        header = "# generic1 %s" % (self.data["generic1"][0][2])
        csvFile.writerow([header])
        print("\tSet header 1 to %s " % header)

    def clear(self):
        self.rData = []
        self.data = {"generic1":[], "generic2":[] }
        self.pData = []
        self._data1 = None
        self._data2 = None
