# PREVISGEN-TB

Nextflow pipeline that turns paired-end Illumina FASTQ from *Mycobacterium tuberculosis* into a QC-gated drug-resistance report. First module of PREVISGEN, a genomics platform for Nepal. Current release: v0.1.0 (git tag). Research use only.

Author: Sushank Jaisi, first-year BSc Bioinformatics, Kathmandu University. He is learning as he builds: explain what you change and why in plain language, and teach rather than just do.

Deadlines: oral presentation at ICBSN 2026 / BIO-INSPIRE, Kathmandu, 17–18 Dec 2026. Longer term: a PLOS ONE paper on the validation.

## Environment

- Windows 11 + WSL2 Ubuntu 24.04. Repo at `~/projects/tb-wgs`. Remote: `git@github.com:sushankjaisi79-droid/tb-wgs.git`, branch `main`.
- Hardware: Ryzen 7 5700X (16 threads), 32 GB RAM.
- Nextflow 26.10.7 (strict syntax), needs Java 17: `NXF_JAVA_HOME` and `JAVA_HOME` point to `/usr/lib/jvm/java-17-openjdk-amd64` in `~/.bashrc`. The tb-profiler env ships Java 11, so never rely on the conda Java for Nextflow.
- Conda (Miniforge) envs:
  - `tb-profiler`: TBProfiler 6.7.0, database 7fe4364e, Trimmomatic 0.40, BWA, FreeBayes 1.3.9, Delly 1.3.3, Samtools 1.21.
  - `bioinfo`: Python 3.11, pandas, fastp, fastqc, multiqc, samtools, bcftools, pytest, jinja2, pyyaml, streamlit, altair, sra-tools.
- Exact versions: `docs/versions.txt`, `docs/env-tb-profiler.yml`, `docs/env-bioinfo.yml`.
- `nextflow.config` points to the conda envs by absolute path (`/home/usersushank/miniforge3/envs/...`). Known portability problem; see ROADMAP.md.
- Never ask the user to paste long text into the terminal (pastes get truncated). Edit files directly.

## Commands

```bash
conda activate bioinfo                                   # default env for working in the repo
nextflow lint .                                          # must be clean before any commit touching main.nf
nextflow run main.nf --samplesheet assets/samplesheet.csv -resume
nextflow run main.nf --samplesheet assets/all_samplesheet.csv -resume   # all 120 isolates (mostly cached)
bash scripts/regression_test.sh                          # 5 checks on ERR1664619, all must PASS
streamlit run app.py                                     # demo app, localhost:8501 only
python scripts/compare_calls.py && python scripts/nepal_stats.py        # recompute validation
```

Samplesheet format: `sample_id,fastq_1,fastq_2` (paths relative to repo root).

## Layout

- `main.nf`, `nextflow.config`: pipeline. Processes: TBPROFILER (cpus 8) -> QC_GATE -> REPORT -> REPORT_INDEX. Workflow uses `workflow { main: ... publish: ... }` plus an `output {}` block; outputs go to `pipeline_out/` (`tbprofiler/`, `qc/`, `reports/`).
- `bin/qc_gate.py`, `bin/make_report.py`: executable helpers, on PATH inside processes.
- `scripts/`: validation (build_panel.py, build_nepal_set.py, compare_calls.py, nepal_stats.py) and regression_test.sh.
- `app.py` + `.streamlit/config.toml`: Streamlit demo (tabs: Run a sample, Browse results, Validation). Run tab defaults to validation isolates; second option runs a pair from `data/incoming/` (git-ignored) into `runs/<ID>/`.
- `incoming.py`: pair detection, sample-ID sanitizing, quick checks and full gzip integrity check for `data/incoming/`. Tested by `tests/test_incoming.py` (`pytest tests/`).
- `assets/`: samplesheets. `results_validation/`: committed validation outputs and the timing benchmark.
- `data/` (FASTQ, ~240 files), `pipeline_out/`, `work*/`, `runs/`, `timing_out/`: git-ignored.
- `../previsgen-site`: git worktree of the `gh-pages` branch, served at https://sushankjaisi79-droid.github.io/tb-wgs/ (landing page + `reports/`).

## How the pipeline works (details that matter)

- TBProfiler does trimming, alignment to H37Rv, variant calling, large-deletion calling and catalogue lookup. We do not reimplement any of that.
- QC gate rules: FAIL if no lineage, <80% reads mapped, or median depth <10x. WARN for 80–90% mapped, 10–20x depth, core resistance gene coverage <95% (unless explained by a detected large deletion, which becomes a note), heteroresistance at 10–90%, and >=2 partial calls (possible mixed infection). A FAIL report never shows drug calls.
- Edits to `bin/` scripts do not invalidate the Nextflow cache, so REPORT and REPORT_INDEX take an md5 of `bin/make_report.py` as an input. Keep this pattern for any new bin script whose output should refresh on edit.
- Reports are self-contained offline HTML with the version stamp `PREVISGEN-TB v{version}` (`params.version`).

## Validation facts (frozen for v0.1.0)

116 Nepali CRyPTIC isolates (reuse table 20240917, HIGH-quality MIC phenotypes, WHO 2021 definitions), 1,216 drug-isolate comparisons, 97.0% agreement. RIF 89/89 and 27/27. INH 89/89 and 26/27. MXF specificity 18/33 (13 of 15 false-resistant carry gyrA A90V/D94A). 29 lineage 2.2.1 isolates share a large ethA deletion. QC over 120 isolates: 113 PASS, 7 WARN, 0 FAIL. Timing: 75–106 s per isolate at 8 threads, peak 3.3 GB. Source of truth: `results_validation/nepal_per_drug.csv`.

## Rules

- Never change what goes into TBPROFILER (inputs, parameters, database) without asking first. That would invalidate the validation. New analyses go in side branches of the workflow.
- After changing `main.nf` or `bin/`: run `nextflow lint .`, a pipeline run on `assets/samplesheet.csv`, and `scripts/regression_test.sh`. Report the results.
- Never delete or modify anything in `data/`, `pipeline_out/` or `results_validation/` unless asked.
- Use a separate work dir (`-w work_<name>`) for experiments so the main cache stays intact.
- Commit only when the user agrees, with a clear message. Ask before `git push`, before touching the `gh-pages` worktree, and before any history rewrite.
- Never commit FASTQ/BAM/VCF, secrets, or files over a few MB.
- Keep the research-use-only wording in reports, the app and the README.
- No real patient data enters this repo. Isolates from Nepali labs need ethics approval first.
- Streamlit stays bound to localhost with telemetry off.
- Check current docs before using an API you are unsure of (Nextflow strict syntax and Streamlit both change often).
- Writing (README, docs, report text): plain and human. No em-dash overuse, no filler like "moreover" or "it's important to note", no promotional phrases, no "it's not X, it's Y". Don't claim "first in Nepal".

## Roadmap

Prioritized tasks with acceptance criteria are in `ROADMAP.md`. Work on one task at a time.
