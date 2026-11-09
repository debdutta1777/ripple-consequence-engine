"""Transparent text-level policy comparison, never represented as an AI verdict.

Works for arbitrary selectable-text policy PDFs and preserves exact source lines.
It does not attempt to infer semantic equivalence or legal compliance.
"""
from difflib import SequenceMatcher
import re

MAX_CHANGES = 24


def _lines(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", s).strip() for s in text.splitlines()]
    return [s for s in lines if s][:160]


def compare_policy_text(before: str, after: str) -> dict:
    old = _lines(before)
    new = _lines(after)
    matcher = SequenceMatcher(None, [s.casefold() for s in old], [s.casefold() for s in new], autojunk=False)
    changes = []
    total = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_part, new_part = old[i1:i2], new[j1:j2]
        # Pair sequential lines for edit/replace; preserve remaining standalone additions/removals.
        count = max(len(old_part), len(new_part))
        for idx in range(count):
            b = old_part[idx] if idx < len(old_part) else ""
            a = new_part[idx] if idx < len(new_part) else ""
            status = "modified" if b and a else "removed" if b else "added"
            total += 1
            if len(changes) < MAX_CHANGES:
                changes.append({"type": status, "previous": b[:500], "updated": a[:500],
                                "previous_line": i1 + idx + 1 if b else None,
                                "updated_line": j1 + idx + 1 if a else None})
    return {"changes": changes, "total_changes": total, "truncated": total > MAX_CHANGES,
            "method": "literal line comparison (not semantic or legal analysis)"}