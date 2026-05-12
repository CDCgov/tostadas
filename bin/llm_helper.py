#!/usr/bin/env python3
"""
LLM helper utilities for the tostadas pipeline.

All public functions have a non-LLM fallback: they return None when the
OpenAI client is unavailable (missing key, missing package, network error).
Callers should treat a None return as "feature not available" and continue
with standard behavior.

Credential resolution order:
  1. OPENAI_API_KEY environment variable (set directly or via Nextflow Secrets)
  2. .env file in the working directory (for local runs)
"""
import os
import json
import logging
from typing import Optional


def _load_dotenv():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def _get_client():
    _load_dotenv()
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        return OpenAI(api_key=api_key)
    except ImportError:
        logging.debug("openai package not installed — LLM features disabled")
        return None


def explain_validation_errors(error_text: str, model: str = "gpt-4o-mini") -> Optional[str]:
    """
    Takes raw error.txt content and returns an enhanced report with plain-English
    explanations and specific fix suggestions for each error.
    Returns None if LLM is unavailable or the call fails.
    """
    client = _get_client()
    if not client:
        return None

    prompt = (
        "You are a bioinformatics assistant helping scientists submit genomic sequences to NCBI.\n\n"
        "Below is a validation error report from the tostadas metadata validation pipeline. "
        "For each error or warning, provide:\n"
        "1. A plain-English explanation of what it means\n"
        "2. A specific, actionable fix the user can apply to their Excel metadata file\n\n"
        "Format each issue as:\n"
        "ISSUE: <exact error text>\n"
        "EXPLANATION: <what it means>\n"
        "FIX: <what to change>\n"
        "---\n\n"
        f"Validation report:\n{error_text}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.warning(f"LLM validation enhancement failed: {e}")
        return None


def interpret_ncbi_report(report_csv: str, model: str = "gpt-4o-mini") -> Optional[str]:
    """
    Takes the content of a batch report CSV returned from NCBI and returns a
    plain-English interpretation of any errors, plus suggested fixes.
    Returns None if LLM is unavailable or the call fails.
    """
    client = _get_client()
    if not client:
        return None

    prompt = (
        "You are a bioinformatics assistant helping scientists submit sequences to NCBI.\n\n"
        "Below is a submission report CSV from the tostadas NCBI submission pipeline. "
        "Review each sample's status. For any sample with an error or non-'processed-ok' status:\n"
        "1. Explain in plain English what the NCBI error message means\n"
        "2. Give a specific actionable fix\n\n"
        "If all samples succeeded, say so briefly. Be concise.\n\n"
        f"Report CSV:\n{report_csv}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.warning(f"LLM report interpretation failed: {e}")
        return None


def suggest_metadata_fixes(
    metadata_row: dict,
    errors: list,
    model: str = "gpt-4o-mini",
) -> Optional[dict]:
    """
    For a single sample row with known validation errors, suggests corrected
    field values. Returns a dict of {field_name: suggested_value}, or None
    if LLM is unavailable or the call fails.
    """
    client = _get_client()
    if not client:
        return None

    prompt = (
        "You are a bioinformatics metadata expert. A scientist is submitting genomic data to NCBI.\n\n"
        f"Sample metadata:\n{json.dumps(metadata_row, indent=2, default=str)}\n\n"
        f"Validation errors:\n" + "\n".join(f"- {e}" for e in errors) + "\n\n"
        "Suggest corrected values ONLY for the fields that have errors. "
        "Return a JSON object mapping field names to corrected values. "
        "Do not include fields that are already valid."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.warning(f"LLM metadata fix suggestion failed: {e}")
        return None
