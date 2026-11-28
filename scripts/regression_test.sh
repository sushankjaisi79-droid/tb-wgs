#!/bin/bash
# Regression test: run the full pipeline on ERR1664619 from raw FASTQ in its
# own work dir and output dir, then check 5 known calls in the fresh result.
#
# Usage:  bash scripts/regression_test.sh            # fresh run (~2 min)
#         bash scripts/regression_test.sh --resume   # reuse work_regression/ cache
#
# A fresh run is the default because Nextflow's cache only tracks the process
# script and its input files. A changed conda env or TBProfiler database would
# not invalidate it, so a resumed run could hide a real break.
set -euo pipefail

cd "$(dirname "$0")/.."

SAMPLE=ERR1664619
SHEET=assets/samplesheet.csv
WORK=work_regression
OUT=regression_out
R="$OUT/tbprofiler/$SAMPLE.results.txt"

resume=""
case "${1:-}" in
    "")        ;;
    --resume)  resume="-resume" ;;
    *)         echo "Unknown option: $1 (only --resume is supported)"; exit 2 ;;
esac

die () { echo; echo "REGRESSION FAILED: $1"; exit 1; }

# Preflight
command -v nextflow >/dev/null \
    || die "nextflow not found on PATH. Open a new terminal so ~/.bashrc sets NXF_JAVA_HOME, then retry."
for f in data/raw/${SAMPLE}_1.fastq.gz data/raw/${SAMPLE}_2.fastq.gz; do
    [ -s "$f" ] || die "input FASTQ missing or empty: $f"
done

# Fresh, isolated run. Only the test's own dirs are removed.
if [ -z "$resume" ]; then
    rm -rf "$WORK" "$OUT"
fi
mkdir -p "$OUT"

echo "Running pipeline on $SAMPLE (work dir: $WORK, output dir: $OUT)"
set +e
nextflow -log "$OUT/nextflow.log" run main.nf \
    --samplesheet "$SHEET" \
    -w "$WORK" -output-dir "$OUT" $resume
status=$?
set -e
[ $status -eq 0 ] \
    || die "pipeline did not finish (exit $status). See $OUT/nextflow.log"
[ -s "$R" ] \
    || die "pipeline finished but $R was not written. See $OUT/nextflow.log"

# The 5 checks. grep -F treats the pattern as plain text, so '.' and '>' are
# matched literally. -x means the whole line must match.
fail=0
total=0
check () {   # check <label-for-context> <grep-flags> <expected>
    local context="$1" flags="$2" expected="$3"
    total=$((total + 1))
    if grep -q $flags -- "$expected" "$R"; then
        echo "PASS  $expected"
    else
        echo "FAIL  $expected"
        echo "      expected: $expected"
        echo "      found:"
        grep -F -- "$context" "$R" | sed 's/^/        /' || echo "        (no line mentioning '$context')"
        fail=$((fail + 1))
    fi
}

echo
echo "Checks on $R"
check "Strain:"          -Fx "Strain: lineage4.3.4.2"
check "Drug-resistance:" -Fx "Drug-resistance: Pre-XDR-TB"
check "rpoB"             -F  "rpoB p.Ser450Leu"
check "gyrA"             -F  "gyrA p.Asp94Ala"
check "rrs"              -F  "rrs n.1401A>G"

echo
if [ $fail -eq 0 ]; then
    echo "REGRESSION PASSED: $total/$total checks"
else
    echo "REGRESSION FAILED: $fail/$total checks failed"
    exit 1
fi
