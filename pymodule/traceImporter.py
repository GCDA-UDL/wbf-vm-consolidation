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
    return pd.Series(series[splitNum : splitNum + num]).reset_index(drop=True)

def getSplitSequentialSample(series, trainingNum, testNum):
    splitNum = random.randint(0, len(series) - trainingNum - testNum)
    total = pd.Series(series[splitNum : splitNum + num]).reset_index(drop=True)
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

class BitBrainsWorkloadLoader(WorkloadLoader):
    def __init__(self):
        WorkloadLoader.__init__(self, "bitbrains")
    
    def getDataTrace(self, filepath):
        return pd.read_csv(filepath, names=None, sep=";", decimal=".", engine='python')

    def getCPUSeries(self, df):
        return df["CPU usage [%]"]
    
class BitBrainsOldFormatWorkloadLoader(WorkloadLoader):
    def __init__(self):
        WorkloadLoader.__init__(self, "bitbrains_old_format")
    
    def getDataTrace(self, filepath):
        return pd.read_csv(filepath, names=None, sep=";\t", decimal=".", engine='python')

    def getCPUSeries(self, df):
        return df["CPU usage [%]"]

class MaternaWorkloadLoader(WorkloadLoader):
    def __init__(self):
        WorkloadLoader.__init__(self, "materna")

    def getDataTrace(self, filepath):
        df_dtype = {0: str,1: int,2: int,3: int,4: np.float32,5: int,6: int,
                         7: np.float32,8: int,9: int,10: np.float32,11: int,12: int}
        return pd.read_csv(filepath, dtype=df_dtype, names=None, sep=";", decimal=",")

    def getCPUSeries(self, df):
        return df["CPU usage [%]"]

# Pending
#class AzureWorkloadLoader(WorkloadLoader):
#    def __init__(self):
#        WorkloadLoader.__init__(self, "azure")
#
#    def getDataTrace(self, filepath):
#        return pd.read_csv(filepath, dtype=df_dtype, names=None, sep=";", decimal=",", engine='python')
#
#    def getCPUSeries(self, df):
#        return df["CPU usage [%]"]

    
#class AlibabaTrace(Trace):
    
class AlibabaWorkloadLoader(WorkloadLoader):
    def __init__(self):
        WorkloadLoader.__init__(self, "alibaba")

    def getDataTrace(self, filepath):
        return pd.read_csv(filepath, names=None, sep=",", decimal=".")

    def getCPUSeries(self, df):
        return df["mem_util_percent"]
    
# Pending
#class GoogleTrace(Trace):

class WorkloadLoaderFactory():
    def getLoader(loaderName):
        if loaderName == "planetlab":
            return PlanetlabWorkloadLoader()
        elif loaderName == "bitbrains":
            return BitBrainsWorkloadLoader()
        elif loaderName == "materna":
            return MaternaWorkloadLoader()
        elif loaderName == "alibaba":
            return AlibabaWorkloadLoader()
        else:
            return None