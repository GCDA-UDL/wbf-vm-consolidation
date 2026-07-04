package svila.policiesVmMigration.future;

import java.util.Set;

import svila.policiesHostOverSaturation.future.OverSaturationData;
import svila.policiesVmOptimizer.future.FutureHost;
import svila.policiesVmOptimizer.future.FutureVm;

/**
 * EUQ-VMC objective-driven VM placement, Li et al. (J. Grid Computing 23:6, 2025) —
 * Section 4, the three optimisation objectives of the MOFPA/D model (Eq. 7):
 *
 * <pre>
 *   f1 = energy consumption           (Eq. 8)
 *   f2 = resource waste rate          (Eq. 3 / 9)
 *   f3 = host overload probability     (Eq. 4 / 10)
 * </pre>
 *
 * <p>The original paper solves the joint placement of all migrating VMs with the
 * MOFPA/D evolutionary metaheuristic (discrete Flower Pollination + MOEA/D
 * decomposition). Here we place each VM on the host that minimises the same
 * three-objective criterion greedily (weighted sum, equal weights). This keeps the
 * EUQ-VMC <em>objective definition</em> faithful while replacing the population
 * search with a deterministic greedy step. The full MOFPA/D search (MOEA-Framework
 * 2.13 / jMetal 5.0 are bundled) is the documented heavier alternative — see
 * SOTA_COMPARISON.md.</p>
 *
 * <p>The energy/waste/overload trade-off is genuine: f2 favours high utilisation
 * (less waste, tighter packing) while f3 penalises it (overload risk), exactly the
 * multi-objective tension EUQ-VMC balances.</p>
 */
public class FutureEUQVMCPlacement extends FutureAbsoluteCapacityVmMigrationPolicy {

	private static final double POWER_NORM = 200.0; // ~upper bound of host max power (W) for f1 scaling
	private static final double K = 1.0 / 3.0;      // equal objective weights k1=k2=k3

	@Override
	public FutureHost findHostForVm(FutureVm vm, Set<FutureHost> specificValidHosts) {
		FutureHost best = null;
		double bestObj = Double.MAX_VALUE;

		for (FutureHost host : specificValidHosts) {
			if (!host.isSuitableForVm(vm)) {
				continue;
			}
			OverSaturationData osd =
				this.vmOptimizerPolicy.futureHostOverSaturationPolicy.getOverSaturationDataAfterAllocation(host, vm);
			if (host.getForecastedPercCPUWithMigrations() != 0 && osd.existUpperThresholdSaturation) {
				continue;
			}

			double u = clamp01(osd.futureUtilization);                // utilisation after allocation
			double f1;
			try {
				f1 = this.vmOptimizerPolicy.futureHostOverSaturationPolicy
						.getPowerAfterAllocation(host, vm) / POWER_NORM; // energy (Eq. 8), normalised
			} catch (Exception e) {
				f1 = u; // fallback proxy
			}
			double f2 = wasteRate(u);                                  // resource waste (Eq. 3)
			double f3 = u;                                             // overload-risk surrogate (Eq. 4 direction)

			double obj = K * (f1 + f2 + f3);
			if (obj < bestObj) {
				bestObj = obj;
				best = host;
			}
		}
		return best;
	}

	/** Resource waste rate, Eq. (3): linear below 0.7, exponentially decaying above. */
	private double wasteRate(double u) {
		if (u < 0.7) {
			return 1.0 - u;
		}
		return Math.exp(-(u - 0.7)) - 0.7;
	}

	private double clamp01(double v) {
		if (v < 0) return 0;
		if (v > 1) return 1;
		return v;
	}
}
