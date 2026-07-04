package svila.metricsLogic.CPUCalculator;

import java.util.List;

public class ForecastingTechniqueFactory {
	public static String last                    = "last";
	public static String autoArima               = "autoArima";
	public static String mean                    = "mean";
	public static String simpleExpSmoothing      = "simpleExpSmoothing";
	public static String holtExpSmoothing        = "holtExpSmoothing";
	public static String holtWintersExpSmoothing = "holtWintersExpSmoothing";
	public static String neuralProphet           = "neuralProphet";
	public static String fbProphet               = "fbProphet";
	public static String perc95                  = "perc95";
	public static String knn					 = "knn";
	public static String dwma					 = "dwma"; // SOTA: AMOVMC dynamic weighted moving average

	public static ForecastingTechnique getForecastingTechnique(String ForecastingTechniqueType) {
		switch(ForecastingTechniqueType) {
		case "last":
			return new LastForecastingTechnique();
		case "dwma": // SOTA comparison: AMOVMC predictor (Goyal & Awasthi 2025)
			return new DWMAForecastingTechnique();
		case "autoArima":
			return new AutoArimaForecastingTechnique();
		case "mean":
			return new MeanForecastingTechnique();
		case "simpleExpSmoothing":
			return new SimpleExpSmoothingForecastingTechnique();
		case "holtExpSmoothing":
			return new HoltExpSmoothingForecastingTechnique();
		case "holtWintersExpSmoothing":
			return new HoltWintersExpSmoothingForecastingTechnique();
		case "neuralProphet":
			return new NeuralProphetForecastingTechnique();
		case "fbProphet":
			return new FBProphetForecastingTechnique();
		case "knn":
			return new KNNForecastingTechnique();
		case "perc95":
			return new Perc95ForecastingTechnique();
		case "percX":
			return new PercXForecastingTechnique();
		default:
			System.err.println("Unknown ForecastingTechnique: " + ForecastingTechniqueType);
            System.exit(-1);
            return null;
		}
	}
}
