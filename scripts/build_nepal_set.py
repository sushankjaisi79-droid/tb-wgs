import io
import urllib.request
from pathlib import Path

import pandas as pd

DRUGS = ["AMI", "BDQ", "CFZ", "DLM", "EMB", "ETH", "INH",
         "KAN", "LEV", "LZD", "MXF", "RIF", "RFB"]
META = Path("data/cryptic_meta")
OUT = Path("data/validation")

reuse = pd.read_csv(META / "CRyPTIC_reuse_table_20240917.csv", dtype=str)
genomes = pd.read_csv(META / "GENOMES.csv", dtype=str,
                      usecols=["UNIQUEID", "SITEID", "SUBJID", "LABID"])
samples = pd.read_csv(META / "SAMPLES.csv", dtype=str,
                      usecols=["SITEID", "SUBJID", "LABID", "COUNTRY_WHERE_SAMPLE_TAKEN"]
                      ).drop_duplicates(["SITEID", "SUBJID", "LABID"])
country = (genomes.merge(samples, on=["SITEID", "SUBJID", "LABID"], how="left")
           [["UNIQUEID", "COUNTRY_WHERE_SAMPLE_TAKEN"]].drop_duplicates("UNIQUEID"))
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
    fq, grp_a = [calls["LEV"], calls["MXF"]], [calls["BDQ"], calls["LZD"]]
    if "R" in fq:
        if "R" in grp_a:
            return "XDR"
        return "PreXDR" if None not in grp_a else None
    if None in fq:
        return None
    return "RR" if inh == "S" else "MDR"


df["CLASS"] = df.apply(classify, axis=1)
nepal = df[(df["COUNTRY_WHERE_SAMPLE_TAKEN"] == "NPL") & df["CLASS"].notna()
           & df["ENA_RUN"].str.match(r"^[EDS]RR\d+$", na=False)]
print(f"Nepali isolates to check on ENA: {len(nepal)}")

rows = []
for _, r in nepal.iterrows():
    url = ("https://www.ebi.ac.uk/ena/portal/api/filereport"
           f"?accession={r['ENA_RUN']}&result=read_run"
           "&fields=library_layout,fastq_ftp,fastq_bytes&format=tsv")
    try:
        t = pd.read_csv(io.StringIO(urllib.request.urlopen(url, timeout=30).read().decode()), sep="\t")
    except Exception as e:
        print(f"skip {r['ENA_RUN']}: {e}")
        continue
    if len(t) != 1 or t.iloc[0]["library_layout"] != "PAIRED":
        continue
    ftp = str(t.iloc[0]["fastq_ftp"]).split(";")
    if len(ftp) != 2:
        continue
    size = sum(int(x) for x in str(t.iloc[0]["fastq_bytes"]).split(";")) / 1e6
    rows.append({"run": r["ENA_RUN"], "class": r["CLASS"], "size_mb": round(size),
                 "url_1": "https://" + ftp[0], "url_2": "https://" + ftp[1]})

ns = pd.DataFrame(rows)
ns.to_csv(OUT / "nepal_set.csv", index=False)

with open(OUT / "nepal_download_urls.txt", "w") as fh:
    for _, r in ns.iterrows():
        fh.write(r["url_1"] + "\n" + r["url_2"] + "\n")

pd.DataFrame({
    "sample_id": ns["run"],
    "fastq_1": "data/validation/fastq/" + ns["run"] + "_1.fastq.gz",
    "fastq_2": "data/validation/fastq/" + ns["run"] + "_2.fastq.gz",
}).to_csv("assets/nepal_samplesheet.csv", index=False)

sel = df.set_index("ENA_RUN").loc[ns["run"]]
new_truth = pd.DataFrame({d: [ph(sel.loc[x], d) or "." for x in ns["run"]] for d in DRUGS},
                         index=ns["run"])
old_truth = pd.read_csv(OUT / "panel_truth.csv", index_col=0)
truth = pd.concat([old_truth, new_truth])
truth = truth[~truth.index.duplicated(keep="first")]
truth.to_csv(OUT / "panel_truth.csv")

print(ns["class"].value_counts().to_string())
print(f"\nUsable Nepali isolates: {len(ns)}, total download: {ns['size_mb'].sum()} MB")
# end of script
