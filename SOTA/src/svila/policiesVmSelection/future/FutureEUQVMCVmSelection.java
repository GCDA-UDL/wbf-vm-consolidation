package svila.policiesVmSelection.future;

import java.util.List;

import svila.policiesVmOptimizer.future.FutureHost;
import svila.policiesVmOptimizer.future.FutureVm;

/**
 * EUQ-VMC Resource-Overload-based VM Selection (ROS), Algorithm 4 / Equation (24)
 * of Li et al., "Resource-Efficient and Quality-Aware Virtual Machine
 * Consolidation Method", J. Grid Computing 23:6, 2025 — Section 5.2.
 *
 * <p>ROS ranks the VMs of an overloaded host by their migration probability</p>
 *
 * <pre>
 *   P_mig_i = U_i^res / vm_i.getRam()
 * </pre>
 *
 * <p>and migrates the VM with the largest P_mig first (high utilisation per unit
 * of RAM transferred), repeating until the host's utilisation drops to or below
 * the overload threshold T_upper (handled by the surrounding selection loop).</p>
 *
 * <p>U_i^res is taken as the VM's forecasted CPU demand (MIPS) in the "future"
 * pipeline, so EUQ-VMC runs under the identical CloudSim energy/SLA model as the
 * baselines and WBF.</p>
 */
public class FutureEUQVMCVmSelection extends FutureVmSelectionBase {

	@Override
	public FutureVm getVmToMigrate(FutureHost host) {
		List<FutureVm> migratableVms = getMigratableVms(host);
		if (migratableVms.isEmpty()) {
			return null;
		}
		FutureVm vmToMigrate = null;
		double maxPmig = -Double.MAX_VALUE;
		for (FutureVm vm : migratableVms) {
			if (vm.getCurrentVm().isInMigration()) {
				continue;
			}
			double ram = vm.getCurrentVm().getRam();          // MB
			if (ram <= 0) ram = 1;                             // guard
			double pMig = vm.getForecastedMIPS() / ram;       // Eq. 24
			if (pMig > maxPmig) {
				maxPmig = pMig;
				vmToMigrate = vm;
			}
		}
		return vmToMigrate;
	}
}
