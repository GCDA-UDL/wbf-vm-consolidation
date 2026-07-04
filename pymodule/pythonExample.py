import os
import glob
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random

rootPath = "C:/Users/Sergi/Documents/networkExperiments/workloads/"

def getWorkloads():
    return glob.glob(rootPath+"*")

def getWorkloadNames():
    return [os.path.basename(x) for x in getWorkloads()]

def getSequentialSample(series, num):
    splitNum = random.randint(0, len(series) - num)
    return pd.Series(cpuData[splitNum : splitNum + num]).reset_index(drop=True)

def getSplitSequentialSample(series, trainingNum, testNum):
    splitNum = random.randint(0, len(series) - trainingNum - testNum)
    total = pd.Series(cpuData[splitNum : splitNum + num]).reset_index(drop=True)
    training = total[:training]
    test = total[training:]
    return total, training, test

class WorkloadLoader:
    def __init__(self, name):
        self.workloadName = name
    def getTraceList(self, trace):
        return glob.glob(rootPath + self.workloadName + "\\" + trace +'/*')
    def getDataTrace(self, filepath):
        pass
    def getCPUSeries(self, df):
        pass
    def getTraces(self):
        return glob.glob(rootPath + self.workloadName + "/*")
    def getTraceNames(self):
        return [os.path.basename(x) for x in self.getTraces()]

class PlanetlabWorkloadLoader(WorkloadLoader):
    def __init__(self):
        WorkloadLoader.__init__(self, "planetlab")
    
    def getDataTrace(self, filepath):
        return pd.read_csv(filepath, header=None)

    def getCPUSeries(self, df):
        return df[0]