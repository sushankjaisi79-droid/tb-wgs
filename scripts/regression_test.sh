#!/bin/bash
set -euo pipefail
R=pipeline_out/tbprofiler/ERR1664619.results.txt
fail=0
check () { grep -q "$1" "$R" && echo "PASS  $1" || { echo "FAIL  $1"; fail=1; }; }
check "Strain: lineage4.3.4.2"
check "Drug-resistance: Pre-XDR-TB"
check "rpoB p.Ser450Leu"
check "gyrA p.Asp94Ala"
check "rrs n.1401A>G"
exit $fail
# end of script
