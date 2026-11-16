# TODO before / around publication

- [ ] **Zenodo DOI**: enable the GitHub↔Zenodo integration for `GCDA-UDL/wbf-vm-consolidation`,
      create the `v0.1.0` release, then paste the minted DOI into:
      - `README.md` (uncomment the DOI badge, replace `XXXXXXX`)
      - `ARTIFACTS.md` (Zenodo line)
      - the paper (replaces the `<pendiente_zenodo>` placeholder).
- [ ] **Shared-cloud link** for the heavy artifacts zip → fill into `ARTIFACTS.md`.
- [ ] **Funding check (FACTOS / shared project)**: the MICIU statement
      (`PID2023-146193OB-I00`) is included. FACTOS is a joint UAB + UdL project; if any UAB-side
      or fire-line grant (e.g. CPP2021-008762, CPP2024-011726) applies to this specific output,
      confirm with the UAB partners and add it to the funding section. Otherwise leave as is.
- [ ] **License sign-off**: confirm with the group that MIT (for our code) + third-party notice
      is acceptable given CloudSim's LGPL (see `THIRD_PARTY.md`).
- [x] The ten PlanetLab daily subsets used by the manuscript are shipped under
      `workloads/planetlab/`.
- [ ] **Release for the revised manuscript**: decide the version number and set `version` and
      `date-released` in `CITATION.cff` (affiliation and preferred-citation note are already
      updated), move the `Unreleased` section of `CHANGELOG.md` under that version, archive the
      raw outputs of the campaign behind the revised tables (or ship the per-run cache of
      `analysis_revision/`), and update `ARTIFACTS.md`.
- [ ] **Raw outputs of the experiments of the revision** (`experiments/revision_r1/`): 3,168
      simulations, their logs (the decision times are read from `runlogs/t1timing/_timing.log`)
      and the per-run cache are not shipped. Decide whether to archive them with the release.
- [ ] **Smoke test before the release**: execute `experiments/revision_r1/tools/start_campaign.sh`
      (for example with `lists/t1_smoke.txt`), `start_fa.sh` and `collect.sh` from this repository
      layout; their paths were adapted to the repository and they have not been executed in it.
      Run the scripts of `analysis_revision/` with the Python 3.8 of the image.
