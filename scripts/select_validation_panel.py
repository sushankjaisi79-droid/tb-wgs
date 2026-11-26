import pandas as pd

genomes = pd.read_csv("data/cryptic_meta/GENOMES.csv", low_memory=False)
phenotypes = pd.read_csv("data/cryptic_meta/UKMYC_PHENOTYPES.csv", low_memory=False)
drug_names = pd.read_csv("data/cryptic_meta/DRUG_CODES.csv")

good = genomes[
    (genomes["PER_SAMPLE_VCF_PRESENT"] == True)
    & (genomes["ENA"].notna())
    & (genomes["N_HET"] < 10)
]

panel = (
    good[good["TB_TYPE_1"].isin(["SUS", "RIF", "MDR", "XDR"])]
    .groupby("TB_TYPE_1", group_keys=False)
    .sample(n=1, random_state=42)
)

print("Selected validation panel:")
print(panel[["UNIQUEID", "TB_TYPE_1", "N_HET", "ENA"]].to_string(index=False))
print()

for _, row in panel.iterrows():
    uid = row["UNIQUEID"]
    print(f"--- {uid}  ({row['TB_TYPE_1']}, ENA: {row['ENA']}) ---")
    sub = phenotypes[phenotypes["UNIQUEID"] == uid].merge(
        drug_names, left_on="DRUG", right_on="DRUG_3_LETTER_CODE", how="left"
    )
    print(sub[["DRUG_NAME", "BINARY_PHENOTYPE",


code scripts/select_validation_panel.py
import pandas as pd

genomes = pd.read_csv("data/cryptic_meta/GENOMES.csv", low_memory=False)
phenotypes = pd.read_csv("data/cryptic_meta/UKMYC_PHENOTYPES.csv", low_memory=False)
drug_names = pd.read_csv("data/cryptic_meta/DRUG_CODES.csv")

good = genomes[
    (genomes["PER_SAMPLE_VCF_PRESENT"] == True)
    & (genomes["ENA"].notna())
    & (genomes["N_HET"] < 10)
]

panel = (
    good[good["TB_TYPE_1"].isin(["SUS", "RIF", "MDR", "XDR"])]
    .groupby("TB_TYPE_1", group_keys=False)
    .sample(n=1, random_state=42)
)

print("Selected validation panel:")
print(panel[["UNIQUEID", "TB_TYPE_1", "N_HET", "ENA"]].to_string(index=False))
print()

for _, row in panel.iterrows():
    uid = row["UNIQUEID"]
    print(f"--- {uid}  ({row['TB_TYPE_1']}, ENA: {row['ENA']}) ---")
    sub = phenotypes[phenotypes["UNIQUEID"] == uid].merge(
        drug_names, left_on="DRUG", right_on="DRUG_3_LETTER_CODE", how="left"
    )
    print(sub[["DRUG_NAME", "BINARY_PHENOTYPE", "MIC"]].to_string(index=False))
    print()




