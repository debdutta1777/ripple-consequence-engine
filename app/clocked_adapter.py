"""Real Clocked usage with strict evidence checks.

Only the explicit min-GPA/max-household-income subset is supported. No data
from live API calls is replaced with fixture results. Review is preferred over
inventing a decision. The raw compare response is made inspectable.
"""
import re
import math
from typing import Any
from app.rules import Policy, impact

MAX_POLICY_LENGTH = 12_000


def _usage_record(endpoint: str, result: Any) -> dict:
    """Read optional, official SDK response metadata; never infer billed credits."""
    record = {"endpoint": endpoint}
    for field in ("credits", "cost_usd", "model_ms"):
        value = getattr(result, field, None)
        record[field] = value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 else None
    return record


def _usage_summary(records: list[dict]) -> dict:
    credit_values = [r["credits"] for r in records]
    cost_values = [r["cost_usd"] for r in records]
    return {
        "request_count": len(records),
        "credits": sum(credit_values) if all(x is not None for x in credit_values) else None,
        "cost_usd": round(sum(cost_values), 8) if all(x is not None for x in cost_values) else None,
        "records": records,
        "note": "SDK-reported usage for this analysis; not a global spending cap.",
    }


def _root_json(result: Any) -> dict:
    if isinstance(result, dict):
        return dict(result)
    # The clocked SDK's Result is mapping-like; accept its documented read API.
    if hasattr(result, "data") and isinstance(result.data, dict):
        return result.data
    if hasattr(result, "items"):
        return dict(result.items())
    raise ValueError("Unexpected Clocked result structure")


def _field_value(field: Any) -> tuple[str, int | None]:
    """Unwrap the exact field value, retaining its optional source offset."""
    if field is None:
        return "", None
    if isinstance(field, str):
        return field, None
    if isinstance(field, (int, float)):
        return str(field), None
    if isinstance(field, list):
        return _field_value(field[0]) if field else ("", None)
    if isinstance(field, dict):
        pos = field.get("start")
        if pos is None and isinstance(field.get("span"), dict):
            pos = field["span"].get("start")
        for key in ("value", "text", "exact", "quote", "match", "raw"):
            if key in field and field[key] is not None:
                text, child_pos = _field_value(field[key])
                if text:
                    return text, pos if isinstance(pos, int) else child_pos
    return "", None


def _number_exact(raw: str, *, gpa: bool) -> float | int | None:
    # Strip currency formatting without accidentally accepting unrelated digits.
    pattern = r"(?<!\d)([0-4](?:\.\d{1,2})?)(?!\d)" if gpa else r"(?:\$\s*)?(\d{1,3}(?:,\d{3})+|\d{4,7})(?!\d)"
    numbers = re.findall(pattern, raw)
    if len(numbers) != 1:
        return None
    if gpa:
        value = float(numbers[0])
        return value if 0 <= value <= 4 else None
    return int(numbers[0].replace(",", ""))


def _source_sentence(source: str, start: int, end: int) -> str:
    """Find the source sentence containing an extracted fragment.

    Split only on sentence-ending punctuation followed by whitespace (and
    newlines), never the decimal point in a value such as 3.5.
    """
    for match in re.finditer(r"[^\n]*?(?:[.!?](?=\s|$)|\n|$)", source):
        if match.start() <= start and end <= match.end():
            return match.group().strip()
    # Graceful fallback on document formatting without sentences.
    return source[max(0, start - 140):min(len(source), end + 100)].strip()


def _supported_direction(sentence: str, *, gpa: bool) -> bool:
    """Reject directionally inverted or unsupported eligibility requirements.

    These checks are intentionally narrow. They *do not* replace the Clocked
    extraction; they prevent a plausible number from becoming a false decision.
    """
    if gpa:
        if not re.search(r"\bgpa\b", sentence, re.I):
            return False
        if re.search(r"\b(maximum gpa|gpa (?:maximum|at most|must not exceed)|gpa ceiling)\b", sentence, re.I):
            return False
        return bool(re.search(r"\b(minimum|at least|no less than|not below|not lower than)\b", sentence, re.I))
    if not re.search(r"\b(?:household\s+)?income\b", sentence, re.I):
        return False
    if re.search(r"\b(income (?:minimum|must exceed|must be at least)|minimum (?:annual )?(?:household )?income)\b", sentence, re.I):
        return False
    if not re.search(r"\b(?:must not exceed|not exceed|maximum|at most|no more than|income ceiling)\b", sentence, re.I):
        return False
    # The demo's currency representation and rules are explicitly USD only.
    # Without a clear currency, do not convert or silently assume dollars.
    return bool(re.search(r"\$|\bUSD\b|\bUS dollars\b", sentence, re.I))


def _extract_supported_rule(fields: dict, name: str, original: str, *, gpa: bool):
    raw, pos = _field_value(fields.get(name))
    if not raw:
        return None, ""
    # A Clocked-extracted value must appear *verbatim* in the source document.
    if raw not in original:
        return None, ""
    if pos is None:
        # Without a source span, a repeated phrase could belong to the wrong
        # section (for example, a historical policy quoted in a later one).
        if original.count(raw) != 1:
            return None, ""
        pos = original.index(raw)
    n = _number_exact(raw, gpa=gpa)
    if n is None:
        return None, raw
    if pos is not None and original[pos:pos+len(raw)] != raw:
        # An offset mismatch is an integrity signal; do not assume it is valid.
        return None, raw
    sentence = _source_sentence(original, pos, pos + len(raw))
    if not _supported_direction(sentence, gpa=gpa):
        return None, ""
    return n, raw


def _derive_policy(client, text: str, label: str) -> tuple[Policy, dict, dict]:
    extract_result = client.extract(
        text=text,
        instructions=(
            "Read ONLY the eligibility requirements of this policy. Copy a single "
            "verbatim phrase for each requested field, including its exact numeric "
            "threshold. If the rule is missing, unclear, qualified by an exception, "
            "or gives multiple alternatives, do not guess a value."
        ),
        fields={
            "minimum_gpa": "Exact excerpt explicitly stating the minimum required cumulative GPA (0.0–4.0 scale)",
            "maximum_household_income": "Exact excerpt explicitly stating the maximum allowed annual household income, including the monetary amount",
        },
    )
    extracted = _root_json(extract_result)
    usage = _usage_record("extract_previous" if label == "Previous version" else "extract_current", extract_result)
    # This demo is intentionally conservative about conditions outside its schema.
    # If it detects an additional restriction/exception, do not issue a positive
    # decision based on GPA and income alone. This is a heuristic, not a proof
    # that arbitrary unrestricted text is safe to decide on.
    unsupported = re.search(
        r"\b(unless|except|exception|waiver|either|alternative|citizenship|citizen|residency|resident|enrolled|enrollment|age|attendance|credit hours|disability|work experience|interview)\b",
        text, re.IGNORECASE,
    )
    fields = extracted.get("fields") or {}
    if not isinstance(fields, dict):
        fields = {}
    gpa, gpa_excerpt = _extract_supported_rule(fields, "minimum_gpa", text, gpa=True)
    income, income_excerpt = _extract_supported_rule(fields, "maximum_household_income", text, gpa=False)
    if unsupported:
        gpa = None
        income = None
    return Policy(label, gpa, income, gpa_excerpt, income_excerpt, "clocked.extract"), extracted, usage


def analyze_live(client, old: str, new: str, applicants: list[dict]) -> dict:
    if not old.strip() or not new.strip():
        raise ValueError("Both policy versions need text")
    if len(old) > MAX_POLICY_LENGTH or len(new) > MAX_POLICY_LENGTH:
        raise ValueError("Each policy must be at most 12,000 characters")
    old_policy, old_extract, old_usage = _derive_policy(client, old, "Previous version")
    new_policy, new_extract, new_usage = _derive_policy(client, new, "Current version")
    compare_result = client.compare(documents=[
        {"id": "previous", "text": old, "title": "Previous policy"},
        {"id": "current", "text": new, "title": "Current policy"},
    ])
    compared = _root_json(compare_result)
    # Rerank clauses so the reviewer can inspect which policies are relevant to the question.
    candidate_docs = [
        {"id": "prev-gpa", "text": old_policy.gpa_evidence or "No verified minimum GPA evidence"},
        {"id": "prev-income", "text": old_policy.income_evidence or "No verified maximum income evidence"},
        {"id": "current-gpa", "text": new_policy.gpa_evidence or "No verified minimum GPA evidence"},
        {"id": "current-income", "text": new_policy.income_evidence or "No verified maximum income evidence"},
    ]
    rerank_result = client.rerank(
        query="Which exact clauses establish the minimum GPA and maximum household income eligibility requirements, and where do those thresholds change?",
        documents=candidate_docs,
        top_n=4,
    )
    ranked = _root_json(rerank_result)
    usage = _usage_summary([old_usage, new_usage, _usage_record("compare", compare_result), _usage_record("rerank", rerank_result)])
    return {
        "mode": "live",
        "notice": "Live Clocked extraction, comparison and relevance ranking. Results remain conditional on the completeness of the policy and review of extracted evidence.",
        "documents": {"old": old, "new": new},
        "policies": {"old": old_policy.as_dict(), "new": new_policy.as_dict()},
        "comparison": {"verdict": compared.get("verdict"), "conflicts": compared.get("conflicts", []), "raw": compared},
        "relevance": ranked.get("results", []),
        "extraction": {"old": old_extract, "new": new_extract},
        "impact": impact(old_policy, new_policy, applicants),
        "api_calls": ["Clocked Extract ×2", "Clocked Compare ×1", "Clocked Rerank ×1"],
        "usage": usage,
    }