package svila.policiesHostOverSaturation.future;

import svila.planetlabNetwork.StaticResources;
import svila.policiesVmOptimizer.future.FutureHost;

/**
 * AMOVMC Multi-Weight Overutilised Host Detection (MWOHD).
 *
 * Goyal &amp; Awasthi, "Adaptive Multi-Objective Virtual Machine Consolidation for
 * Energy-Efficient Cloud Data Centers", J. Grid Computing 23:21, 2025 — Section 4.1,
 * Algorithm 2 and Equation (11).
 *
 * <p>MWOHD flags a host as over-utilised when the predicted <em>performance</em>
 * (mapped from the predicted CPU utilisation and the number of co-located VMs by
 * Eq. 11) drops below the QoS threshold gamma. Eq. 11 is:</p>
 *
 * <pre>
 *   u_th = (1.0489 - 0.01 * V_n - 0.3288 * u_j) / 0.9509      if u_j &lt;= 0.80
 *          (1.5459 - 0.005 * V_n - 1.2074 * u_j) / 0.9559      if u_j &gt;  0.80
 * </pre>
 *
 * <p>where u_j is the (forecasted) host CPU utilisation and V_n the number of VMs.
 * The host is over-utilised when u_th &lt; gamma.</p>
 *
 * <p>To keep the detection consistent with the migration-selection loop of the
 * "future" pipeline — which migrates VMs while {@code futureUtilization &gt;
 * upperThreshold} (see {@code FutureVmSelectionBase.getVmsToMigrateWithFirstCheck})
 * — we invert Eq. 11 at the performance point gamma to obtain the equivalent
 * <em>utilisation</em> threshold u_crit (the utilisation at which performance == gamma):</p>
 *
 * <pre>
 *   u_crit = (1.0489 - 0.01 * V_n - 0.9509 * gamma) / 0.3288   (low-load branch)
 *   u_crit = (1.5459 - 0.005 * V_n - 0.9559 * gamma) / 1.2074  (high-load branch, if u_crit &gt; 0.80)
 * </pre>
 *
 * <p>The host is over-utilised iff forecasted utilisation &gt; u_crit, and the
 * selection loop migrates VMs until utilisation falls back below u_crit. This is
 * mathematically equivalent to the performance test u_th &lt; gamma while reusing
 * the unchanged consolidation loop, so AMOVMC runs in the same CloudSim
 * energy/SLA harness as the baselines and WBF.</p>
 */
public class FutureHostOverSaturationAMOVMC extends FutureHostOverSaturationBase {

	/** QoS performance threshold gamma (Eq. 11). Performance below gamma => overloaded.
	 *  The paper ties this to the 500 ms response-time SLA point (performance ~0.80). */
	private final double gamma;

	public FutureHostOverSaturationAMOVMC(double gamma) {
		super();
		this.gamma = gamma;
	}

	/** Inverts Eq. 11 at performance == gamma to get the critical utilisation. */
	private double criticalUtilization(int vmCount) {
		// low-load branch (u_j <= 0.80)
		double uCrit = (1.0489 - 0.01 * vmCount - 0.9509 * gamma) / 0.3288;
		if (uCrit > 0.80) {
			// high-load branch (u_j > 0.80)
			uCrit = (1.5459 - 0.005 * vmCount - 0.9559 * gamma) / 1.2074;
		}
		// keep the threshold in a sane (0,1.5] range
		if (uCrit < 0.0) uCrit = 0.0;
		return uCrit;
	}

	@Override
	public OverSaturationData getOverSaturationData(FutureHost host) {
		// PM_util: forecasted host CPU utilisation (sum of the VMs' forecasts), Algorithm 2
		double utilization = host.getForecastedPercCPUWithMigrations();
		int vmCount = host.getFutureVms().size();

		double uCrit = criticalUtilization(vmCount);

		// log the dynamic threshold like the other policies do
		this.vmOptimizerPolicy.migrationStatistics.addHistoryEntry(host.getCurrentHost(), uCrit);

		OverSaturationData osd = new OverSaturationData(host, uCrit, utilization);
		// existUpperThresholdSaturation is set by the constructor to (utilization > uCrit),
		// which is exactly the AMOVMC rule (performance u_th < gamma). existSaturationOver100Perc
		// stays bound to the real forecasted utilisation. No override needed.
		return osd;
	}
}
