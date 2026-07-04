package svila.policiesFactories.future;

import svila.planetlabNetwork.StaticResources;
import svila.policiesVmMigration.future.FutureAbsoluteCapacityVmMigrationPolicy;
import svila.policiesVmMigration.future.FutureAMOVMCPlacement;
import svila.policiesVmMigration.future.FutureEUQVMCPlacement;
import svila.policiesVmMigration.future.FutureDefaultVMMigrationPolicy;
import svila.policiesVmMigration.future.FutureDemandRiskVmMigrationPolicy;
import svila.policiesVmMigration.future.FutureGuazzoneBFDVmMigrationPolicy;
import svila.policiesVmMigration.future.FutureLagoVmMigrationPolicy;
import svila.policiesVmMigration.future.FutureMDGVmMigrationPolicy;
import svila.policiesVmMigration.future.FutureMWFDVPVmMigrationPolicy;
import svila.policiesVmMigration.future.FuturePercentageUtilVmMigrationPolicy;
import svila.policiesVmMigration.future.FutureSWFDVPVmMigrationPolicy;
import svila.policiesVmMigration.future.FutureVmMigrationPolicyBase;
import svila.policiesVmMigration.future.markov.FutureMPABFDVmMigrationPolicy;

public class FutureVmMigrationPolicyFactory {
public static FutureVmMigrationPolicyBase getVmMigrationPolicy(String VmMigrationPolicyFactoryName) {
        
        if(VmMigrationPolicyFactoryName.isEmpty()) {
            return null;
        }
        
        switch(VmMigrationPolicyFactoryName){
        	case "def":
        		FutureDefaultVMMigrationPolicy def = new FutureDefaultVMMigrationPolicy();
        		return def;
        	case "mdg":
        		FutureMDGVmMigrationPolicy mdg = new FutureMDGVmMigrationPolicy();
        		return mdg;
        	case "ac":
        		FutureAbsoluteCapacityVmMigrationPolicy ac = new FutureAbsoluteCapacityVmMigrationPolicy();
        		return ac;
        	case "amovmcfit": // SOTA native placement: AMOVMC fitness (Goyal & Awasthi 2025, Eq. 20)
        		return new FutureAMOVMCPlacement();
        	case "euqmofpad": // SOTA native placement: EUQ-VMC 3-objective greedy (Li et al. 2025, Eq. 3/8/4)
        		return new FutureEUQVMCPlacement();
        	case "dr":
        		FutureDemandRiskVmMigrationPolicy dr = new FutureDemandRiskVmMigrationPolicy();
        		return dr;
        	case "bfd":
        		FutureGuazzoneBFDVmMigrationPolicy bfd = new FutureGuazzoneBFDVmMigrationPolicy();
        		return bfd;
        	case "lago":
        		FutureLagoVmMigrationPolicy lago = new FutureLagoVmMigrationPolicy();
        		return lago;
        	case "mwfdvp":
        		FutureMWFDVPVmMigrationPolicy mwfdvp = new FutureMWFDVPVmMigrationPolicy();
        		return mwfdvp;
        	case "swfdvp":
        		FutureSWFDVPVmMigrationPolicy swfdvp = new FutureSWFDVPVmMigrationPolicy();
        		return swfdvp;
        	case "pu":
        		FuturePercentageUtilVmMigrationPolicy pu = new FuturePercentageUtilVmMigrationPolicy();
        		return pu;
        	case "markov":
        		FutureMPABFDVmMigrationPolicy markov = new FutureMPABFDVmMigrationPolicy();
        		return markov;
        	default:
        		String errorMessage = "FutureVmMigrationPolicy Factory: Unknown FutureVmMigrationPolicy: " + VmMigrationPolicyFactoryName;
                StaticResources.throwRuntimeException(new ClassNotFoundException(errorMessage), errorMessage);
                return null;
        }
    }
}
