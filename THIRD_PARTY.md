# Third-party components and their licenses

The MIT license in [LICENSE](LICENSE) covers the original code, configurations and documentation
written for this repository. The bundled simulator (`metacloud.jar`) and the Docker image
redistribute third-party software, each under **its own license**. This file lists the main
components so downstream users can comply.

| Component | Role | License (verify upstream) |
|-----------|------|---------------------------|
| **CloudSim** (cloudbus/CloudSim) | Discrete-event cloud simulation core that MetaCloudSim extends | LGPL — see upstream repository |
| **jpy** (bcdev/jpy) | Java↔Python bridge used to call the forecasting code | Apache License 2.0 |
| **Facebook Prophet** (`prophet`) | Time-series forecasting | MIT |
| **Stan / CmdStan** (via Prophet) | Bayesian back-end used by Prophet | BSD 3-Clause |
| **pandas, numpy, scipy, matplotlib** | Analysis stack in the image | BSD 3-Clause |
| **NeuralProphet, PyTorch** (optional, `Dockerfile.neural`) | Forecaster comparison only | MIT / BSD-3 |
| **OpenJDK 8**, **Python 3.8**, **Ubuntu 20.04** | Base toolchain | GPLv2+CE / PSF / various |

Notes:

- The exact version and license of each dependency are those resolved at image build time
  (`Dockerfile`, `environment/requirements_docker.txt`) and those bundled in `metacloud.jar`.
- **CloudSim** is the core simulation library. Its license (LGPL) governs redistribution of the
  simulator jar; redistributing it for scientific reproduction is standard practice, but if the
  group prefers a different repository-level license than MIT, adjust [LICENSE](LICENSE) and this
  file accordingly.
- Workload datasets are **not** software and keep their data licenses — see
  [workloads/DATA_LICENSES.md](workloads/DATA_LICENSES.md).
