import json
import math
import subprocess
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "pipeline_out"
FASTQ = ROOT / "data" / "validation" / "fastq"
VAL = ROOT / "results_validation"
DRUG_ORDER = ["RIF", "INH", "EMB", "LEV", "MXF", "BDQ", "LZD", "CFZ", "DLM", "AMI", "KAN", "ETH"]
DRUG_NAMES = {"RIF": "rifampicin", "INH": "isoniazid", "EMB": "ethambutol", "LEV": "levofloxacin",
              "MXF": "moxifloxacin", "BDQ": "bedaquiline", "LZD": "linezolid", "CFZ": "clofazimine",
              "DLM": "delamanid", "AMI": "amikacin", "KAN": "kanamycin", "ETH": "ethionamide"}

st.set_page_config(page_title="PREVISGEN-TB", layout="wide")
st.title("PREVISGEN-TB: drug-resistance profiling from TB sequencing data")
st.caption("Research use only. Predictions require clinician review alongside phenotypic testing.")


def show_report(path):
    if path.exists():
        components.html(path.read_text(), height=1500, scrolling=True)
    else:
        st.warning(f"No report found at {path}")


def wilson(k, n):
    z = 1.96
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


tab_run, tab_browse, tab_val = st.tabs(["Run a sample", "Browse results", "Validation"])

with tab_run:
    st.subheader("Run the pipeline on one sample")
    pairs = sorted({p.name.rsplit("_", 1)[0] for p in FASTQ.glob("*_1.fastq.gz")})
    sample = st.selectbox("Sample (paired-end FASTQ)", pairs)
    if st.button("Run pipeline", type="primary"):
        runs = ROOT / "runs"
        runs.mkdir(exist_ok=True)
        sheet = runs / f"{sample}.csv"
        sheet.write_text("sample_id,fastq_1,fastq_2\n"
                         f"{sample},{FASTQ}/{sample}_1.fastq.gz,{FASTQ}/{sample}_2.fastq.gz\n")
        outdir = runs / sample
        cmd = ["nextflow", "run", str(ROOT / "main.nf"), "--samplesheet", str(sheet),
               "-output-dir", str(outdir), "-resume", "-ansi-log", "false"]
        with st.status(f"Running pipeline on {sample}", expanded=True) as status:
            box, lines = st.empty(), []
            proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                lines.append(line.rstrip())
                box.code("\n".join(lines[-15:]))
            proc.wait()
            if proc.returncode == 0:
                status.update(label=f"Finished: {sample}", state="complete")
            else:
                status.update(label="Pipeline failed, see log above", state="error")
        if proc.returncode == 0:
            show_report(outdir / "reports" / f"{sample}.report.html")

with tab_browse:
    st.subheader("All analysed isolates")
    rows = []
    for q in sorted((OUT / "qc").glob("*.qc.json")):
        d = json.loads(q.read_text())
        r = json.loads((OUT / "tbprofiler" / f"{d['sample']}.results.json").read_text())
        rows.append({"sample": d["sample"], "QC": d["verdict"],
                     "lineage": d["lineage"], "resistance": r.get("drtype", "")})
    df = pd.DataFrame(rows)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Isolates", len(df))
    m2.metric("QC pass", int((df.QC == "PASS").sum()))
    m3.metric("QC warning", int((df.QC == "WARN").sum()))
    m4.metric("Pre-XDR / XDR", int(df.resistance.str.contains("XDR").sum()))
    c1, c2 = st.columns(2)
    qc_f = c1.multiselect("QC verdict", sorted(df.QC.unique()), default=sorted(df.QC.unique()))
    dr_f = c2.multiselect("Resistance class", sorted(df.resistance.unique()),
                          default=sorted(df.resistance.unique()))
    view = df[df.QC.isin(qc_f) & df.resistance.isin(dr_f)]
    st.dataframe(view, hide_index=True)
    pick = st.selectbox("Open a report", view["sample"])
    if pick:
        show_report(OUT / "reports" / f"{pick}.report.html")

with tab_val:
    st.subheader("Validation against laboratory phenotypes: 116 Nepali isolates (CRyPTIC)")
    comp = pd.read_csv(VAL / "all_comparisons.csv")
    nepal = set(pd.read_csv(ROOT / "data" / "validation" / "nepal_set.csv")["run"])
    nc = comp[comp.run.isin(nepal)]
    agree = int((nc.lab == nc.wgs).sum())
    v1, v2, v3 = st.columns(3)
    v1.metric("Isolates", nc.run.nunique())
    v2.metric("Drug calls compared", len(nc))
    v3.metric("Agreement", f"{agree / len(nc):.1%}")

    rows = []
    for drug, g in nc.groupby("drug"):
        for metric, lab in [("Sensitivity", "R"), ("Specificity", "S")]:
            sub = g[g.lab == lab]
            n = len(sub)
            if n == 0:
                continue
            k = int((sub.wgs == lab).sum())
            lo, hi = wilson(k, n)
            rows.append({"drug": drug, "metric": metric, "value": k / n, "lo": lo, "hi": hi,
                         "result": f"{k}/{n} ({k / n:.0%})"})
    stats = pd.DataFrame(rows)
    order = [d for d in DRUG_ORDER if d in set(stats.drug)]

    col_s, col_p = st.columns(2)
    for col, metric in [(col_s, "Sensitivity"), (col_p, "Specificity")]:
        d = stats[stats.metric == metric]
        y = alt.Y("drug:N", sort=order, title=None)
        x = alt.X("lo:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%"), title=None)
        rule = alt.Chart(d).mark_rule(strokeWidth=3, color="#9aa4b2").encode(y=y, x=x, x2="hi:Q")
        point = alt.Chart(d).mark_point(filled=True, size=90, color="#1f5fa8", opacity=1).encode(
            y=y, x="value:Q",
            tooltip=["drug", "result",
                     alt.Tooltip("lo:Q", format=".1%", title="95% CI low"),
                     alt.Tooltip("hi:Q", format=".1%", title="95% CI high")])
        col.markdown(f"**{metric}**")
        col.altair_chart((rule + point).properties(height=360))

    no_r = [DRUG_NAMES[x] for x in order if x not in set(stats[stats.metric == "Sensitivity"].drug)]
    st.caption("Dot = estimate, grey line = 95% confidence interval (Wilson). A wide line means few "
               "resistant isolates, so that estimate is uncertain. Sensitivity not estimable for "
               + ", ".join(no_r) + ": no Nepali isolate in this set was resistant.")

    st.markdown("**Results by drug**")
    table = stats.pivot(index="drug", columns="metric", values="result").reindex(order).fillna("n/a")
    st.dataframe(table)

    st.markdown("**Key findings**")
    st.markdown(
        "- Rifampicin: 89/89 resistant isolates detected, 27/27 susceptible correct.\n"
        "- Moxifloxacin specificity is low; 13 of 15 false-resistant calls carry gyrA A90V or D94A, "
        "mutations that confer low-level resistance.\n"
        "- 29 isolates (lineage 2.2.1) share one large ethA deletion; all 15 with an ethionamide "
        "result were resistant and correctly predicted.\n"
        "- Three isolates show paired mutation frequencies consistent with mixed infection.\n"
        "- One isolate (ERR4830980) had four phenotypic resistances with no known resistance mutation.")
    st.markdown("**All disagreements**")
    st.dataframe(nc[nc.lab != nc.wgs].sort_values(["drug", "run"]), hide_index=True)
# end of file
