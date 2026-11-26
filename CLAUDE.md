# tb-wgs: project guide

## Goal
Nepal-specific TB whole-genome pipeline: FASTQ -> QC -> TBProfiler resistance calls -> report.
Research use only. A physician stays in the loop for any clinical reporting.

## Where we are
Read STATE.md first, every session. Update it at the end of every session.
The plan is in the doc "TB-WGS Validation: Plan, Phases and Handoff".

## Environment
Windows PC, WSL2 Ubuntu. All work runs inside WSL. Project folder: ~/projects/tb-wgs.
Tools: conda (env: bioinfo), TBProfiler, Nextflow, Docker. Versions are logged in logs/versions_*.txt.

## Layout
data/        raw data, never in git
runs/        one folder per run: runs/<date>_<tag>/ with command and versions saved
results_validation/  final tables and figures (tracked in git); results/ is scratch
docs/        abstract and notes
logs/        version logs and run logs
STATE.md     current phase, last result, next command

## Rules
1. Never commit data/, FASTQ files or anything from real patients. Public data only for now.
2. After the freeze tag, no changes to tool versions or parameters. A change means a new tag and a rerun of every isolate.
3. Make small changes and test after each one. Show the exact command and its output.
4. Claim accuracy only from a results table in results_validation/. No assumed numbers.
5. Run long jobs inside tmux.
6. Ask before any delete, overwrite or install. Say what and why. Use conda, apt or official docs, never a script piped from an unknown site.
7. Report errors and uncertainty plainly. Do not guess and move on.

## Validation plan
Reference: lab phenotype (R or S per drug; "." means excluded for that drug).
Metrics: per-drug sensitivity and specificity with 95% Wilson confidence intervals, plus counts.
Every discordant call is examined individually.

## Working style
The user is a first-year student. Explain why a step is needed, briefly. Be direct and critical.
