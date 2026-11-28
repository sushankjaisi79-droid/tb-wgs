# PREVISGEN-TB

Automated whole-genome sequencing pipeline that turns raw *Mycobacterium tuberculosis* sequencing reads into a quality-checked drug-resistance report, designed to run on a single desktop computer without internet access during analysis.

PREVISGEN-TB is the first module of PREVISGEN, a genomics platform built for Nepal's clinical and public-health context.

> **Research use only.** Genotypic predictions must be interpreted by a qualified clinician alongside phenotypic drug susceptibility testing. This is not a certified diagnostic device.

## What it does

For each sample (paired-end Illumina FASTQ), PREVISGEN-TB:

1. Predicts lineage and resistance to 20 anti-TB drugs with [TBProfiler](https://github.com/jodyphelan/TBProfiler), which trims, aligns to H37Rv, calls variants (including large deletions) and matches them against a WHO-based mutation catalogue.
2. Applies a QC gate (PASS / WARN / FAIL) covering lineage, read mapping, depth, coverage of resistance genes, large deletions and mixed infection.
3. Writes a self-contained HTML report per sample and a run summary page, both readable offline.
4. Offers a local web app for running samples, browsing results and viewing validation.

## Validation

Evaluated on 116 Nepali clinical isolates from the public CRyPTIC dataset, using high-quality broth microdilution (MIC) phenotypes. 1,216 drug–isolate comparisons, 97.0% agreement.

| Drug | Sensitivity | Specificity |
|---|---|---|
| Rifampicin | 89/89 (100%) | 27/27 (100%) |
| Isoniazid | 89/89 (100%) | 26/27 (96.3%) |
| Ethambutol | 34/34 (100%) | 21/23 (91.3%) |
| Levofloxacin | 80/81 (98.8%) | 25/27 (92.6%) |
| Moxifloxacin | 57/58 (98.3%) | 18/33 (54.5%) |
| Ethionamide | 27/29 (93.1%) | 48/49 (98.0%) |
| Kanamycin | 4/5 (80.0%) | 97/106 (91.5%) |
| Amikacin | 1/2 (50.0%) | 107/107 (100%) |

Notes:

- 13 of 15 false-resistant moxifloxacin calls carry gyrA A90V or D94A, mutations that confer low-level resistance often below the phenotypic test threshold.
- 29 lineage 2.2.1 isolates share one large ethA deletion; all 15 with an ethionamide phenotype were resistant and correctly predicted.
- Amikacin and kanamycin had too few resistant isolates for reliable estimates.
- The WHO catalogue was partly developed using CRyPTIC isolates, so accuracy on this dataset may be optimistic.

## Pipeline

```
FASTQ pair -> TBPROFILER -> QC_GATE -> REPORT -> REPORT_INDEX
```

Orchestrated with Nextflow; each step runs in its own pinned conda environment, and completed steps are cached and reused.

## Quick start

Requirements: Linux or WSL2 (Ubuntu 24.04 tested), Java 17, Nextflow 26.10, Miniforge.

```bash
# environments (exact versions are in docs/)
mamba env create -n tb-profiler -f docs/env-tb-profiler.yml
mamba env create -n bioinfo -f docs/env-bioinfo.yml
conda activate tb-profiler
tb-profiler update_tbdb

# run on a samplesheet with columns: sample_id,fastq_1,fastq_2
nextflow run main.nf --samplesheet assets/samplesheet.csv -resume

# local web app
conda activate bioinfo
streamlit run app.py
```

Outputs are written to `pipeline_out/`: `tbprofiler/` (raw results), `qc/` (verdicts), `reports/` (HTML; open `index.html`), `fastp/` (raw-read QC per sample) and `multiqc/` (raw-read QC for the whole run).

To run a new sample from the app, copy a gzipped FASTQ pair into `data/incoming/` (names like `NAME_R1.fastq.gz` / `NAME_R2.fastq.gz`, `NAME_1` / `NAME_2`, or Illumina `NAME_S1_L001_R1_001`), open the Run tab, choose "New sample from data/incoming/" and press Refresh. The app checks that both files are complete gzipped FASTQ before starting. Results go to `runs/NAME/`. Do not use patient data without ethics approval.

Note: `nextflow.config` currently points to conda environments by absolute path. Adjust these for your machine; container support is planned.

## Quality control rules

| Check | FAIL | WARN |
|---|---|---|
| *M. tuberculosis* lineage | none detected | two lineages, or non-*M. tuberculosis* |
| Reads mapped to H37Rv | below 80% | 80–90% |
| Genome median depth | below 10x | 10–20x |
| Coverage of key resistance genes | | below 95%, unless explained by a detected large deletion |
| Resistance mutations at 10–90% frequency | | heteroresistance; two or more suggests mixed infection |

## Repository layout

| Path | Contents |
|---|---|
| `main.nf`, `nextflow.config` | Pipeline definition and settings |
| `bin/` | QC gate and report generator, used by the pipeline |
| `scripts/` | Validation: panel selection, comparison, statistics, regression test |
| `app.py`, `incoming.py` | Streamlit app; finding and checking new FASTQ pairs in `data/incoming/` |
| `tests/` | Unit tests (`pytest tests/`) |
| `assets/` | Samplesheets |
| `docs/` | Environment files, tool versions, CRyPTIC data schema |
| `results_validation/` | Validation outputs |

## Credits and data

- TBProfiler: Phelan JE et al. *Genome Medicine* 11, 41 (2019); Coll F et al. *Genome Medicine* 7, 51 (2015). TBProfiler and the tools it bundles are distributed under their own licenses.
- Validation data: The CRyPTIC Consortium, *PLoS Biology* 20(8): e3001721 (2022), reuse table `CRyPTIC_reuse_table_20240917.csv`, licensed CC BY 4.0.
- Nextflow: Di Tommaso P et al. *Nature Biotechnology* 35, 316–319 (2017).

## Limitations

- Validated on public data only; prospective validation on isolates from Nepali reference laboratories has not yet been done.
- Predictions depend on the mutation catalogue version (TBProfiler 6.7.0, database 7fe4364e); novel resistance mechanisms are not detected.
- Absence of a known resistance mutation does not prove susceptibility.

## License

PREVISGEN-TB code is released under the MIT License. See `LICENSE`.

## Author

Sushank Jaisi, BSc Bioinformatics, Kathmandu University, Dhulikhel, Nepal.

<!-- end of README -->
