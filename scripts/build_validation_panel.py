import io
import urllib.request
from pathlib import Path

import pandas as pd

N_PER_CLASS = 1      # raise to 5 later for a 20-isolate panel
CANDIDATES = 25
CLASSES = ["SUS", "RR", "MDR", "XDR_old"]

out = Path("data/validation")
out.mkdir(parents=True, exist_ok=True)

genomes = pd.read_csv("data/cryptic_meta/GENOMES.csv", low_memory=False)
phenotypes = pd.read_csv("data/cryptic_meta/UKMYC_PHENOTYPES.csv", low_memory=False)
drugs = pd.read_csv("data/cryptic_meta/DRUG_CODES.csv")

hq = phenotypes[phenotypes["PHENOTYPE_QUALITY"] == "HIGH"]
wide = hq.pivot_table(index="UNIQUEID", columns="DRUG",
                      values="BINARY_PHENOTYPE", aggfunc="first")

def classify(r):
    rif, inh = r.get("RIF"), r.get("INH")
    if pd.isna(rif) or pd.isna(inh):
        return None
    if rif == "S" and inh == "S":
        return "SUS" if (r.dropna() == "S").all() else None
    if rif == "R" and inh == "S":
        return "RR"
    if rif == "R" and inh == "R":
        fq = any(r.get(d) == "R" for d in ["LEV", "MXF"])
        inj = any(r.get(d) == "R" for d in ["AMI", "KAN"])
        if fq and inj:
            return "XDR_old"
        if not fq and not inj:
            return "MDR"
    return None

wide["pheno_class"] = wide.apply(classify, axis=1)
wide = wide[wide["pheno_class"].notna()]

good = genomes[
    (genomes["ENA"].notna())
    & (genomes["N_HET"] < 10)
    & (genomes["UNIQUEID"].isin(wide.index))
].merge(wide[["pheno_class"]], left_on="UNIQUEID", right_index=True)

print("Isolates available per phenotype class:")
print(good["pheno_class"].value_counts().to_string())
print()

rows = []
for cls in CLASSES:
    pool = good[good["pheno_class"] == cls]
    cands = pool.sample(n=min(CANDIDATES, len(pool)), random_state=42)
    picked = 0
    for _, g in cands.iterrows():
        url = (
            "https://www.ebi.ac.uk/ena/portal/api/filereport"
            f"?accession={g['ENA']}&result=read_run"
            "&fields=run_accession,library_layout,read_count,fastq_ftp,fastq_bytes&format=tsv"
        )
        try:
            text = urllib.request.urlopen(url, timeout=30).read().decode()
            runs = pd.read_csv(io.StringIO(text), sep="\t")
        except Exception as e:
            print(f"skip {g['ENA']}: {e}")
            continue
        if len(runs) != 1:
            continue
        run = runs.iloc[0]
        ftp = str(run["fastq_ftp"]).split(";")
        if run["library_layout"] != "PAIRED" or len(ftp) != 2:
            continue
        size_mb = sum(int(x) for x in str(run["fastq_bytes"]).split(";")) / 1e6
        rows.append({
            "uniqueid": g["UNIQUEID"],
            "pheno_class": cls,
            "ena_sample": g["ENA"],
            "run": run["run_accession"],
            "read_count": run["read_count"],
            "size_mb": round(size_mb),
            "url_1": "https://" + ftp[0],
            "url_2": "https://" + ftp[1],
        })
        picked += 1
        if picked == N_PER_CLASS:
            break
    if picked < N_PER_CLASS:
        print(f"WARNING: only found {picked} usable isolates for {cls}")

panel = pd.DataFrame(rows)
panel.to_csv(out / "panel.csv", index=False)

pheno = (
    hq[hq["UNIQUEID"].isin(panel["uniqueid"])]
    .merge(drugs, left_on="DRUG", right_on="DRUG_3_LETTER_CODE", how="left")
    .merge(panel[["uniqueid", "run"]], left_on="UNIQUEID", right_on="uniqueid")
    [["run", "UNIQUEID", "DRUG", "DRUG_NAME", "BINARY_PHENOTYPE", "MIC"]]
)
pheno.to_csv(out / "panel_phenotypes.csv", index=False)

with open(out / "download_urls.txt", "w") as f:
    for _, r in panel.iterrows():
        f.write(r["url_1"] + "\n" + r["url_2"] + "\n")

pd.DataFrame({
    "sample_id": panel["run"],
    "fastq_1": "data/validation/fastq/" + panel["run"] + "_1.fastq.gz",
    "fastq_2": "data/validation/fastq/" + panel["run"] + "_2.fastq.gz",
}).to_csv("assets/validation_samplesheet.csv", index=False)

print(panel[["run", "pheno_class", "ena_sample", "read_count", "size_mb"]].to_string(index=False))
print(f"\nTotal download: {panel['size_mb'].sum()} MB")
print("\nLab phenotypes (S = susceptible, R = resistant):")
print(pheno.pivot_table(index="DRUG", columns="run", values="BINARY_PHENOTYPE", aggfunc="first").to_string())
# end of script
