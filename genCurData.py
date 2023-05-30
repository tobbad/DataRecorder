# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 09:47:21 2023

@author: tobias.badertscher
"""
import sys, os
import time as ti
import csv
from math import ceil, isnan
from datetime import datetime
import time


def writeCsvHeader(csvFile):
    print("Set csv Header")

    header = "# generic2 mA"
    csvFile.writerow([header])
    print("\tSet header 2 to %s" % header)
    header = "# generic1 mA"
    csvFile.writerow([header])
    print("\tSet header 1 to %s " % header)


def generateCsv(cnt = 1440, sampleIntervall_ms=200):
    # Geneate a current ramp from 4mA to 20mA
    # which fills 1440 samples with the
    # given sampleIntervall_ms and the given
    # Count
    file = open("generated.csv", "w")
    fileCsv = csv.writer(file, lineterminator="\n")
    writeCsvHeader(fileCsv)
    startTime = datetime.now()
    for i in range(cnt):
        now = datetime
        absTime = now.now().strftime("%Y-%m-%dT%H:%M:%S.%f+01:00")
        # print("Now is %s" %self.lastTime)
        measureTime = now.now()
        delta = (measureTime - startTime).total_seconds()
        data = [absTime, delta]
        now = datetime.now()
        dt = (startTime-now)
        curmA1 = (20.0-4-0)/cnt*i + 4.0
        curmA2 = (20.0-4-0)/(cnt*2)*i + 4.0
        data.extend([curmA1, "mA"])
        data.extend([curmA2, "mA"])
        fileCsv.writerow(data)
        print("%04d" % i, data)
        time.sleep(sampleIntervall_ms/1000)
    file.close()

if __name__ == "__main__":
    generateCsv()