#!/bin/bash
# Copy fresh reports from pipeline_out/ into the gh-pages worktree
# (../previsgen-site/reports/) and show what changed. It never commits or
# pushes: review the changes, then commit by hand.
#
# Usage:  bash scripts/update_site.sh
#
# What gets copied:
#   - pipeline_out/reports/index.html
#   - only the *.report.html files that index links to (stray reports left
#     behind by other runs, such as the regression sample, stay out)
#   - pipeline_out/multiqc/multiqc_report.html, if it covers every sample
#
# Safety check: the pipeline rebuilds index.html for whatever samplesheet ran
# last. After a 1-sample run the index lists 1 report. The script refuses to
# copy an index that would drop reports the site already lists.
set -euo pipefail

cd "$(dirname "$0")/.."

SITE=../previsgen-site
SRC=pipeline_out/reports
DEST="$SITE/reports"
MQC=pipeline_out/multiqc/multiqc_report.html
MQC_STATS=pipeline_out/multiqc/multiqc_report_data/multiqc_general_stats.txt

die () { echo; echo "SITE UPDATE STOPPED: $1"; exit 1; }

# List the report files an index.html links to, one per line, sorted.
linked_reports () {
    grep -o 'href="[^"]*\.report\.html"' "$1" | sed 's/^href="//; s/"$//' | sort -u
}

# 1. Preflight
[ -d "$SITE" ] || die "$SITE not found. It should be the gh-pages worktree."
branch=$(git -C "$SITE" rev-parse --abbrev-ref HEAD 2>/dev/null) \
    || die "$SITE is not a git worktree."
[ "$branch" = "gh-pages" ] || die "$SITE is on branch '$branch', expected gh-pages."
[ -s "$SRC/index.html" ] || die "$SRC/index.html missing. Run the pipeline first."
mkdir -p "$DEST"

# 2. Which reports does each index link to?
new_list=$(linked_reports "$SRC/index.html")
old_list=""
[ -f "$DEST/index.html" ] && old_list=$(linked_reports "$DEST/index.html" || true)
n_new=$(printf '%s\n' "$new_list" | grep -c . || true)
n_old=$(printf '%s\n' "$old_list" | grep -c . || true)
echo "New index lists $n_new reports; site index lists $n_old."

# 3. Refuse if the new index would drop reports the site already has.
dropped=$(comm -13 <(printf '%s\n' "$new_list") <(printf '%s\n' "$old_list") | grep . || true)
if [ -n "$dropped" ]; then
    n_drop=$(printf '%s\n' "$dropped" | wc -l)
    echo "These site reports are missing from the new index ($n_drop), e.g.:"
    printf '%s\n' "$dropped" | head -5 | sed 's/^/    /'
    die "the new index would drop $n_drop reports. The last pipeline run probably
used a smaller samplesheet. Rebuild the full index first (mostly cached):
    nextflow run main.nf --samplesheet assets/all_samplesheet.csv -resume"
fi

# 4. Every linked report must exist before anything is copied.
missing=""
for f in $new_list; do
    [ -s "$SRC/$f" ] || missing="$missing $f"
done
[ -z "$missing" ] || die "index links to reports that don't exist in $SRC:$missing"

# 5. Copy index + linked reports. Nothing in the site is deleted.
cp "$SRC/index.html" "$DEST/"
for f in $new_list; do
    cp "$SRC/$f" "$DEST/"
done
echo "Copied index.html and $n_new reports into $DEST/"

# 6. MultiQC report, only if it covers at least as many samples as the index.
if [ -s "$MQC" ]; then
    n_mqc=0
    [ -s "$MQC_STATS" ] && n_mqc=$(( $(wc -l < "$MQC_STATS") - 1 ))
    if [ "$n_mqc" -lt "$n_new" ]; then
        echo "WARNING: MultiQC report covers $n_mqc samples but the index has $n_new."
        echo "         Skipped it (looks like it came from a smaller run)."
    else
        cp "$MQC" "$DEST/multiqc_report.html"
        echo "Copied MultiQC report ($n_mqc samples) to $DEST/multiqc_report.html"
    fi
else
    echo "No MultiQC report at $MQC; skipped."
fi

# 7. Show what changed. Committing and pushing are left to you.
echo
echo "git status in $SITE:"
git -C "$SITE" status --short
git -C "$SITE" diff --stat | tail -1
echo
echo "Nothing was committed or pushed. To publish, review the changes, then:"
echo "    cd $SITE && git add reports && git commit -m '...' && git push"
