#!/usr/bin/env python3
"""PREVISGEN-TB: self-contained HTML report per sample, plus an index page."""
import argparse
import html
import re
import json
from datetime import date
from pathlib import Path

TOOL = "PREVISGEN-TB"
FIRST_LINE = ["Rifampicin", "Rifapentine", "Isoniazid", "Ethambutol", "Pyrazinamide"]
GROUP_A = ["Levofloxacin", "Moxifloxacin", "Bedaquiline", "Linezolid"]
OTHER = ["Pretomanid", "Delamanid", "Clofazimine", "Cycloserine", "Amikacin", "Kanamycin",
         "Capreomycin", "Streptomycin", "Ethionamide", "Prothionamide", "Para-aminosalicylic_acid"]
ALL_DRUGS = FIRST_LINE + GROUP_A + OTHER
HEADERS = ["Resistance variants report", "Other variants report", "QC failed variants report",
           "Coverage report", "Missing positions report", "Analysis pipeline specifications", "Citation"]
VALIDATION = ("Validated on 116 Nepali clinical isolates (CRyPTIC, MIC phenotypes): rifampicin "
              "sensitivity 100% (89/89), specificity 100% (27/27); isoniazid 100% (89/89), 96.3% (26/27). "
              "Moxifloxacin calls driven by gyrA A90V or D94A indicate low-level resistance and may test "
              "susceptible phenotypically.")

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:960px;margin:24px auto;padding:0 16px;color:#1d2433;background:#fff}
h1{font-size:22px;margin:2px 0 4px} h2{font-size:16px;margin:28px 0 8px;border-bottom:1px solid #e3e6eb;padding-bottom:4px}
.brand{font-size:12px;letter-spacing:.08em;color:#1f5fa8;font-weight:600}
.muted{color:#667085;font-size:13px} .ruo{background:#fff4e5;border:1px solid #f5c26b;padding:8px 12px;border-radius:6px;font-size:13px;margin:12px 0}
.banner{padding:12px 16px;border-radius:8px;font-weight:600;margin:16px 0}
.pass{background:#e7f6ec;color:#1e6b3a;border:1px solid #9bd3ad} .warn{background:#fff4e5;color:#8a5a00;border:1px solid #f5c26b}
.fail{background:#fdecec;color:#9b1c1c;border:1px solid #f2a7a7}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px} .card{border:1px solid #e3e6eb;border-radius:8px;padding:10px}
.card b{display:block;font-size:12px;color:#667085;font-weight:500} .card span{font-size:16px;font-weight:600}
.summary{border:1px solid #e3e6eb;border-radius:8px;padding:10px 14px;margin:16px 0;font-size:14px;line-height:1.6}
table{border-collapse:collapse;width:100%;font-size:13px} th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #eef0f3;vertical-align:top}
table.drugs{table-layout:fixed} th{background:#f7f8fa;font-weight:600} .r{color:#9b1c1c;font-weight:600} .s{color:#667085}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600}
ul{margin:4px 0;padding-left:20px;font-size:13px} footer{margin-top:32px;font-size:12px;color:#667085;border-top:1px solid #e3e6eb;padding-top:8px}
@media(max-width:640px){.grid{grid-template-columns:repeat(2,1fr)}}
"""


def esc(x):
    return html.escape(str(x))


def pct(x):
    try:
        return f"{float(x) * 100:.0f}%"
    except ValueError:
        return x


def fmt_mech(m):
    return re.sub(r"\((\d\.\d+)\)", lambda x: f"({float(x.group(1)) * 100:.0f}%)", m)


def nice(drug):
    return drug.replace("_", " ")


def section(lines, start):
    out, inside = [], False
    for line in lines:
        if line.startswith(start):
            inside = True
            continue
        if inside and any(line.startswith(h) for h in HEADERS if h != start):
            break
        if inside:
            out.append(line)
    return out


def drug_calls(lines):
    calls = {}
    for line in section(lines, "Resistance report"):
        p = line.split("\t")
        name = p[0].strip()
        if not name or name.startswith(("Drug", "---")):
            continue
        calls[name] = (len(p) > 1 and p[1].strip() == "R", p[2].strip() if len(p) > 2 else "")
    return calls


def dr_variants(lines):
    rows = []
    for line in section(lines, "Resistance variants report"):
        p = line.split("\t")
        if len(p) < 9 or p[0].startswith(("Genome", "---")):
            continue
        rows.append({"gene": p[2], "change": p[4], "depth": p[5], "freq": pct(p[6]),
                     "drugs": p[7].replace(",", ", "), "conf": p[8],
                     "comment": (p[9] if len(p) > 9 else "").strip(", ")})
    return rows


def versions(lines):
    v = {"tbprofiler": "?", "db": "?"}
    for line in lines:
        if line.startswith("Software version:"):
            v["tbprofiler"] = line.split(":", 1)[1].strip()
        elif line.startswith("Database version:"):
            v["db"] = line.split(":", 1)[1].strip()
    return v


def summary_box(calls):
    res = [nice(d).lower() for d in ALL_DRUGS if d in calls and calls[d][0]]
    none = [nice(d).lower() for d in ALL_DRUGS if d in calls and not calls[d][0]]
    return (f'<div class="summary"><b>Resistance mutations detected:</b> {esc(", ".join(res) or "none")}<br>'
            f'<b>No resistance mutation detected:</b> {esc(", ".join(none) or "none")}<br>'
            '<span class="muted">Absence of a known resistance mutation does not prove susceptibility.</span></div>')


def drug_table(title, names, calls):
    rows = ""
    for n in names:
        if n not in calls:
            continue
        resistant, mech = calls[n]
        status = '<span class="r">Resistant</span>' if resistant else '<span class="s">No resistance mutation detected</span>'
        rows += f"<tr><td>{esc(nice(n))}</td><td>{status}</td><td>{esc(fmt_mech(mech))}</td></tr>"
    return (f'<h2>{esc(title)}</h2><table class="drugs"><colgroup><col style="width:26%"><col style="width:30%">'
            f'<col style="width:44%"></colgroup><tr><th>Drug</th><th>Genotypic prediction</th>'
            f"<th>Mutation(s)</th></tr>{rows}</table>")


def sample_report(json_path, txt_path, qc_path, out, version):
    r = json.loads(Path(json_path).read_text())
    q = json.loads(Path(qc_path).read_text())
    lines = Path(txt_path).read_text().splitlines()
    calls, variants, v = drug_calls(lines), dr_variants(lines), versions(lines)
    verdict = q["verdict"]
    msg = {"PASS": "QC PASS: result reportable",
           "WARN": "QC WARNING: reportable, review the warnings below",
           "FAIL": "QC FAIL: result not reportable"}[verdict]

    cards = "".join(f'<div class="card"><b>{esc(k)}</b><span>{esc(val)}</span></div>' for k, val in [
        ("Lineage", r.get("sub_lineage") or r.get("main_lineage") or "none"),
        ("Resistance class", r.get("drtype", "?")),
        ("Median depth", f"{q['median_depth']:.0f}x"),
        ("Reads mapped", f"{q['pct_mapped']:.1f}%")])

    if verdict == "FAIL":
        body = f"<h2>Drug resistance</h2><p>Not reported because the sample failed QC: {esc(q['fails'])}.</p>"
        top = ""
    else:
        top = summary_box(calls)
        body = drug_table("First-line drugs", FIRST_LINE, calls)
        body += drug_table("WHO Group A (MDR-TB regimens)", GROUP_A, calls)
        body += drug_table("Other second-line drugs", OTHER, calls)
        vrows = "".join(
            f"<tr><td>{esc(x['gene'])}</td><td>{esc(x['change'])}</td><td>{esc(x['freq'])}</td><td>{esc(x['depth'])}</td>"
            f"<td>{esc(x['drugs'])}</td><td>{esc(x['conf'])}</td><td>{esc(x['comment'])}</td></tr>" for x in variants)
        body += ("<h2>Resistance mutations found</h2><table><tr><th>Gene</th><th>Change</th><th>Fraction</th>"
                 "<th>Depth</th><th>Drugs</th><th>Confidence</th><th>Comment</th></tr>"
                 f"{vrows or '<tr><td colspan=7>None</td></tr>'}</table>")

    flags = ""
    for label, key in [("Failures", "fails"), ("Warnings", "warnings"), ("Notes", "notes")]:
        if q.get(key):
            flags += f"<p><b>{label}</b></p><ul>" + "".join(f"<li>{esc(x)}</li>" for x in q[key].split("; ")) + "</ul>"
    flags = f"<h2>Quality control</h2>{flags or '<p>No issues found.</p>'}"

    Path(out).write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{TOOL} report {esc(r['id'])}</title><style>{CSS}</style></head>
<body><div class="brand">{TOOL} v{esc(version)}</div><h1>Genomic drug-resistance report</h1>
<div class="muted">Sample {esc(r['id'])} &middot; generated {date.today().isoformat()}</div>
<div class="ruo">Research use only. Genotypic predictions must be interpreted by a qualified clinician alongside phenotypic testing. This is not a certified diagnostic device.</div>
<div class="banner {verdict.lower()}">{msg}</div><div class="grid">{cards}</div>
{top}{body}{flags}
<footer>{TOOL} v{esc(version)} &middot; TBProfiler {esc(v['tbprofiler'])}, database {esc(v['db'])}, reference H37Rv.<br>
{esc(VALIDATION)}<br><a href="index.html">All samples</a></footer></body></html>""")


def index_page(files, out, version):
    results, qcs = {}, {}
    for f in files:
        d = json.loads(Path(f).read_text())
        if str(f).endswith(".qc.json"):
            qcs[d["sample"]] = d
        else:
            results[d["id"]] = d
    rows, counts = "", {"PASS": 0, "WARN": 0, "FAIL": 0}
    for sid in sorted(results):
        r, q = results[sid], qcs.get(sid, {})
        verdict = q.get("verdict", "?")
        counts[verdict] = counts.get(verdict, 0) + 1
        rows += (f'<tr><td><a href="{esc(sid)}.report.html">{esc(sid)}</a></td>'
                 f'<td><span class="badge {verdict.lower()}">{esc(verdict)}</span></td>'
                 f"<td>{esc(r.get('sub_lineage') or r.get('main_lineage') or '')}</td><td>{esc(r.get('drtype', ''))}</td></tr>")
    Path(out).write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{TOOL} run summary</title><style>{CSS}</style></head>
<body><div class="brand">{TOOL} v{esc(version)}</div><h1>Run summary</h1>
<div class="muted">{len(results)} samples &middot; generated {date.today().isoformat()}</div>
<div class="ruo">Research use only.</div>
<p>QC: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL</p>
<table><tr><th>Sample</th><th>QC</th><th>Lineage</th><th>Resistance class</th></tr>{rows}</table>
<footer>{esc(VALIDATION)}</footer></body></html>""")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--json", required=True)
    s.add_argument("--txt", required=True)
    s.add_argument("--qc", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--version", default="dev")
    i = sub.add_parser("index")
    i.add_argument("files", nargs="+")
    i.add_argument("--out", default="index.html")
    i.add_argument("--version", default="dev")
    a = ap.parse_args()
    if a.cmd == "sample":
        sample_report(a.json, a.txt, a.qc, a.out, a.version)
    else:
        index_page(a.files, a.out, a.version)


if __name__ == "__main__":
    main()
# end of script
