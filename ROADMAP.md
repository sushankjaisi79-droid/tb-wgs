# PREVISGEN-TB roadmap

One task per Claude Code session. Each task ends with lint clean, regression test passing, a short summary for Sushank, and a commit he approves. Validation numbers for v0.1.0 must not change unless a task says so.

## Phase 1: before the conference (finish by 8 Dec 2026)

### 1. Replace the deprecated Streamlit call
`app.py` uses `st.components.v1.html`, which Streamlit warns "will be removed after 2026-06-01". Replace it with `st.iframe` (accepts a raw HTML string; `height` can be an int, "content" or "stretch"). Check the current Streamlit docs first.
Done when: no deprecation warnings in the terminal, reports render fully in the Run and Browse tabs, the report is not squeezed into half the page.

### 2. Raw-read QC report (side branch)
Add FASTP (bioinfo env) on each FASTQ pair, writing JSON/HTML reports only, and a MULTIQC step that combines them for the run. TBPROFILER must keep receiving the original FASTQ files. Publish to `pipeline_out/fastp/` and `pipeline_out/multiqc/`.
Done when: lint clean, MultiQC report opens and shows read counts, quality, adapter content and duplication; regression test passes; TBProfiler results for ERR1664619 are byte-identical apart from timestamps.

### 3. Run new samples from the app
The Run tab currently offers only isolates already in `data/validation/fastq`. Add a way to run a new sample: either FASTQ paths entered by the user or a scan of `data/incoming/` for `*_1/_2` or `*_R1/_R2` pairs. Validate that both files exist and are gzipped, sanitize the sample ID, and show clear errors.
Done when: a pair copied into `data/incoming/` can be run from the app and its report appears.

### 4. Regression test through the whole pipeline
Make sure `scripts/regression_test.sh` runs the pipeline on ERR1664619 in its own work dir and output dir, then checks lineage 4.3.4.2, Pre-XDR-TB, rpoB p.Ser450Leu, gyrA p.Asp94Ala, rrs n.1401A>G. If it already does, leave it alone and say so.
Done when: one command gives PASS/FAIL for all 5 checks from raw FASTQ.

### 5. Site update script
Write `scripts/update_site.sh` that copies `pipeline_out/reports/*.html` into the `../previsgen-site/reports/` worktree and shows `git status` there. It must not commit or push by itself.

### 6. Demo hardening
Confirm the app starts cleanly from a fresh terminal, a run of one isolate finishes, and the XDR example (ERR4796343) renders. List anything that could fail on the day.

## Phase 2: after the conference

- Nepali-language summary box in the report (Sushank must check every word with a native speaker; nothing clinical should be invented).
- Portability: replace absolute conda paths with Nextflow profiles (`-profile conda` and `-profile docker`), then containers for each process.
- GitHub Actions: lint and a tiny test on every push.
- ethA deletion cluster: test whether the 29 lineage 2.2.1 isolates are closely related (pairwise SNP distances from whole-genome variant calls). Possible transmission cluster; key result for the paper.
- Nanopore input support (check `tb-profiler profile --help` for the platform option).
- Contamination screen (Kraken2 or similar; database size is a constraint).
- Zenodo DOI: enable the Zenodo GitHub integration before creating the next GitHub release.
- Prospective validation on isolates from Nepali reference labs (needs faculty supervisor and ethics approval; not a coding task).
