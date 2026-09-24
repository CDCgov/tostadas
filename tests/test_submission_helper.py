"""Regression tests for https://github.com/CDCgov/tostadas/issues/362.

If `ncbi-bioproject` is blank in the metadata, the generated submission XML
must not contain a BioProject reference at all. Writing the placeholder
"Not Provided" (the old behavior) causes NCBI to reject the submission and
tostadas hangs waiting on it.
"""
import importlib.util
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

BIN_DIR = Path(__file__).resolve().parent.parent / "bin"


def load_submission_helper():
    spec = importlib.util.spec_from_file_location(
        "submission_helper", BIN_DIR / "submission_helper.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sh = load_submission_helper()


def make_biosample_obj(bioproject_value):
    obj = sh.BiosampleSubmission.__new__(sh.BiosampleSubmission)
    obj.submission_config = {
        "NCBI_Namespace": "TESTNS",
        "BioSample_package": "Pathogen.cl.1.0",
    }
    obj.top_metadata = {
        "ncbi-spuid": "SAMPLE1",
        "ncbi-bioproject": bioproject_value,
        "title": "test title",
    }
    obj.biosample_metadata = {"organism": "Test organism"}
    obj.accession_id = None
    obj.wastewater = False
    return obj


def make_sra_obj(bioproject_value):
    obj = sh.SRASubmission.__new__(sh.SRASubmission)
    obj.submission_config = {"NCBI_Namespace": "TESTNS"}
    obj.top_metadata = {
        "ncbi-bioproject": bioproject_value,
        "ncbi-spuid": "SAMPLE1",
        "ncbi-spuid-sra": "SAMPLE1-SRA",
    }
    obj.sra_metadata = {}
    return obj


def biosample_xml(bioproject_value):
    obj = make_biosample_obj(bioproject_value)
    root = ET.Element("Submission")
    obj.add_action_block(root)
    return ET.tostring(root, encoding="unicode")


def sra_xml(bioproject_value):
    obj = make_sra_obj(bioproject_value)
    add_files = ET.Element("AddFiles")
    obj.add_attributes_block(add_files)
    return ET.tostring(add_files, encoding="unicode")


@pytest.mark.parametrize("blank", [float("nan"), "", "   ", "Not Provided", None])
def test_blank_bioproject_omitted_from_biosample_xml(blank, caplog):
    with caplog.at_level(logging.WARNING):
        xml = biosample_xml(blank)
    assert "BioProject" not in xml
    assert "Not Provided" not in xml
    assert "ncbi-bioproject is blank" in caplog.text


@pytest.mark.parametrize("blank", [float("nan"), "", "   ", "Not Provided", None])
def test_blank_bioproject_omitted_from_sra_xml(blank, caplog):
    with caplog.at_level(logging.WARNING):
        xml = sra_xml(blank)
    assert "BioProject" not in xml
    assert "Not Provided" not in xml
    assert "ncbi-bioproject is blank" in caplog.text


def test_missing_bioproject_key_omitted():
    obj = make_biosample_obj("PRJNA123456")
    del obj.top_metadata["ncbi-bioproject"]
    root = ET.Element("Submission")
    obj.add_action_block(root)
    xml = ET.tostring(root, encoding="unicode")
    assert "BioProject" not in xml
    assert "Not Provided" not in xml


def test_real_bioproject_still_written():
    for xml in (biosample_xml("PRJNA123456"), sra_xml("PRJNA123456")):
        assert "BioProject" in xml
        assert "PRJNA123456" in xml
        assert "Not Provided" not in xml


def test_bioproject_id_helper():
    obj = make_biosample_obj("PRJNA123456")
    assert obj.bioproject_id() == "PRJNA123456"
    obj.top_metadata["ncbi-bioproject"] = "  PRJNA123456  "
    assert obj.bioproject_id() == "PRJNA123456"
    for blank in (float("nan"), "", "   ", "Not Provided", None):
        obj.top_metadata["ncbi-bioproject"] = blank
        assert obj.bioproject_id() is None, blank
    del obj.top_metadata["ncbi-bioproject"]
    assert obj.bioproject_id() is None
