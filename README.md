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
conda activate tb-profiler &&# tb-wgs
A reproducible bioinformatics workflow for tuberculosis whole-genome sequencing analysis.
