#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

import pandas as pd

MIN_MAPPED_FAIL, MIN_MAPPED_WARN = 80.0, 90.0
MIN_DEPTH_FAIL, MIN_DEPTH_WARN = 10.0, 20.0
MIN_GENE_PCT = 95.0
CORE_GENES = {"rpoB", "katG", "inhA", "fabG1", "embB", "pncA",
              "gyrA", "gyrB", "rrs", "eis", "ethA"}
LARGE_DEL = re.compile(r"_.*del")


def pick(d, *options):
    for o in options:
        if o in d:
            return o
    raise KeyError(f"none of {options} found; keys are {sorted(d)}")


def check(path):
    r = json.loads(Path(path).read_text())
    qc = r["qc"]
    variants = r.get("dr_variants", []) + r.get("other_variants", [])
    fails, warns, notes = [], [], []

    lineage = r.get("main_lineage") or ""
    if not lineage:
        fails.append("no M. tuberculosis lineage detected")
    elif ";" in lineage:
        warns.append(f"possible mixed infection, two lineages ({lineage})")
    elif not lineage.startswith("lineage"):
        warns.append(f"non-M. tuberculosis lineage ({lineage})")

    mapped = float(qc["percent_reads_mapped"])
    if mapped < MIN_MAPPED_FAIL:
        fails.append(f"only {mapped:.1f}% reads mapped")
    elif mapped < MIN_MAPPED_WARN:
        warns.append(f"{mapped:.1f}% reads mapped")

    depth = float(qc["genome_median_depth"])
    if depth < MIN_DEPTH_FAIL:
        fails.append(f"median depth {depth:.0f}x")
    elif depth < MIN_DEPTH_WARN:
        warns.append(f"median depth {depth:.0f}x")

    deleted = {}
    for v in variants:
        if LARGE_DEL.search(str(v.get("change", ""))):
            deleted.setdefault(v.get("gene_name"), v.get("change"))

    targets = qc.get("target_qc", [])
    if targets:
        gk = pick(targets[0], "gene_name", "gene", "target")
        pk = pick(targets[0], "percent_depth_pass", "pct_depth_pass")
        for t in targets:
            g, pct = t[gk], float(t[pk])
            if g in CORE_GENES and pct < MIN_GENE_PCT:
                if g in deleted:
                    notes.append(f"{g} large deletion {deleted[g]} (explains {pct:.0f}% coverage)")
                else:
                    warns.append(f"low coverage: {g} {pct:.0f}%")

    partial = [v for v in r.get("dr_variants", [])
               if v.get("freq") is not None and 0.10 <= float(v["freq"]) < 0.90]
    for v in partial:
        warns.append(f"heteroresistance: {v.get('gene_name')} {v.get('change')} at {float(v['freq']):.0%}")
    if len(partial) >= 2:
        warns.append("possible mixed infection (several mutations at partial frequency)")

    verdict = "FAIL" if fails else ("WARN" if warns else "PASS")
    return {"sample": r["id"], "verdict": verdict, "lineage": r.get("sub_lineage") or lineage,
            "pct_mapped": mapped, "median_depth": depth,
            "fails": "; ".join(fails), "warnings": "; ".join(warns), "notes": "; ".join(notes)}


def main():
    ap = argparse.ArgumentParser(description="QC gate for TBProfiler results")
    ap.add_argument("json_files", nargs="+")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--summary", default=None)
    a = ap.parse_args()
    out = Path(a.outdir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for jf in a.json_files:
        res = check(jf)
        (out / f"{res['sample']}.qc.json").write_text(json.dumps(res, indent=2))
        rows.append(res)
    df = pd.DataFrame(rows)
    if a.summary:
        df.to_csv(a.summary, index=False)
    print(df["verdict"].value_counts().to_string())
    print(f"\nSamples with an explanatory note: {(df['notes'] != '').sum()}")
    flagged = df[df["verdict"] != "PASS"]
    if len(flagged):
        print()
        print(flagged[["sample", "verdict", "fails", "warnings"]].to_string(index=False))


if __name__ == "__main__":
    main()
# end of script
