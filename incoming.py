"""Find and check FASTQ pairs dropped into data/incoming/ so the app can run them.

Kept free of Streamlit so it can be tested with pytest (tests/test_incoming.py).
"""
import gzip
import re
from pathlib import Path

# NAME_1 / NAME_2, NAME_R1 / NAME_R2, and Illumina NAME_S1_L001_R1_001
PAIR_RE = re.compile(r"^(?P<name>.+?)(?:_S\d+_L\d{3})?_R?(?P<read>[12])(?:_001)?\.(?:fastq|fq)\.gz$")
UNZIPPED_RE = re.compile(r"\.(?:fastq|fq)$")
MAX_ID_LEN = 50
CHUNK = 1024 * 1024


def sanitize_id(name):
    """Turn a file-name stem into a safe sample ID, or '' if nothing usable is left."""
    clean = re.sub(r"[^A-Za-z0-9_.-]", "_", name).lstrip(".-")
    return clean[:MAX_ID_LEN]


def find_pairs(folder):
    """Return ({sample_id: (r1, r2)}, [problem sentences]) for files directly in folder."""
    folder = Path(folder)
    groups, problems = {}, []
    if not folder.is_dir():
        return {}, []
    for f in sorted(p for p in folder.iterdir() if p.is_file()):
        if UNZIPPED_RE.search(f.name):
            problems.append(f"`{f.name}` is not gzipped (.fastq.gz or .fq.gz expected).")
            continue
        m = PAIR_RE.match(f.name)
        if not m:
            if f.name.endswith((".fastq.gz", ".fq.gz")):
                problems.append(f"`{f.name}`: can't tell if this is read 1 or read 2. "
                                "Name it like NAME_R1.fastq.gz / NAME_R2.fastq.gz.")
            continue
        groups.setdefault(m["name"], {"1": [], "2": []})[m["read"]].append(f)

    pairs, owner = {}, {}
    for name, reads in groups.items():
        r1, r2 = reads["1"], reads["2"]
        if len(r1) > 1 or len(r2) > 1:
            extra = ", ".join(f"`{p.name}`" for p in r1 + r2)
            problems.append(f"`{name}`: more than one file for the same read ({extra}).")
            continue
        if not r1 or not r2:
            have, missing = (r1[0], "R2") if r1 else (r2[0], "R1")
            problems.append(f"`{have.name}` has no matching {missing} file.")
            continue
        sid = sanitize_id(name)
        if not sid:
            problems.append(f"`{name}`: no usable sample ID (use letters, digits, _ - .).")
            continue
        if sid in owner:
            problems.append(f"`{name}` and `{owner[sid]}` both become sample ID `{sid}`; rename one.")
            pairs.pop(sid, None)
            continue
        owner[sid] = name
        pairs[sid] = (r1[0], r2[0])
    return pairs, problems


def check_pair(fq1, fq2):
    """Quick checks (milliseconds). Returns a list of problem sentences; empty means OK."""
    errors = []
    fq1, fq2 = Path(fq1), Path(fq2)
    if fq1.resolve() == fq2.resolve():
        errors.append("Read 1 and read 2 are the same file.")
    for f in (fq1, fq2):
        if "," in str(f):
            errors.append(f"`{f.name}`: the path contains a comma; rename the file or folder.")
        if not f.is_file():
            errors.append(f"`{f.name}` does not exist.")
            continue
        if f.stat().st_size == 0:
            errors.append(f"`{f.name}` is empty.")
            continue
        with open(f, "rb") as fh:
            if fh.read(2) != b"\x1f\x8b":
                errors.append(f"`{f.name}` is not gzip-compressed, even though its name ends in .gz.")
                continue
        try:
            with gzip.open(f, "rt", errors="replace") as fh:
                first = fh.readline()
        except (OSError, EOFError):
            errors.append(f"`{f.name}` could not be decompressed.")
            continue
        if not first.startswith("@"):
            errors.append(f"`{f.name}` does not look like FASTQ (first line should start with @).")
    return errors


def gzip_ok(path):
    """Full integrity test, like `gzip -t`: decompress the whole file and throw the data away.

    Returns None if the file is complete, otherwise a problem sentence. A file that is still
    being copied, or was cut short, fails here instead of deep inside TBProfiler.
    """
    path = Path(path)
    try:
        with gzip.open(path, "rb") as fh:
            while fh.read(CHUNK):
                pass
    except (EOFError, gzip.BadGzipFile, OSError, ValueError) as e:
        return (f"`{path.name}` is incomplete or corrupt ({e.__class__.__name__}). "
                "If it is still copying, wait and try again; otherwise copy it again.")
    return None
