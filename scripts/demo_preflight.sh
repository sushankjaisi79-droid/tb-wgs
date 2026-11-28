#!/bin/bash
# Demo preflight: quick read-only checks before starting the app for a talk.
# It changes nothing. Run it from a fresh terminal after `conda activate bioinfo`:
#
#   bash scripts/demo_preflight.sh
#
# Every line prints PASS or FAIL. Fix every FAIL before the demo (see
# docs/DEMO_CHECKLIST.md).

cd "$(dirname "$0")/.." || exit 1

DEMO=ERR4796343
fails=0
pass () { echo "PASS  $1"; }
fail () { echo "FAIL  $1"; fails=$((fails + 1)); }
check () { if eval "$2" >/dev/null 2>&1; then pass "$1"; else fail "$1${3:+  ($3)}"; fi; }

echo "PREVISGEN-TB demo preflight ($(date '+%F %H:%M'))"

# Software
check "bioinfo env is active" '[ "$CONDA_DEFAULT_ENV" = bioinfo ]' "run: conda activate bioinfo"
check "streamlit on PATH" 'command -v streamlit'
check "nextflow on PATH" 'command -v nextflow' "open a new terminal so ~/.bashrc runs"
check "NXF_JAVA_HOME points to Java 17" '[[ "$NXF_JAVA_HOME" == *java-17* ]] && [ -x "$NXF_JAVA_HOME/bin/java" ]'
check "nextflow starts" 'nextflow -version'
check "tb-profiler conda env exists" '[ -x "$HOME/miniforge3/envs/tb-profiler/bin/tb-profiler" ]'
check "bioinfo conda env exists" '[ -x "$HOME/miniforge3/envs/bioinfo/bin/python" ]'

# Data and results the app reads
check "demo FASTQ pair present ($DEMO)" "[ -s data/validation/fastq/${DEMO}_1.fastq.gz ] && [ -s data/validation/fastq/${DEMO}_2.fastq.gz ]"
check "demo report present ($DEMO)" "[ -s pipeline_out/reports/${DEMO}.report.html ]"
# The Browse tab lists the isolates in assets/all_samplesheet.csv
ids=$(tail -n +2 assets/all_samplesheet.csv | cut -d, -f1)
nids=$(echo "$ids" | grep -c .)
missing=""
for id in $ids; do
    [ -s "pipeline_out/qc/$id.qc.json" ] && [ -s "pipeline_out/tbprofiler/$id.results.json" ] \
        || missing="$missing $id"
done
check "Browse tab data complete ($nids isolates in all_samplesheet.csv)" '[ -z "$missing" ]' "no results for:$missing"
check "validation table present" '[ -s results_validation/all_comparisons.csv ]'
check "Nepal isolate list present" '[ -s data/validation/nepal_set.csv ]'

# Cache: the app resumes the latest OK run that used the main work/ dir
session=$(awk -F'\t' '$4 == "OK" && $7 !~ / -w(ork-dir)? / {s = $6} END {print s}' .nextflow/history 2>/dev/null)
check "main Nextflow cache session found (${session:-none})" '[ -n "$session" ] && [ -d work ]'

# Nothing else running
check "no other Nextflow run active" '! pgrep -f "nextflow.cli.Launcher"' "wait for it or stop it"
check "no Streamlit already running" '! pgrep -f "streamlit run"' "stop the old one, or it holds port 8501"
check "port 8501 free" '! (exec 3<>/dev/tcp/127.0.0.1/8501)'

# Disk
free_gb=$(df -BG --output=avail . | tail -1 | tr -dc 0-9)
check "free disk ${free_gb} GB (need 20)" "[ ${free_gb:-0} -ge 20 ]"

echo
if [ $fails -eq 0 ]; then
    echo "All checks passed. Start the app with: streamlit run app.py"
else
    echo "$fails check(s) failed. Fix them before the demo."
    exit 1
fi
