package svila.policiesVmSelection.future;

import java.util.List;

import svila.policiesVmOptimizer.future.FutureHost;
import svila.policiesVmOptimizer.future.FutureVm;

/**
 * AMOVMC Modified VM Selection (ROS-like), Algorithm 3 of Goyal &amp; Awasthi
 * (J. Grid Computing 23:21, 2025).
 *
 * <p>Whereas classic MMT picks the VM with the smallest RAM (fastest migration),
 * AMOVMC selects the VM with the highest <em>combined</em> recent+predicted CPU
 * utilisation, i.e. the VM that contributes most to the (forecasted) host
 * overload. Algorithm 3 computes for each VM</p>
 *
 * <pre>
 *   VU_comb = w1 * VU_next + w2 * VU_prd
 * </pre>
 *
 * <p>and returns argmax(VU_comb). In the "future" pipeline the per-VM forecast
 * {@link FutureVm#getForecastedMIPS()} already carries the combined
 * recent+predicted load produced by the configured forecaster (DWMA for AMOVMC),
 * so VU_comb is read directly from it. Migrating the highest-load VM first brings
 * the host below the MWOHD threshold in the fewest migrations.</p>
 */
public class FutureAMOVMCVmSelection extends FutureVmSelectionBase {

	@Override
	public FutureVm getVmToMigrate(FutureHost host) {
		List<FutureVm> migratableVms = getMigratableVms(host);
		if (migratableVms.isEmpty()) {
			return null;
		}
		FutureVm vmToMigrate = null;
		double maxMetric = -Double.MAX_VALUE;
		for (FutureVm vm : migratableVms) {
			if (vm.getCurrentVm().isInMigration()) {
				continue;
			}
			double metric = vm.getForecastedMIPS(); // VU_comb (combined predicted load)
			if (metric > maxMetric) {
				maxMetric = metric;
				vmToMigrate = vm;
			}
		}
		return vmToMigrate;
	}
}
