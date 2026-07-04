from bollingerFunctions import *
from traceImporter import *
from scipy.signal import find_peaks, peak_prominences
from scipy import stats

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

def getPeaks(series, rolling, zScoreThreshold=None):
    df = pd.DataFrame(series.copy())
    df.columns = [0]
    heightSeries = df.rolling(rolling).mean()
    heightSeries = heightSeries.fillna(heightSeries.mean())
    heightValues = heightSeries[0].values
    if zScoreThreshold is not None and zScoreThreshold != -1: # If there is max height
        zResult = pd.Series(stats.zscore(df[0]), index=df.index)
        outliers = zResult[zResult > zScoreThreshold]
        if len(outliers) > 0:
            minOutlier = df[0].iloc[outliers.index].min()-0.001 # 0.001 due to maxHeight is inclusive
            heightValues =[heightSeries[0].values, minOutlier]

    peaks, _ = find_peaks(series.values, heightValues)
    peaks = np.append(peaks, [series.index[-1]]) # TODO: o ficar l'últim valor com a peak,
                                                 # o mantenir l'últim peak però amb la mateixa "y"
    return peaks

def doPeakInterpolation(series, peak1, peak2):
    x = [peak1, peak2]
    y = [series[peak1], series[peak2]]
    for i in range(peak1+1, peak2):
        x_new = i
        y_new = np.interp(x_new, x, y)
        series[x_new] = y_new

def interpolatePeaks(series, peaks):
    newSeries = series.copy()
    if len(peaks) < 2:
        return newSeries
    peak1 = peaks[0]
    #print(peaks)
    #print(newSeries)
    newSeries.iloc[-1] = newSeries.iloc[peaks[-2]]
    #print(peaks)
    #print(len(newSeries))
    for peak in peaks[1:]:
        peak2 = peak
        doPeakInterpolation(newSeries, peak1, peak2)
        peak1 = peak2
    return newSeries

def getPeaksOverHeight(series, height):
	df = pd.DataFrame(series.copy())
	df.columns = [0]
	peaks, _ = find_peaks(series.values, height=height)
	return peaks

def getSeasonality(series):
	corrPeaks = getPeaksOverHeight(series, 0.4)
	if len(corrPeaks) > 0:
		firstPeak = corrPeaks[0]
		if firstPeak > 1:
			return firstPeak
	return -1

class SignalProcessing:
	def python_getBollinger(values, winma, alpha):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		return get_bollinger_upper(ser, winma, alpha)

	def python_getInterPeaks(values, rolling, zScoreThreshold):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		peaks = getPeaks(ser, rolling, zScoreThreshold)
		return interpolatePeaks(ser, peaks)

	def python_getInterBollinger(values, winma, alpha, rolling, zScoreThreshold):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		interpolatedBollinger = get_bollinger_upper(ser, winma, alpha)
		interpolatedBollingerSer = pd.Series(interpolatedBollinger, dtype=float)
		interPeaks = getPeaks(interpolatedBollingerSer, rolling, zScoreThreshold)
		return interpolatePeaks(interpolatedBollingerSer, interPeaks)

	def python_getSeasonality(values):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		seasonality = getSeasonality(ser)
		isSeasonal = seasonality > 1
		seasonalityValue = seasonality if isSeasonal else 1
		return [int(isSeasonal), int(seasonalityValue)]