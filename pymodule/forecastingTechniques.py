from pmdarima.arima import ADFTest
import pmdarima as pm
import pandas as pd
import numpy as np
from pmdarima import datasets
from pmdarima import preprocessing
from pmdarima.arima import auto_arima
from statsmodels.tsa.api import ExponentialSmoothing, SimpleExpSmoothing, Holt
try:
    from neuralprophet import NeuralProphet
except ImportError:
    NeuralProphet = None  # neuralprophet optional; only needed for neuralProphet technique
from prophet import Prophet
from sklearn import neighbors
import contextlib
import sys

class DummyFile(object):
    def write(self, x): pass

@contextlib.contextmanager
def nostdouterr():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    save_stderr = sys.stderr
    sys.stderr = DummyFile()
    yield
    sys.stdout = save_stdout
    sys.stderr = save_stderr

class ForecastingTechniques:
	def python_getAutoArima(values, periodsForecasted, isSeasonal, seasonalityValue):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		if not np.isfinite(ser).all(): return [-1]
		forecast  = []
		try:
			model = auto_arima(ser,start_p=0,d=1,start_q=0,
					  max_p=5,max_d=5,max_q=5, start_P=0,
					  D=1, start_Q=0, max_P=5,max_D=5,
					  max_Q=5, m=seasonalityValue, seasonal=isSeasonal,
					  error_action='warn',trace=True,
					  supress_warnings=True,stepwise=True,
					  random_state=20,n_fits=1)
			predictionIndex = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
			prediction = pd.DataFrame(model.predict(n_periods = periodsForecasted),index=predictionIndex)
			prediction.columns = ['forecast']
			forecast = prediction['forecast'].values
		except (ValueError, IndexError) as e:
			print(e)
			forecast = [-1]
		print(forecast)
		return forecast

	# https://www.statsmodels.org/stable/examples/notebooks/generated/exponential_smoothing.html
	def python_getSimpleExpSmoothing(values, periodsForecasted, smoothing_level_value=0.8):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		fit = SimpleExpSmoothing(ser, initialization_method="estimated").fit(smoothing_level=smoothing_level_value)
		result = fit.forecast(periodsForecasted)
		predictionIndex = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
		prediction = pd.DataFrame(result,index=predictionIndex)
		prediction.columns = ['forecast']
		forecast = prediction['forecast'].values
		return forecast

	def python_getHoltExpSmoothing(values, periodsForecasted,
								   smoothing_level_value=0.8, smoothing_trend_value=0.2):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		fit = Holt(ser, initialization_method="estimated").fit(smoothing_level=smoothing_level_value,
															   smoothing_trend=smoothing_trend_value,
															   optimized=False)
		result = fit.forecast(periodsForecasted)
		predictionIndex = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
		prediction = pd.DataFrame(result,index=predictionIndex)
		prediction.columns = ['forecast']
		forecast = prediction['forecast'].values
		return forecast
		
	def python_getHoltWintersExpSmoothing(values, periodsForecasted, isSeasonal, seasonalityValue,
		smoothing_level_value=None, smoothing_trend_value=None, smoothing_seasonal_value=None,
		damping_trend_value=None):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		forecast = []
		try:
			fit = None
			if isSeasonal:
				fit = ExponentialSmoothing(ser, seasonal_periods=seasonalityValue,
										   trend='add', seasonal='mul', use_boxcox=True,
										   initialization_method="estimated").fit(
										   		smoothing_level=smoothing_level_value,
												smoothing_trend=smoothing_trend_value,
												smoothing_seasonal=smoothing_seasonal_value,
												damping_trend=damping_trend_value
										   	)
			else:
				fit = ExponentialSmoothing(ser, use_boxcox=True, initialization_method="estimated").fit(
								smoothing_level=smoothing_level_value,
								smoothing_trend=smoothing_trend_value,
								smoothing_seasonal=smoothing_seasonal_value,
								damping_trend=damping_trend_value
					)
			result = fit.forecast(periodsForecasted)
			predictionIndex = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
			prediction = pd.DataFrame(result,index=predictionIndex)
			prediction.columns = ['forecast']
			forecast = prediction['forecast'].values
		except ValueError as e:
			print(e)
			forecast = [-1]
		return forecast

	# http://neuralprophet.com/hyperparameter-selection/
	def python_getNeuralProphet(values, periodsForecasted):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		forecast = []
		try:
			m = NeuralProphet(yearly_seasonality=False,
							  weekly_seasonality=False,
							  daily_seasonality=False,
							  epochs=50)
			temp = ser.copy()
			df = pd.DataFrame({'ds':pd.date_range('1970-01-01 0:00:00', freq='1D', periods=len(temp)).tolist(),
							  "y": temp})
			metrics = None
			with nostdouterr():
				metrics = m.fit(df, freq="D")
			future = m.make_future_dataframe(df, periods=periodsForecasted)
			forecast = m.predict(future)
			prediction = pd.DataFrame(forecast["yhat1"])
			prediction.index = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
			prediction.columns = ['forecast']
			forecast = prediction['forecast'].values
		except ValueError as e:
			print(e)
			forecast = [-1]
		return forecast

	def python_getFacebookProphet(values, periodsForecasted):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		forecast = []
		try:
			m = Prophet(uncertainty_samples=None)
			temp = ser.copy()
			df = pd.DataFrame({'ds':pd.date_range('1970-01-01 0:00:00', freq='1D', periods=len(temp)).tolist(),
								  "y": temp})
			m.fit(df)
			future = m.make_future_dataframe(periods=periodsForecasted)
			forecast = m.predict(future)
			prediction = pd.DataFrame(forecast["yhat"].iloc[-periodsForecasted:])
			prediction.index = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
			prediction.columns = ['forecast']
			forecast = prediction['forecast'].values
		except ValueError as e:
			print(e)
			forecast = [-1]
		return forecast

	def python_getKNN(values, periodsForecasted, n_neighbors):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		weights = "distance" # uniform or distance
		X = ser.index.values.reshape(-1, 1)
		predictionIndex = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
		T = predictionIndex.values.reshape(-1, 1)
		y = ser
		knn = neighbors.KNeighborsRegressor(n_neighbors, weights=weights)
		y_ = knn.fit(X,y).predict(T)
		prediction = pd.DataFrame(y_)
		prediction.index = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
		prediction.columns = ['forecast']
		forecast = prediction['forecast'].values
		# If there is no history, forecast is [NaN]
		return forecast

	def python_getPercentile(values, periodsForecasted, perc):
		values = list(np.float_(values))
		ser = pd.Series(values, dtype=float)
		temp = ser.copy()
		temp = temp.sort_values(ignore_index=True)
		result = [temp.quantile(perc)] * periodsForecasted
		predictionIndex = pd.RangeIndex(start=len(ser), stop=len(ser)+periodsForecasted, step=1)
		prediction = pd.DataFrame(result,index=predictionIndex)
		prediction.columns = ['forecast']
		forecast = prediction['forecast'].values
		return forecast