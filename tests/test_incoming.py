import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import incoming  # noqa: E402

FASTQ = b"@read1\nACGT\n+\nIIII\n" * 200


def gz(path, data=FASTQ):
    path.write_bytes(gzip.compress(data))
    return path


def test_sanitize_id():
    assert incoming.sanitize_id("my sample#1") == "my_sample_1"
    assert incoming.sanitize_id("..-x") == "x"
    assert incoming.sanitize_id("ERR123.v2-a") == "ERR123.v2-a"
    assert len(incoming.sanitize_id("a" * 80)) == incoming.MAX_ID_LEN
    assert incoming.sanitize_id("...") == ""


def test_finds_all_naming_styles(tmp_path):
    for a, b in [("A_1", "A_2"), ("B_R1", "B_R2"), ("C_S1_L001_R1_001", "C_S1_L001_R2_001")]:
        gz(tmp_path / f"{a}.fastq.gz")
        gz(tmp_path / f"{b}.fq.gz")
    pairs, problems = incoming.find_pairs(tmp_path)
    assert sorted(pairs) == ["A", "B", "C"]
    assert pairs["C"][0].name == "C_S1_L001_R1_001.fastq.gz"
    assert problems == []


def test_underscore_number_in_name(tmp_path):
    gz(tmp_path / "ERR_1_1.fastq.gz")
    gz(tmp_path / "ERR_1_2.fastq.gz")
    pairs, _ = incoming.find_pairs(tmp_path)
    assert list(pairs) == ["ERR_1"]


def test_missing_mate(tmp_path):
    gz(tmp_path / "X_R1.fastq.gz")
    pairs, problems = incoming.find_pairs(tmp_path)
    assert pairs == {}
    assert "no matching R2" in problems[0]


def test_uncompressed_reported(tmp_path):
    (tmp_path / "Y_1.fastq").write_bytes(FASTQ)
    (tmp_path / "Y_2.fastq").write_bytes(FASTQ)
    pairs, problems = incoming.find_pairs(tmp_path)
    assert pairs == {}
    assert len(problems) == 2 and all("not gzipped" in p for p in problems)


def test_duplicate_read_files(tmp_path):
    for n in ["Z_1", "Z_R1", "Z_2"]:
        gz(tmp_path / f"{n}.fastq.gz")
    pairs, problems = incoming.find_pairs(tmp_path)
    assert "Z" not in pairs
    assert "more than one file" in problems[0]


def test_odd_characters_become_safe_id(tmp_path):
    gz(tmp_path / "my sample#1_R1.fastq.gz")
    gz(tmp_path / "my sample#1_R2.fastq.gz")
    pairs, _ = incoming.find_pairs(tmp_path)
    assert list(pairs) == ["my_sample_1"]


def test_ignores_other_files_and_subfolders(tmp_path):
    (tmp_path / "notes.txt").write_text("hi")
    (tmp_path / "sub").mkdir()
    gz(tmp_path / "sub" / "S_1.fastq.gz")
    assert incoming.find_pairs(tmp_path) == ({}, [])


def test_check_pair_ok(tmp_path):
    assert incoming.check_pair(gz(tmp_path / "a_1.fastq.gz"), gz(tmp_path / "a_2.fastq.gz")) == []


def test_check_pair_fake_gz(tmp_path):
    r1 = gz(tmp_path / "a_1.fastq.gz")
    r2 = tmp_path / "a_2.fastq.gz"
    r2.write_bytes(FASTQ)  # plain text with a .gz name
    errors = incoming.check_pair(r1, r2)
    assert len(errors) == 1 and "not gzip-compressed" in errors[0]


def test_check_pair_not_fastq(tmp_path):
    r1 = gz(tmp_path / "a_1.fastq.gz", b">fasta\nACGT\n")
    errors = incoming.check_pair(r1, gz(tmp_path / "a_2.fastq.gz"))
    assert len(errors) == 1 and "does not look like FASTQ" in errors[0]


def test_check_pair_empty_and_same(tmp_path):
    r1 = tmp_path / "a_1.fastq.gz"
    r1.write_bytes(b"")
    errors = incoming.check_pair(r1, r1)
    assert any("same file" in e for e in errors)
    assert any("is empty" in e for e in errors)


def test_check_pair_comma(tmp_path):
    d = tmp_path / "with,comma"
    d.mkdir()
    errors = incoming.check_pair(gz(d / "a_1.fastq.gz"), gz(d / "a_2.fastq.gz"))
    assert any("comma" in e for e in errors)


def test_gzip_ok_complete(tmp_path):
    assert incoming.gzip_ok(gz(tmp_path / "a.fastq.gz")) is None


def test_gzip_ok_truncated(tmp_path):
    # valid gzip header and start, but cut short like a half-finished copy
    full = gzip.compress(FASTQ * 50)
    f = tmp_path / "half.fastq.gz"
    f.write_bytes(full[: len(full) // 2])
    msg = incoming.gzip_ok(f)
    assert msg is not None and "incomplete or corrupt" in msg
    # the quick check alone does not catch this, which is why gzip_ok exists
    assert incoming.check_pair(f, gz(tmp_path / "b.fastq.gz")) == []
