package svila.policiesHostOverSaturation.future;

import org.apache.commons.math3.distribution.NormalDistribution;
import org.cloudbus.cloudsim.power.PowerHostUtilizationHistory;
import org.cloudbus.cloudsim.util.MathUtil;

import svila.policiesVmOptimizer.future.FutureHost;

/**
 * EUQ-VMC Host Overload Detection (HOD), Algorithm 3 of Li et al.,
 * "Resource-Efficient and Quality-Aware Virtual Machine Consolidation Method",
 * J. Grid Computing 23:6, 2025 — Section 5.1, Equations (4) and (23).
 *
 * <p>The host resource usage HD is modelled as a normal distribution
 * HD ~ N(mu, sigma^2) fitted on the host's utilisation history. The probability
 * that the aggregated VM demand exceeds the host capacity HC (Eq. 4) is</p>
 *
 * <pre>
 *   P_over(h) = Pr(HD &gt; HC) = 1 - Phi( (HC - mu) / sigma )
 * </pre>
 *
 * <p>In normalised CPU-utilisation terms HC = 1, so
 * P_over = 1 - Phi((1 - mu)/sigma). The dynamic overload threshold (Eq. 23) is</p>
 *
 * <pre>
 *   T_upper(h) = 1 - safe * P_over(h)
 * </pre>
 *
 * <p>and the host is over-utilised iff its (forecasted) utilisation U_j exceeds
 * T_upper. {@code safe} is the experiment {@code parameter} (safety factor),
 * matching how the MAD/IQR policies use it.</p>
 */
public class FutureHostOverSaturationEUQVMC extends FutureHostOverSaturationBase {

	private static final NormalDistribution STANDARD_NORMAL = new NormalDistribution();

	public FutureHostOverSaturationEUQVMC(double safetyParameter) {
		super();
		setSafetyParameter(safetyParameter);
	}

	@Override
	public OverSaturationData getOverSaturationData(FutureHost host) {
		PowerHostUtilizationHistory ph = (PowerHostUtilizationHistory) host.getCurrentHost();
		double[] history = ph.getUtilizationHistory();

		double utilization = host.getForecastedPercCPUWithMigrations();
		double tUpper;

		int valid = MathUtil.countNonZeroBeginning(history);
		if (valid >= 12) {
			// mu, sigma of the historical utilisation (Eq. 4: HD ~ N(mu, sigma^2))
			double mu = 0.0;
			for (int i = 0; i < valid; i++) mu += history[i];
			mu /= valid;
			double var = 0.0;
			for (int i = 0; i < valid; i++) var += (history[i] - mu) * (history[i] - mu);
			var /= valid;
			double sigma = Math.sqrt(var);

			double pOver;
			if (sigma <= 1e-9) {
				pOver = (mu >= 1.0) ? 1.0 : 0.0;
			} else {
				double z = (1.0 - mu) / sigma;             // (HC - mu)/sigma, HC = 1
				pOver = 1.0 - STANDARD_NORMAL.cumulativeProbability(z); // Eq. 4
			}
			tUpper = 1.0 - getSafetyParameter() * pOver;    // Eq. 23
		} else {
			// not enough history yet: fall back to a plain 100% threshold (no false positives)
			tUpper = 1.0;
		}

		this.vmOptimizerPolicy.migrationStatistics.addHistoryEntry(host.getCurrentHost(), tUpper);

		// existUpperThresholdSaturation = (utilization > tUpper) by the constructor (Algorithm 3, line 5)
		return new OverSaturationData(host, tUpper, utilization);
	}
}
