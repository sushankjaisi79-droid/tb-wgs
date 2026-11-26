import io
import urllib.request
from pathlib import Path

import pandas as pd

N_PER_CLASS = 2
CLASSES = ["SUS", "RR", "MDR", "PreXDR", "XDR"]
DRUGS = ["AMI", "BDQ", "CFZ", "DLM", "EMB", "ETH", "INH",
         "KAN", "LEV", "LZD", "MXF", "RIF", "RFB"]
META = Path("data/cryptic_meta")
OUT = Path("data/validation")
OUT.mkdir(parents=True, exist_ok=True)

reuse = pd.read_csv(META / "CRyPTIC_reuse_table_20240917.csv", dtype=str)
genomes = pd.read_csv(META / "GENOMES.csv", dtype=str,
                      usecols=["UNIQUEID", "SITEID", "SUBJID", "LABID"])
samples = pd.read_csv(META / "SAMPLES.csv", dtype=str,
                      usecols=["SITEID", "SUBJID", "LABID", "COUNTRY_WHERE_SAMPLE_TAKEN"]
                      ).drop_duplicates(["SITEID", "SUBJID", "LABID"])
country = (genomes.merge(samples, on=["SITEID", "SUBJID", "LABID"], how="left")
           [["UNIQUEID", "COUNTRY_WHERE_SAMPLE_TAKEN"]]
           .drop_duplicates("UNIQUEID")
           .rename(columns={"COUNTRY_WHERE_SAMPLE_TAKEN": "COUNTRY"}))
df = reuse.merge(country, on="UNIQUEID", how="left")


def ph(r, d):
    if r.get(f"{d}_PHENOTYPE_QUALITY") != "HIGH":
        return None
    v = r.get(f"{d}_BINARY_PHENOTYPE")
    return v if v in ("R", "S") else None


def classify(r):
    rif, inh = ph(r, "RIF"), ph(r, "INH")
    if rif is None or inh is None:
        return None
    calls = {d: ph(r, d) for d in DRUGS}
    if rif == "S":
        known = [v for v in calls.values() if v]
        return "SUS" if known and all(v == "S" for v in known) else None
    fq = [calls["LEV"], calls["MXF"]]
    grp_a = [calls["BDQ"], calls["LZD"]]
    if "R" in fq:
        if "R" in grp_a:
            return "XDR"
        return "PreXDR" if None not in grp_a else None
    if None in fq:
        return None
    return "RR" if inh == "S" else "MDR"


df["CLASS"] = df.apply(classify, axis=1)
usable = df[df["CLASS"].notna()
            & df["ENA_RUN"].str.match(r"^[EDS]RR\d+$", na=False)].copy()
usable["NEPAL"] = usable["COUNTRY"] == "NPL"

print("Isolates usable for validation (columns: from Nepal?):")
print(pd.crosstab(usable["CLASS"], usable["NEPAL"], margins=True).to_string())
print()


def ena_files(run):
    url = ("https://www.ebi.ac.uk/ena/portal/api/filereport"
           f"?accession={run}&result=read_run"
           "&fields=run_accession,library_layout,fastq_ftp,fastq_bytes&format=tsv")
    try:
        t = pd.read_csv(io.StringIO(urllib.request.urlopen(url, timeout=30).read().decode()), sep="\t")
    except Exception as e:
        print(f"skip {run}: {e}")
        return None
    if len(t) != 1 or t.iloc[0]["library_layout"] != "PAIRED":
        return None
    ftp = str(t.iloc[0]["fastq_ftp"]).split(";")
    if len(ftp) != 2:
        return None
    size = sum(int(x) for x in str(t.iloc[0]["fastq_bytes"]).split(";")) / 1e6
    return "https://" + ftp[0], "https://" + ftp[1], round(size)


rows = []
for cls in CLASSES:
    pool = usable[usable["CLASS"] == cls]
    ordered = pd.concat([
        pool[pool["NEPAL"]].sample(frac=1, random_state=42),
        pool[~pool["NEPAL"]].sample(frac=1, random_state=42),
    ])
    picked = 0
    for _, r in ordered.head(30).iterrows():
        f = ena_files(r["ENA_RUN"])
        if f is None:
            continue
        rows.append({"run": r["ENA_RUN"], "uniqueid": r["UNIQUEID"], "class": cls,
                     "country": r["COUNTRY"], "url_1": f[0], "url_2": f[1], "size_mb": f[2]})
        picked += 1
        if picked == N_PER_CLASS:
            break
    if picked < N_PER_CLASS:
        print(f"WARNING: only {picked} usable isolates for {cls}")

panel = pd.DataFrame(rows)
panel.to_csv(OUT / "panel.csv", index=False)

with open(OUT / "download_urls.txt", "w") as fh:
    for _, r in panel.iterrows():
        fh.write(r["url_1"] + "\n" + r["url_2"] + "\n")

pd.DataFrame({
    "sample_id": panel["run"],
    "fastq_1": "data/validation/fastq/" + panel["run"] + "_1.fastq.gz",
    "fastq_2": "data/validation/fastq/" + panel["run"] + "_2.fastq.gz",
}).to_csv("assets/validation_samplesheet.csv", index=False)

sel = df[df["ENA_RUN"].isin(panel["run"])].set_index("ENA_RUN")
truth = pd.DataFrame({d: [ph(sel.loc[run], d) or "." for run in panel["run"]] for d in DRUGS},
                     index=panel["run"])
truth.to_csv(OUT / "panel_truth.csv")

print(panel[["run", "class", "country", "size_mb"]].to_string(index=False))
print(f"\nTotal download: {panel['size_mb'].sum()} MB")
print("\nLab phenotypes, HIGH quality only (R/S, '.' = not available):")
print(truth.to_string())
# end of script


