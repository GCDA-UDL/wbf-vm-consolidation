package svila.policiesFactories.future;

import org.cloudbus.cloudsim.power.PowerVmSelectionPolicy;

import svila.planetlabNetwork.StaticResources;
import svila.planetlabNetwork.correlation.PearsonMathCorrelation;
import svila.planetlabNetwork.results.CorrelationsResults;
import svila.policiesFactories.IVMSelectionPolicyFactory;
import svila.policiesFactories.VMSelectionPolicyFactory;
import svila.policiesVmSelection.MinimumMigrationTimeVmSelection;
import svila.policiesVmSelection.PSP2VmSelection;
import svila.policiesVmSelection.future.FutureAMOVMCVmSelection;
import svila.policiesVmSelection.future.FutureEUQVMCVmSelection;
import svila.policiesVmSelection.future.FutureCompatibilityVmSelection;
import svila.policiesVmSelection.future.FutureMaximumCorrelationVMSelection;
import svila.policiesVmSelection.future.FutureMinimumMigrationTimeVmSelection;
import svila.policiesVmSelection.future.FutureMinimumUtilizationTimeVmSelection;
import svila.policiesVmSelection.future.FutureNoVmSelection;
import svila.policiesVmSelection.future.FuturePSP2VmSelection;
import svila.policiesVmSelection.future.FutureRandomSearchVmSelection;
import svila.policiesVmSelection.future.FutureVmSelectionBase;
import svila.vmOptimizerFix.VMSelectionPolicy;

public class FutureVmSelectionPolicyFactory implements IVMSelectionPolicyFactory {

	public String getVersion() {
		return "v3";
	}
	
    public static FutureVmSelectionBase getFutureVmSelectionPolicy(String vmSelectionPolicyName) {
        
        if(vmSelectionPolicyName.isEmpty()) {
            return null;
        }
        
        /* Not active
        if(vmSelectionPolicyName.startsWith("compat-")) {
        	String name = vmSelectionPolicyName.split("-")[1];
        	VMSelectionPolicy policy = new VMSelectionPolicyFactory().getVmSelectionPolicy(name);
        	return new FutureCompatibilityVmSelection(policy);
        }
        */
        
        switch(vmSelectionPolicyName) {
        	case "rs":
        		FutureRandomSearchVmSelection rs = new FutureRandomSearchVmSelection();
        		return rs;
        	case "mu":
        		FutureMinimumUtilizationTimeVmSelection mu = new FutureMinimumUtilizationTimeVmSelection();
        		return mu;
        	case "mmt":
        		FutureMinimumMigrationTimeVmSelection mmt = new FutureMinimumMigrationTimeVmSelection();
        		return mmt;
        	case "mc":
        		FutureMaximumCorrelationVMSelection mc = new FutureMaximumCorrelationVMSelection(new FutureMinimumMigrationTimeVmSelection());
        		return mc;
        	case "psp2":
        		new CorrelationsResults().start();
        		FuturePSP2VmSelection psp2 = new FuturePSP2VmSelection(
        				new PearsonMathCorrelation(),
        				new FutureMinimumMigrationTimeVmSelection());
        		return psp2;
        	case "nm":
        		FutureNoVmSelection nm = new FutureNoVmSelection();
        		return nm;
        	case "amovmc": // SOTA: AMOVMC modified VM selection (Goyal & Awasthi 2025, Algorithm 3)
        		return new FutureAMOVMCVmSelection();
        	case "euqvmc": // SOTA: EUQ-VMC ROS selection (Li et al. 2025, Eq. 24)
        		return new FutureEUQVMCVmSelection();
        	default:
                String errorMessage = "Future VM Policy Factory: Unknown VM selection policy: " + vmSelectionPolicyName;
                StaticResources.throwRuntimeException(new ClassNotFoundException(errorMessage), errorMessage);
                return null;
        }
        
        /*switch(vmSelectionPolicyName){
        	case "rs":
        		return new RandomSearchVmSelection();
        	case "mu":
                return new MinimumUtilizationVmSelection();
        	case "mmt":
        		return new MinimumMigrationTimeVmSelection();
        	case "mc":
        		return new MaximumCorrelationVMSelection(new MinimumMigrationTimeVmSelection());
        	case "nm":
            	return new NoVmSelection();
        	case "psp2":
        		new CorrelationsResults().start();
            	return new PSP2VmSelection(
        				new PearsonMathCorrelation(),
        				new MinimumMigrationTimeVmSelection()
        				);
            default:
                System.out.println("Power VM Policy Factory: Unknown VM selection policy: " + vmSelectionPolicyName);
                System.exit(0);
                return null;
        }*/
    }

	@Override
	public PowerVmSelectionPolicy getVmSelectionPolicy(String vmSelectionPolicyName) {
		return null;
	}
}
