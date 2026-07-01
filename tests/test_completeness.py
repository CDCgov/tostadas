"""Unit tests for completeness-from-VADR-coverage (bin/submission_helper.py).

Runs offline against the real vadr_runs_bundle .sqc/.sgm files plus a synthetic
N450 fragment. Works under pytest or as a plain script: python3 test_completeness.py
"""
import os
import sys
import types
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "bin")
REPO = os.path.join(HERE, "..", "..")
BUNDLE = os.path.join(REPO, "vadr_runs_bundle")
sys.path.insert(0, BIN)

# submission_helper pulls in submission-only deps that the parser does not need;
# stub any that are absent so the pure function can be imported offline.
for _mod in ("paramiko", "nameparser"):
    try:
        __import__(_mod)
    except ImportError:
        _stub = types.ModuleType(_mod)
        if _mod == "nameparser":
            _stub.HumanName = object
        sys.modules[_mod] = _stub

from submission_helper import completeness_from_vadr  # noqa: E402

FULL_DIR = os.path.join(BUNDLE, "vadr_qc_20260422", "batch1")
FULL_SEQ = "MVs_Florida.USA_Jun.25_1064"            # mdl cov 1.000, all trc=no
TRUNC_DIR = os.path.join(BUNDLE, "staging_20260507", "vadr_qc")
TRUNC_SEQ = "MVs_Texas.USA_Jun.25_1427"             # mdl cov 0.975, trc {no,5',3'}


def _write_pair(d, name, mdl_cov, trc):
    """Write a single-sequence <name>.vadr.sqc/.sgm pair into dir d."""
    with open(os.path.join(d, f"{name}.vadr.sqc"), "w") as f:
        f.write("#idx name len p/f ant model1 grp1 grp1 score sc/nt cov mdlcov bias hits str\n")
        f.write(f"1 {name} 15894 PASS yes PP101943 MeV D8 100.0 1.0 1.000 {mdl_cov} 0 1 +\n")
    with open(os.path.join(d, f"{name}.vadr.sgm"), "w") as f:
        f.write("#idx name len p/f model ftrtype ftrname idx num sgm from to mfrom mto len str trc\n")
        f.write(f"1.1.1 {name} 15894 PASS PP101943 gene N 1 1 1 1 100 1 100 100 + {trc}\n")


def test_full_genome_is_complete():
    assert completeness_from_vadr(FULL_DIR, FULL_SEQ, 0.99) == "complete"


def test_truncated_genome_not_complete():
    # fails both: 0.975 < 0.99 and trc has 5'/3'
    assert completeness_from_vadr(TRUNC_DIR, TRUNC_SEQ, 0.99) == ""
    # still not complete at 0.95 because of the truncation test alone
    assert completeness_from_vadr(TRUNC_DIR, TRUNC_SEQ, 0.95) == ""


def test_synthetic_n450_fragment_not_complete():
    with tempfile.TemporaryDirectory() as d:
        _write_pair(d, "tmp", "0.028", "no")
        assert completeness_from_vadr(d, "tmp", 0.99) == ""
        # also fails when the fragment is truncated
        _write_pair(d, "tmp2", "0.028", "3'")
        # tmp2 dir would now have two pairs; isolate in its own dir
    with tempfile.TemporaryDirectory() as d:
        _write_pair(d, "tmp", "0.028", "3'")
        assert completeness_from_vadr(d, "tmp", 0.99) == ""


def test_param_off_or_missing_dir_returns_blank():
    # threshold None => feature off, never consulted
    assert completeness_from_vadr(FULL_DIR, FULL_SEQ, None) == ""
    # no vadr dir => blank
    assert completeness_from_vadr(None, FULL_SEQ, 0.99) == ""


def test_override_precedence_rule():
    # mirrors the injector guard: a non-blank metadata cell wins and VADR is not consulted
    def resolve(meta_value, cmin, vadr_dir, seq_name):
        completeness = (meta_value or "").strip()
        if not completeness and cmin is not None and vadr_dir:
            completeness = completeness_from_vadr(vadr_dir, seq_name, cmin)
        return completeness
    # curator-set value wins even over a full genome
    assert resolve("partial", 0.99, FULL_DIR, FULL_SEQ) == "partial"
    # blank cell + param set => derived from VADR
    assert resolve("", 0.99, FULL_DIR, FULL_SEQ) == "complete"
    # blank cell + param off => stays blank
    assert resolve("", None, FULL_DIR, FULL_SEQ) == ""


def test_single_sequence_dir_resolves_without_name_match():
    with tempfile.TemporaryDirectory() as d:
        _write_pair(d, "tmp", "1.000", "no")
        # a non-matching seq_name still resolves in a single-sequence dir
        assert completeness_from_vadr(d, "DOES_NOT_MATCH", 0.99) == "complete"


def test_multi_sequence_dir_requires_name_match():
    # real multi-sequence bundle: a bogus name resolves to blank
    assert completeness_from_vadr(FULL_DIR, "NOT_A_REAL_SEQ", 0.99) == ""


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    fails = []
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
        except AssertionError as e:
            fails.append((t.__name__, str(e)))
            print(f"  FAIL {t.__name__}: {e}")
    if fails:
        print(f"\nFAILED {len(fails)}/{len(tests)}")
        return 1
    print(f"\ncompleteness_from_vadr: all {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
