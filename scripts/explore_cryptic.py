import pandas as pd

genomes = pd.read_csv("data/cryptic_meta/GENOMES.csv")
phenotypes = pd.read_csv("data/cryptic_meta/UKMYC_PHENOTYPES.csv")

good = genomes[
    (genomes["PER_SAMPLE_VCF_PRESENT"] == True)
    & (genomes["ENA"].notna())
    & (genomes["N_HET"] < 10)  # low heterozygosity = clean single-strain infection
]

print(f"Total genomes: {len(genomes)}")
print(f"With VCF + ENA accession + low heterozygosity: {len(good)}")
print()
print("TB_TYPE_1 categories in that filtered set:")
print(good["TB_TYPE_1"].value_counts())
print()
print("Sample row for inspection:")
print(good.iloc[0][["UNIQUEID", "LINEAGE_NAME", "TB_TYPE_1", "N_HET", "ENA"]])
