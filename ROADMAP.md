# PREVISGEN-TB roadmap

Goal: a tool that a Nepali TB reference laboratory can install, run on real isolates and trust, with every result traceable to its inputs, software and database versions.

Until the validation in Phase 5 is done and approved, every report stays "Research use only". Software alone cannot make a result clinical; validation in a lab, under a supervisor, can.

## How we work

- One task per Claude Code session. Plan mode first; Sushank approves the plan.
- All new work goes on a feature branch named after the task (`feat/07-housekeeping`, `feat/09-containers`, ...), never directly on `main`. Merge only when the task's "Done when" is met and Sushank approves.
- Every task ends with: `nextflow lint .` clean, `pytest tests/` passing, `bash scripts/regression_test.sh` passing, a short summary in plain language, and a commit Sushank approves.
- Never change what feeds TBPROFILER (inputs, parameters, database) inside a task that does not say so. A change that can alter calls gets its own task, a new version number and a re-run of the validation.
- Version numbers: v0.2.0 = conference version. Each merged phase raises the minor version. v1.0.0 only after Phase 5.

## Phase 1: conference demo (done)

1. Replace deprecated Streamlit call. Done.
2. Raw-read QC side branch (fastp + MultiQC). Done.
3. Run new samples from `data/incoming/`. Done.
4. Regression test runs the full pipeline. Done.
5. Site update script. Done.
6. Demo hardening. Done except: Windows browser test with Wi-Fi off (rehearsal day). After it passes, tag `v0.2.0`.

## Phase 2: engineering foundation (installs anywhere, tested automatically)

### 7. Housekeeping
- In CLAUDE.md, the all-samples command resumes the main session explicitly (`-resume e4c044eb-200c-454f-92a5-55d6d6d2cb2e`) and notes that a bare `-resume` after the regression test re-runs everything.
- Done when: CLAUDE.md updated and committed.

### 8. Configuration without absolute paths
- Move machine-specific settings out of `nextflow.config` into profiles: `-profile conda` (current envs, paths from params or env vars), `-profile docker`, `-profile singularity` (Apptainer, common on lab servers).
- Resource settings (`cpus`, `memory`) as params with safe defaults for an 8 GB machine.
- Done when: no `/home/usersushank` anywhere in the repo, and the pipeline runs with `-profile conda` exactly as before (regression test passes, validation calls unchanged).

### 9. Containers
- One pinned container per environment: TBProfiler 6.7.0 with database 7fe4364e inside, and one for Python/fastp/MultiQC. Use existing BioContainers images where they match the pinned versions; build our own only where needed, with the Dockerfile in `containers/`.
- Record image digests (not just tags) in `docs/versions.txt`.
- Done when: on a clean machine (or a fresh WSL distro) with only Docker and Nextflow installed, `nextflow run main.nf -profile docker,test` passes, and ERR1664619 gives the same 5 regression results.

### 10. Small test dataset and `-profile test`
- A subsampled read pair (a few MB) that still triggers known resistance calls, stored outside git if over a few MB (Zenodo or a GitHub release asset) and downloaded by the test profile.
- Done when: `nextflow run main.nf -profile docker,test` finishes in under 5 minutes and checks expected results.

### 11. Input validation
- Samplesheet checked before anything runs: header, unique sample IDs, safe characters, files exist, are gzipped FASTQ, R1/R2 names match. Clear error messages that say what to fix.
- Done when: pytest covers each bad-input case, and a bad samplesheet fails in seconds with a readable message.

### 12. Continuous integration
- GitHub Actions on every push and pull request: lint, pytest, and the test profile with Docker.
- Done when: a green check appears on GitHub for `main`, and a deliberately broken test turns it red.

## Phase 3: analytical robustness (results a lab can trust and trace)

### 13. Audit trail in every report and in a machine-readable file
- Run ID, date and time, operator name (param), pipeline version and git commit, container digests, TBProfiler and database versions, MD5 checksums of both input FASTQ files, all params.
- Same information in `<sample>.provenance.json`.
- Done when: two runs of the same input give identical provenance apart from date and run ID, and a changed input file changes the checksum shown.

### 14. Species and contamination check
- Confirm the sample is M. tuberculosis complex and estimate contamination before trusting calls. Compare options (TBProfiler's own species output, a small Kraken2 database, Mash) for size, speed and offline use; pick one and justify it in `docs/`.
- QC gate: FAIL for non-MTBC, WARN above a contamination threshold.
- Done when: a mixed test sample (MTBC plus non-TB reads) is flagged, and the validation isolates are unaffected.

### 15. Confidence and low-level resistance in the report
- Show each mutation's WHO catalogue grading. Flag known low-level mutations (e.g. gyrA A90V, D94A for moxifloxacin) with plain wording a clinician can act on.
- Done when: the 13 MXF discordant isolates show the low-level flag, and the wording is reviewed by Sushank and his supervisor.

### 16. Analytical performance experiments (also paper material)
- Depth: downsample validation isolates (10x, 15x, 20x, 30x, 50x) and measure how calls change. Use the result to justify the QC depth thresholds.
- Heteroresistance: mix reads of a resistant and a susceptible isolate in silico (5%, 10%, 25%, 50%) and find the lowest fraction detected.
- Reproducibility: run the same isolates three times, on different days and machines; calls must be identical.
- Done when: scripts in `scripts/analytical/`, tables in `results_validation/analytical/`, and a short write-up in `docs/analytical_performance.md`.

### 17. Second opinion for disagreements
- Run Mykrobe alongside TBProfiler; flag any drug where they disagree for manual review. Never merge calls automatically.
- Done when: concordance across the 116 isolates is reported, and each disagreement shows in the report as "needs review".

### 18. Catalogue updates without silent drift
- One script that installs a new TBProfiler database into a new version folder, re-runs the 116-isolate validation, and prints old vs new accuracy per drug.
- Done when: running it produces a comparison table, and nothing changes in production until the new version is approved.

## Phase 4: usable by lab staff

### 19. Report for the laboratory
- Lab fields: lab sample ID, specimen type, date received, sequencing run, analyst, reviewer and sign-off. Interpretation wording aligned with WHO guidance. PDF output alongside HTML.
- Nepali-language summary, with the text kept in one file so a native speaker and a clinician can check every sentence. Sushank approves the wording before it ships.
- Done when: a printed PDF of one report is reviewed by Sushank's supervisor.

### 20. Batch runs and exports
- A summary for a whole sequencing batch, and a CSV export with stable column names, suitable for a lab information system or Excel.
- Done when: a 10-isolate batch produces one summary page and one CSV that opens cleanly in Excel.

### 21. Data protection
- Only pseudonymised sample IDs in file names, reports and logs; input validation refuses names that look like personal data; nothing leaves the machine.
- Done when: documented in `docs/data_protection.md` and enforced by input validation.

### 22. Nanopore input (experimental)
- Accept long reads using TBProfiler's platform option. Label every Nanopore report "experimental, not validated" until Nepali Nanopore data with phenotypes is available.
- Done when: public Nanopore TB data runs end to end, and the label appears.

### 23. Documentation for lab staff
- Installation guide, user manual, troubleshooting, and a draft standard operating procedure (SOP) in `docs/`.
- Done when: someone other than Sushank installs and runs it using only the docs, and their questions are fixed in the docs.

## Phase 5: validation for real use (supervisor-led, not coding)

### 24. Validation plan and approvals
- Written with the faculty supervisor: intended use, accuracy against phenotypic DST, reproducibility, depth and mixture limits (from task 16), acceptance criteria.
- Ethics approval (NHRC) before any patient-derived isolate is used. Agreement with a reference laboratory (NTCC or NPHL).
- Find out with the supervisor what Nepal requires before software is used to inform treatment.

### 25. Prospective validation on fresh Nepali isolates
- Run blinded against the lab's phenotypic results. Per-drug sensitivity and specificity with confidence intervals.
- Done when: results meet the acceptance criteria in task 24 and are written up for PLOS ONE. Only then v1.0.0, and the research-use-only wording is revisited with the lab.
