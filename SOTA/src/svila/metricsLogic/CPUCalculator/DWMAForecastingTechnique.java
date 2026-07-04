package svila.metricsLogic.CPUCalculator;

import java.util.Arrays;
import java.util.List;

import svila.planetlabNetwork.StaticResources;

/**
 * Dynamic Weighted Moving Average (DWMA) forecaster used by the AMOVMC method
 * (Goyal &amp; Awasthi, "Adaptive Multi-Objective Virtual Machine Consolidation
 * for Energy-Efficient Cloud Data Centers", J. Grid Computing 23:21, 2025).
 *
 * Faithful re-implementation of the predictor in Section 4.1 of that paper:
 *   - Algorithm 1: Dynamic Window Size adjustment. The window size ws in [3,30]
 *     is the one that minimises the absolute error between the WMA prediction
 *     and the last actual observation.
 *   - Equation (17): Weighted Moving Average with linearly decreasing weights
 *     (the most recent sample weights ws, the oldest weights 1). NOTE: the paper
 *     prints the normaliser as ws*(ws-1)/2; the algebraically correct sum of the
 *     weights ws+(ws-1)+...+1 is ws*(ws+1)/2, which is what we use so the weights
 *     sum to one (documented deviation - apparent typo in the source paper).
 *   - Equations (18)-(19): final prediction PM_util = w1*P_next + w2*A_prev, with
 *     w1,w2 the normalised accuracies (over the last 10 steps) of the WMA
 *     prediction vs. the persistence (last value) baseline.
 *
 * The forecaster is registered as "dwma" in {@link ForecastingTechniqueFactory}
 * and is selected through the experiment config (hostForecastingTechnique /
 * vmForecastingTechnique*). It runs inside the same "future" pipeline as WBF, so
 * the comparison shares the identical CloudSim energy/SLA model.
 */
public class DWMAForecastingTechnique implements ForecastingTechnique {

	private static final int MIN_WS = 3;
	private static final int MAX_WS = 30;

	@Override
	public void setParams(List<Float> params) {}

	/** Weighted moving average over the last {@code ws} samples (Eq. 17). */
	private double wma(Float[] v, int ws) {
		int n = v.length;
		ws = Math.min(ws, n);
		double num = 0.0;
		double den = 0.0;
		// weight ws to the most recent sample down to 1 for the oldest in the window
		for (int k = 0; k < ws; k++) {
			double weight = ws - k;          // ws, ws-1, ..., 1
			num += v[n - 1 - k] * weight;
			den += weight;                   // = ws*(ws+1)/2
		}
		return den == 0 ? v[n - 1] : num / den;
	}

	/** Algorithm 1: pick the window size in [3,30] with the lowest one-step error. */
	private int dynamicWindow(Float[] v) {
		int n = v.length;
		if (n <= MIN_WS) {
			return Math.max(1, n - 1);
		}
		double lastActual = v[n - 1];
		int bestWs = MIN_WS;
		double bestErr = Double.MAX_VALUE;
		int maxWs = Math.min(MAX_WS, n - 1);
		for (int ws = MIN_WS; ws <= maxWs; ws++) {
			// predict v[n-1] from the ws samples *before* it, compare to the actual
			Float[] past = Arrays.copyOfRange(v, 0, n - 1);
			double pred = wma(past, ws);
			double err = Math.abs(pred - lastActual);
			if (err < bestErr) {
				bestErr = err;
				bestWs = ws;
			}
		}
		return bestWs;
	}

	/**
	 * Weights w1 (WMA accuracy) and w2 (persistence accuracy) from Eq. (19):
	 * over the last up-to-10 transitions, count how often each predictor was the
	 * closer one; normalise so w1 + w2 = 1.
	 */
	private double[] accuracyWeights(Float[] v, int ws) {
		int n = v.length;
		int wmaWins = 0, persistWins = 0;
		int steps = Math.min(10, n - ws - 1);
		for (int i = 0; i < steps; i++) {
			int end = n - 1 - i;                      // predict v[end] from earlier data
			Float[] past = Arrays.copyOfRange(v, 0, end);
			if (past.length < 2) break;
			double actual = v[end];
			double wmaPred = wma(past, ws);
			double persistPred = past[past.length - 1];
			if (Math.abs(wmaPred - actual) <= Math.abs(persistPred - actual)) wmaWins++;
			else persistWins++;
		}
		int total = wmaWins + persistWins;
		if (total == 0) return new double[] {0.5, 0.5};
		return new double[] {(double) wmaWins / total, (double) persistWins / total};
	}

	@Override
	public Float[] apply(Float[] values) {
		int interval = StaticResources.getCE().getMigrationInterval();
		Float[] forecast = new Float[interval];
		if (values == null || values.length == 0) {
			Arrays.fill(forecast, 0f);
			return forecast;
		}
		if (values.length == 1) {
			Arrays.fill(forecast, values[0]);
			return forecast;
		}

		int ws = dynamicWindow(values);             // Algorithm 1
		double pNext = wma(values, ws);             // P_next (Eq. 17)
		double aPrev = values[values.length - 1];   // A_prev (last actual)
		double[] w = accuracyWeights(values, ws);   // w1,w2 (Eq. 19)
		double prediction = w[0] * pNext + w[1] * aPrev; // PM_util (Eq. 18)

		Arrays.fill(forecast, (float) prediction);
		return forecast;
	}

	@Override
	public String getName() {
		return "dwma";
	}
}
