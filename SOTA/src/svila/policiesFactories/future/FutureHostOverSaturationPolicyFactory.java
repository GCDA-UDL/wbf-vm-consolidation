package svila.policiesFactories.future;

import svila.metricsLogic.CPUCalculator.ForecastingTechnique;
import svila.metricsLogic.CPUCalculator.ForecastingTechniqueFactory;
import svila.metricsLogic.CPUCalculator.SignalProcessingMethod;
import svila.metricsLogic.CPUCalculator.SignalProcessingMethodFactory;
import svila.planetlabNetwork.ExperimentConfiguration;
import svila.planetlabNetwork.StaticResources;
import svila.policiesFactories.GeneralPolicyFactory;
import svila.policiesFactories.HostOverSaturationPolicyFactory;
import svila.policiesHostOverSaturation.HostOverSaturationEverTrue;
import svila.policiesHostOverSaturation.HostOverSaturationIQR;
import svila.policiesHostOverSaturation.HostOverSaturationLR;
import svila.policiesHostOverSaturation.HostOverSaturationLRR;
import svila.policiesHostOverSaturation.HostOverSaturationMAD;
import svila.policiesHostOverSaturation.HostOverSaturationSmoothingForecasting;
import svila.policiesHostOverSaturation.HostOverSaturationTHR;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationAMOVMC;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationEUQVMC;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationBase;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationEverFalse;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationEverTrue;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationIQR;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationLR;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationLRR;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationMAD;
import svila.policiesHostOverSaturation.future.FutureHostOverSaturationTHR;
import svila.vmOptimizerFix.HostOverSaturationPolicy;

public class FutureHostOverSaturationPolicyFactory {

	public static FutureHostOverSaturationBase getFutureHostOverSaturationPolicy(String hostOverSaturationPolicyName) {	
        if(hostOverSaturationPolicyName.isEmpty()) {
            return null;
        }
        
        double safetyParameter = Double.parseDouble(StaticResources.getCE().getParameter());
        double utilizationThreshold = StaticResources.getCE().getUtilizationThreshold();
        
        switch(hostOverSaturationPolicyName){
        	case "iqr":
        		FutureHostOverSaturationIQR iqr = new FutureHostOverSaturationIQR(
        				safetyParameter,
        				FutureHostOverSaturationPolicyFactory.getFutureHostOverSaturationPolicy("thr")
        			);
        		return iqr;
        	case "thr":
        		FutureHostOverSaturationTHR thr = new FutureHostOverSaturationTHR(utilizationThreshold);
        		return thr;
        	case "mad":
        		FutureHostOverSaturationMAD mad = new FutureHostOverSaturationMAD(
        				safetyParameter,
        				FutureHostOverSaturationPolicyFactory.getFutureHostOverSaturationPolicy("thr")
        				);
        		return mad;
        	case "lr":
        		FutureHostOverSaturationLR lr = new FutureHostOverSaturationLR(
        				safetyParameter,
        				10,
        				6,
        				FutureHostOverSaturationPolicyFactory.getFutureHostOverSaturationPolicy("thr")
        				);
        		return lr;
        	case "lrr":
        		FutureHostOverSaturationLRR lrr = new FutureHostOverSaturationLRR(
        				safetyParameter,
        				10,
        				6,
        				FutureHostOverSaturationPolicyFactory.getFutureHostOverSaturationPolicy("thr")
        				);
        		return lrr;
        	case "et":
        		FutureHostOverSaturationEverTrue ev = new FutureHostOverSaturationEverTrue();
        		return ev;
        	case "ef":
        		FutureHostOverSaturationEverFalse ef = new FutureHostOverSaturationEverFalse();
        		return ef;
        	case "amovmc": // SOTA: AMOVMC MWOHD (Goyal & Awasthi 2025, Eq. 11). gamma=0.80 (500ms SLA point)
        		return new FutureHostOverSaturationAMOVMC(0.80);
        	case "amovmcg": // SOTA tuning variant: AMOVMC MWOHD with gamma read from config 'parameter'
        		return new FutureHostOverSaturationAMOVMC(safetyParameter);
        	case "euqvmc": // SOTA: EUQ-VMC HOD (Li et al. 2025, Eq. 4+23). safe = parameter
        		return new FutureHostOverSaturationEUQVMC(safetyParameter);
        	default:
                String errorMessage = "FutureHostOverSaturationPolicy Factory: Unknown FutureHostOverSaturationPolicy: " + hostOverSaturationPolicyName;
                StaticResources.throwRuntimeException(new ClassNotFoundException(errorMessage), errorMessage);
                return null;
        }
    }
}
