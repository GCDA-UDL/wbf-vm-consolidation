package svila.policiesVmMigration.future;

import java.util.Set;

import org.cloudbus.cloudsim.power.PowerHostUtilizationHistory;
import org.cloudbus.cloudsim.util.MathUtil;

import svila.policiesHostOverSaturation.future.OverSaturationData;
import svila.policiesVmOptimizer.future.FutureHost;
import svila.policiesVmOptimizer.future.FutureVm;

/**
 * AMOVMC adaptive VM placement (fitness function), Goyal &amp; Awasthi (J. Grid
 * Computing 23:21, 2025) — Section 4.2.2, Equation (20) and Algorithm 4.
 *
 * <p>Among the candidate hosts that can host the VM without becoming overloaded,
 * the VM is placed on the one with the best (lowest) fitness</p>
 *
 * <pre>
 *   F = a1·dU + a2·Umax + a3·Umin + a4·Ccycle + a5·Upred + a6·UPer   (Eq. 20)
 * </pre>
 *
 * <p>computed from the candidate host's utilisation profile after allocation:</p>
 * <ul>
 *   <li>dU  (Eq. 21) — mean |consecutive difference| of the utilisation history (volatility)</li>
 *   <li>Umax/Umin (Eq. 22/23) — max/min utilisation</li>
 *   <li>Ccycle (Eq. 24) — fluctuation around the midpoint (variance of the history)</li>
 *   <li>Upred — predicted utilisation after the VM is placed</li>
 *   <li>UPer — fraction of history breaching the performance threshold (0.80)</li>
 * </ul>
 *
 * <p>The fitness rewards stable, predictable hosts with adequate head-room, which is
 * the paper's stated goal (reduce over-utilisation risk and unnecessary migrations).
 * Equal weights a_i = 1/6 are used (the paper leaves them tunable); this is
 * documented in SOTA_COMPARISON.md. Only the host-scoring differs from the shared
 * placement — VM ordering and migration-map construction are inherited.</p>
 */
public class FutureAMOVMCPlacement extends FutureAbsoluteCapacityVmMigrationPolicy {

	private static final double PERF_THRESHOLD = 0.80;
	private static final double A = 1.0 / 6.0; // equal weights a1..a6

	@Override
	public FutureHost findHostForVm(FutureVm vm, Set<FutureHost> specificValidHosts) {
		FutureHost best = null;
		double bestFitness = Double.MAX_VALUE;

		for (FutureHost host : specificValidHosts) {
			if (!host.isSuitableForVm(vm)) {
				continue;
			}
			OverSaturationData osd =
				this.vmOptimizerPolicy.futureHostOverSaturationPolicy.getOverSaturationDataAfterAllocation(host, vm);
			// skip hosts that would be overloaded after allocation (same guard as the baseline)
			if (host.getForecastedPercCPUWithMigrations() != 0 && osd.existUpperThresholdSaturation) {
				continue;
			}

			double fitness = fitness(host, osd.futureUtilization);
			if (fitness < bestFitness) {
				bestFitness = fitness;
				best = host;
			}
		}
		return best;
	}

	/** Eq. 20 fitness from the host utilisation history + predicted utilisation. */
	private double fitness(FutureHost host, double predictedUtil) {
		double[] h = ((PowerHostUtilizationHistory) host.getCurrentHost()).getUtilizationHistory();
		int n = MathUtil.countNonZeroBeginning(h);
		double dU, umax, umin, ccycle, uper;
		if (n >= 2) {
			double sumAbsDiff = 0.0, mean = 0.0, max = 0.0, min = 1.0;
			int breaches = 0;
			for (int i = 0; i < n; i++) {
				mean += h[i];
				if (h[i] > max) max = h[i];
				if (h[i] < min) min = h[i];
				if (h[i] > PERF_THRESHOLD) breaches++;
			}
			mean /= n;
			for (int i = 1; i < n; i++) sumAbsDiff += Math.abs(h[i] - h[i - 1]);
			double var = 0.0;
			for (int i = 0; i < n; i++) var += (h[i] - mean) * (h[i] - mean);
			var /= n;
			dU = sumAbsDiff / (n - 1);   // Eq. 21
			umax = max; umin = min;       // Eq. 22/23
			ccycle = var;                 // Eq. 24 (fluctuation magnitude)
			uper = (double) breaches / n; // performance-threshold breach frequency
		} else {
			dU = umax = umin = ccycle = uper = 0.0;
		}
		double upred = predictedUtil;     // predicted utilisation after allocation
		return A * (dU + umax + umin + ccycle + upred + uper); // Eq. 20, minimise
	}
}
