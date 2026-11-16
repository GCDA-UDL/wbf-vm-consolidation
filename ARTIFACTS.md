# Heavy run artifacts (archived outside git)

To keep the repository light and fast to clone, the **raw outputs and logs** of the full
simulation campaign are **not** stored in git. They are archived as a single compressed file:

- **File:** `wbf-vm-consolidation_run-outputs_v0.1.0.zip` (~404 MB compressed, ~3 GB uncompressed;
  12,276 files)
- **Contents:** `output/` (per-seed `*_data.json`, migrations CSVs, status logs),
  `logs/` (run logs) and `generatedExperiments/` (expanded per-seed configs) for the full campaign
  (4 workloads × techniques × 30 seeds, including the AMOVMC / EUQ-VMC comparison).

## Where to get it

<!-- Fill in the shared-cloud link and, after the release, the Zenodo record: -->
- **Shared cloud (group):** `<PASTE_ONEDRIVE_OR_SHARED_LINK_HERE>`
- **Zenodo (permanent):** the code release is archived at DOI
  [10.5281/zenodo.21197524](https://doi.org/10.5281/zenodo.21197524).

## Do I need it?

**Not to run the experiments.** The commands in [REPRODUCE.md](REPRODUCE.md) regenerate outputs of
the same kind from scratch inside Docker. The individual values of a re-execution differ from the
stored ones (see [results/reference/README.md](results/reference/README.md)), so the stored
outputs are needed to regenerate the exact numbers behind the tables of the manuscript with
`analysis_revision/`.

The archive named above was made for v0.1.0. The campaign behind the tables of the revised
manuscript (3,900 simulations, plus the native-placement and parameter-sweep runs) was executed
later; an archive of those outputs has to be added here before the release that accompanies the
revised manuscript. The raw outputs of the three experiments added by the revision (3,168
simulations and the forecast-accuracy computation, see
[experiments/revision_r1/README.md](experiments/revision_r1/README.md)) are not shipped in this
version either; that folder holds their run lists, tools and resulting tables.

Individual runs are not reproducible bit for bit (ties between equivalent candidates are resolved
by the iteration order of hash-based collections), so a re-execution is compared with the stored
campaign on means and confidence intervals, not run by run.

To use it, download the zip, unpack it at the repository root, and point the analysis scripts /
notebooks at `output/`.
