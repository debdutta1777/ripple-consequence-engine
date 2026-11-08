"""Opt-in end-to-end Clocked verification with *fictional* documents only.

Usage: python -m scripts.smoke_clocked --run

Does not print or store API keys. Makes FOUR billable Clocked requests:
Extract x 2, Compare x 1, Rerank x 1. Only run with permission.
"""
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from app.clocked_adapter import analyze_live
from app.demo import OLD_TEXT, NEW_TEXT, APPLICANTS

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Actually call Clocked (4 billable requests)")
    args = parser.parse_args()
    if not args.run:
        print("Dry-run only. Add --run to make 4 real Clocked requests using the backend environment.")
        return
    if not os.getenv("CLOCKED_API_KEY"):
        raise SystemExit("No API key configured. See docs/SECURE_API_SETUP.md; do not paste the key into chat.")
    from clocked_sdk import Clocked
    with Clocked() as client:
        response = analyze_live(client, OLD_TEXT, NEW_TEXT, APPLICANTS)
    # Print only synthetic sample data and metadata—not secrets or private input.
    report = {
        "mode": response["mode"],
        "endpoints": response["api_calls"],
        "old_policy": {
            "min_gpa": response["policies"]["old"]["min_gpa"],
            "max_income": response["policies"]["old"]["max_income"],
        },
        "new_policy": {
            "min_gpa": response["policies"]["new"]["min_gpa"],
            "max_income": response["policies"]["new"]["max_income"],
        },
        "comparison_verdict": response["comparison"]["verdict"],
        "compare_conflicts": len(response["comparison"]["conflicts"]),
        "rerank_results": len(response["relevance"]),
        "impact_counts": response["impact"]["counts"],
        "extract_field_keys": {
            name: list(response["extraction"][name].get("fields", {}).keys())
            for name in ("old", "new")
        },
    }
    print(json.dumps(report, indent=2))
    if any(response["policies"][name]["min_gpa"] is None or response["policies"][name]["max_income"] is None for name in ("old", "new")):
        raise SystemExit("Clocked responded, but at least one rule was not verified. Inspect live response privately; maintain review mode until resolved.")
    print("PASS: Clocked-backed thresholds confirmed against the fictional sample documents.")


if __name__ == "__main__":
    main()
