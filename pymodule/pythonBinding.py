import os
import glob
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import random
import sys

rootPath = "C:/Users/Sergi/Documents/networkExperiments/workloads/"


def get_bollinger(ser, winma=10, alpha=2):
	ma = ser.rolling(winma).mean()
	std = ser.rolling(winma).std()
	lower = pd.Series(ma - alpha*std).fillna(method='bfill').values
	upper = pd.Series(ma + alpha*std).fillna(method='bfill').values
	return lower, upper

def get_bollinger_upper(ser, winma=10, alpha=2):
	ma = ser.rolling(winma).mean()
	std = ser.rolling(winma).std()
	upper = pd.Series(ma + alpha*std).fillna(method='bfill').values
	return upper

def get_bollinger_lower(ser, winma=10, alpha=2):
	ma = ser.rolling(winma).mean()
	std = ser.rolling(winma).std()
	lower = pd.Series(ma - alpha*std).fillna(method='bfill').values
	return lower

class PythonBinding:
	def process(values):
		result = 0
		for val in values:
			result += val
		return [result, result*2]

	def getWorkloads():
		return glob.glob(rootPath+"*")

	def getBollingerUpper(values, winma=10, alpha=2):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		return get_bollinger_upper(ser, winma=10, alpha=2)

	def getBollinger(values, winma=10, alpha=2):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		upper, lower = get_bollinger(ser, winma=10, alpha=2)
		return np.concatenate((upper, lower))

	def getPythonPath():
		return sys.executable

"""
	def get_alerts(df):
		data = df["data"].values
		low = np.argwhere(data < df["lower"].values)
		high = np.argwhere(data > df["upper"].values)
		return low, high

	def getBollingerRangedFinalData(data, minRange, maxRange, winma=10, alpha=2):
		df = pd.DataFrame(data=data.values, columns=["data"])
		df["lower"] = len(data) * [np.nan]
		df["upper"] = len(data) * [np.nan]
		lower, upper = get_bollinger(df["data"][minRange:maxRange], winma, alpha)
		for i in range(maxRange-minRange):
			df["lower"].loc[minRange+i] = lower[i]
			df["upper"].loc[minRange+i] = upper[i]
		low, high = get_alerts(df)
		return df, low, high

	def getBollingerFinalData(data, winma=10, alpha=2):
		df = pd.DataFrame(data=data.values, columns=["data"])
		df["lower"] = len(data) * [np.nan]
		df["upper"] = len(data) * [np.nan]
		lower, upper = get_bollinger(df["data"], winma, alpha)
		for i in range(len(data)):
			df["lower"].loc[i] = lower[i]
			df["upper"].loc[i] = upper[i]
		low, high = get_alerts(df)
		return df, low, high

	def getAlertPoints(alerts):
		alertsX = []
		alertsY = []
		for i in low:
		    alertsX.append(df.index[i][0])
			alertsY.append(df["data"][i].iloc[0])
		return alertsX, alertsY
"""