import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import glob
import plotly.graph_objects as go
from plotly.subplots import make_subplots

inputFolder = "C:\\Users\\Sergi\\Documents\\networkExperiments\\workloads\\"

def get_bollinger(ser, winma=10, alpha=2):
    ma = ser.rolling(winma).mean()
    std = ser.rolling(winma).std()
    lower = pd.Series(ma - alpha*std).fillna(method='bfill').values
    upper = pd.Series(ma + alpha*std).fillna(method='bfill').values
    return lower, upper

def get_alerts(df):
    data = df["data"].values
    low = np.argwhere(data < df["lower"].values)
    high = np.argwhere(data > df["upper"].values)
    return low, high

def getBollingerFinalData(data, minRange, maxRange, winma=10, alpha=2):
    df = pd.DataFrame(data=data, columns=["data"])
    df["lower"] = len(data) * [np.nan]
    df["upper"] = len(data) * [np.nan]
    lower, upper = get_bollinger(df["data"][minRange:maxRange], winma, alpha)
    for i in range(maxRange-minRange):
        df["lower"].loc[minRange+i] = lower[i]
        df["upper"].loc[minRange+i] = upper[i]
    low, high = get_alerts(df)
    return df, low, high

def getAlertPoints(alerts):
    alertsX = []
    alertsY = []
    for i in low:
        alertsX.append(df.index[i][0])
        alertsY.append(df["data"][i].iloc[0])
    return alertsX, alertsY

def showBollingerPlot(df, lowAlertsX, lowAlertsY, highAlertsX, highAlertsY):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["lower"], mode='lines', name='Lower'))
    fig.add_trace(go.Scatter(x=df.index, y=df["data"], mode='lines', name='Data'))
    fig.add_trace(go.Scatter(x=df.index, y=df["upper"], mode='lines', name='Upper'))
    fig.add_trace(go.Scatter(x=lowAlertsX, y=lowAlertsY, mode='markers', name='Low alerts'))
    fig.add_trace(go.Scatter(x=highAlertsX, y=highAlertsY, mode='markers', name='High alerts'))
    fig.show()

def showDiffPlot(df):
    df["diffThreshold"] = df["upper"] - df["lower"]
    mean = df["diffThreshold"].mean()
    std = df["diffThreshold"].std()
    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(go.Scatter(x=df.index,
                             y=df["data"], mode='lines', name='data'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index,
                             y=df["upper"], mode='lines', name='upper'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index,
                             y=df["diffThreshold"], mode='lines', name='diffThreshold'), row=2, col=1)
    fig.update_layout(shapes=[
    dict(type= 'line', yref= 'y', y0= mean, y1= mean, xref= 'paper', x0= 0, x1= 1, name="mean"
         ),
    dict(type= 'line', yref= 'y', y0= mean+std, y1= mean+std, xref= 'paper', x0= 0, x1= 1, name="mean+std"
         ) 
    ])
    fig.show()

def showAutocorrelationPlot(df):
    ax = autocorrelation_plot(df["data"])
    pyplot.show()

def getAutocorrelationData(df):
    ax = autocorrelation_plot(df["data"])
    correlationData = ax.lines[5].get_data()[1]
    return pd.DataFrame(data=correlationData, columns=["correlationData"])
    
class WorkloadLoader:
    def __init__(self):
        pass
    def getTraces(self, trace):
        pass
    def getDataTrace(self, filepath):
        pass
    def getCPUSeries(self, df):
        pass
    
class MaternaWorkloadLoader(WorkloadLoader):
    def getTraces(self, trace):
        return glob.glob(inputFolder + "materna" + "\\" + trace +'/*')

    def getDataTrace(self, filepath):
        df_dtype = {0: str,1: int,2: int,3: int,4: np.float32,5: int,6: int,
                         7: np.float32,8: int,9: int,10: np.float32,11: int,12: int}
        return pd.read_csv(filepath, dtype=df_dtype, names=None, sep=";", decimal=",")

    def getCPUSeries(self, df):
        return df["CPU usage [%]"].values