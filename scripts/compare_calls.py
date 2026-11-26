from pathlib import Path

import pandas as pd

TB_TO_CODE = {
    "Amikacin": "AMI", "Bedaquiline": "BDQ", "Clofazimine": "CFZ",
    "Delamanid": "DLM", "Ethambutol": "EMB", "Ethionamide": "ETH",
    "Isoniazid": "INH", "Kanamycin": "KAN", "Levofloxacin": "LEV",
    "Linezolid": "LZD", "Moxifloxacin": "MXF", "Rifampicin": "RIF",
}

truth = pd.read_csv("data/validation/panel_truth.csv", index_col=0)
results_dir = Path("pipeline_out/tbprofiler")


def read_calls(txt):
    calls, inside = {}, False
    for line in txt.read_text().splitlines():
        if line.startswith("Resistance report"):
            inside = True
            continue
        if inside and line.startswith("Resistance variants report"):
            break
        if not inside or not line.strip() or line.startswith(("Drug", "---")):
            continue
        parts = line.split("\t")
        drug = parts[0].strip()
        if drug in TB_TO_CODE:
            calls[TB_TO_CODE[drug]] = "R" if len(parts) > 1 and parts[1].strip() == "R" else "S"
    return calls


rows = []
for run in truth.index:
    txt = results_dir / f"{run}.results.txt"
    if not txt.exists():
        print(f"missing result for {run}, skipped")
        continue
    calls = read_calls(txt)
    for code in TB_TO_CODE.values():
        lab = truth.loc[run, code] if code in truth.columns else "."
        if lab not in ("R", "S") or code not in calls:
            continue
        rows.append({"run": run, "drug": code, "lab": lab, "wgs": calls[code]})

df = pd.DataFrame(rows)
out = Path("results_validation")
out.mkdir(exist_ok=True)
df.to_csv(out / "all_comparisons.csv", index=False)


def stats(g):
    tp = ((g.lab == "R") & (g.wgs == "R")).sum()
    fn = ((g.lab == "R") & (g.wgs == "S")).sum()
    tn = ((g.lab == "S") & (g.wgs == "S")).sum()
    fp = ((g.lab == "S") & (g.wgs == "R")).sum()
    return pd.Series({
        "TP": tp, "FN": fn, "TN": tn, "FP": fp,
        "sensitivity": round(tp / (tp + fn), 2) if tp + fn else None,
        "specificity": round(tn / (tn + fp), 2) if tn + fp else None,
    })


per_drug = df.groupby("drug").apply(stats, include_groups=False)
per_drug.to_csv(out / "per_drug.csv")
agree = (df.lab == df.wgs).sum()

print(f"Isolates compared: {df.run.nunique()}")
print(f"Drug-isolate comparisons: {len(df)}, agreement: {agree} ({agree / len(df):.1%})")
print()
print(per_drug.to_string())
print("\nDisagreements:")
print(df[df.lab != df.wgs].to_string(index=False) or "none")
# end of script
