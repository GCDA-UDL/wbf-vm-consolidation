# TODO before / around publication

- [x] **Zenodo DOI**: GitHub↔Zenodo integration enabled; concept DOI
      [10.5281/zenodo.21197524](https://doi.org/10.5281/zenodo.21197524), cited in `README.md`,
      `ARTIFACTS.md` and the paper.
- [ ] **Shared-cloud link** for the heavy artifacts zip → fill into `ARTIFACTS.md`.
- [ ] **Funding check (FACTOS / shared project)**: the MICIU statement
      (`PID2023-146193OB-I00`) is included. FACTOS is a joint UAB + UdL project; if any UAB-side
      or fire-line grant (e.g. CPP2021-008762, CPP2024-011726) applies to this specific output,
      confirm with the UAB partners and add it to the funding section. Otherwise leave as is.
- [ ] **License sign-off**: confirm with the group that MIT (for our code) + third-party notice
      is acceptable given CloudSim's LGPL (see `THIRD_PARTY.md`).
- [x] The ten PlanetLab daily subsets used by the manuscript are shipped under
      `workloads/planetlab/`.
- [x] **Release for the revised manuscript**: v0.3.0, then v0.3.1 (fixes of the launchers of the
      additional traces), with the per-run caches of the revision in `caches/` (see `CHANGELOG.md`).
- [ ] **Raw outputs of the experiments of the revision** (`experiments/revision_r1/`): the simulations,
      their logs and the raw outputs are not shipped; the per-run records from which the tables are
      computed are (`caches/`). Decide whether to archive the raw outputs elsewhere.
- [ ] **Smoke test of the remaining launchers**: `mt_smoke.sh` was executed from this layout (v0.3.1,
      see `experiments/revision_r1/README.md`); `start_campaign.sh` (for example with
      `lists/t1_smoke.txt`), `start_fa.sh` and `collect.sh` have not been executed in it yet.
      Run the scripts of `analysis_revision/` with the Python 3.8 of the image.
