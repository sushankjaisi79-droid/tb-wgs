import math

import pandas as pd

df = pd.read_csv("results_validation/all_comparisons.csv")
nepal = set(pd.read_csv("data/validation/nepal_set.csv")["run"])
df = df[df["run"].isin(nepal)]


def wilson(k, n):
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def fmt(k, n):
    if n == 0:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({k / n:.1%}, 95% CI {lo:.1%}-{hi:.1%})"


rows = []
for drug, g in df.groupby("drug"):
    tp = int(((g.lab == "R") & (g.wgs == "R")).sum())
    fn = int(((g.lab == "R") & (g.wgs == "S")).sum())
    tn = int(((g.lab == "S") & (g.wgs == "S")).sum())
    fp = int(((g.lab == "S") & (g.wgs == "R")).sum())
    rows.append({"drug": drug, "sensitivity": fmt(tp, tp + fn),
                 "specificity": fmt(tn, tn + fp)})

out = pd.DataFrame(rows).set_index("drug")
out.to_csv("results_validation/nepal_per_drug.csv")
agree = int((df.lab == df.wgs).sum())
print(f"Nepali isolates: {df.run.nunique()}")
print(f"Comparisons: {len(df)}, agreement: {agree} ({agree / len(df):.1%})")
print(out.to_string())
# end of script
