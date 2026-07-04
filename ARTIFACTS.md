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
  [10.5281/zenodo.21197525](https://doi.org/10.5281/zenodo.21197525).

## Do I need it?

**No — not to reproduce.** The commands in [REPRODUCE.md](REPRODUCE.md) regenerate all of these
outputs from scratch inside Docker. This archive is provided only for convenience: to inspect the
exact per-seed numbers behind the paper's tables without re-running the campaign.

To use it, download the zip, unpack it at the repository root, and point the analysis scripts /
notebooks at `output/`.
