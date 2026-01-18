"""Red-team checks

Goal: catch obvious tier-gating/audit bypass mistakes before humans review PRs.

This is intentionally conservative and can be expanded over time.
"""

from __future__ import annotations

import pathlib
import re
import sys

FORBIDDEN_PATTERNS = [
    # UI-only gating language (should be enforced server-side too)
    re.compile(r"client-side\s+only\s+gating", re.IGNORECASE),
    re.compile(r"skip\s+audit", re.IGNORECASE),
    re.compile(r"bypass\s+lock", re.IGNORECASE),
]

SUSPECT_FILES = [
    "apps",
    "services/api",
]

def main() -> None:
    root = pathlib.Path(__file__).resolve().parents[3]
    hits: list[str] = []

    for folder in SUSPECT_FILES:
        p = root / folder
        if not p.exists():
            continue
        for file in p.rglob("*"):
            if file.is_dir():
                continue
            if file.suffix.lower() not in {".py", ".ts", ".tsx", ".js", ".md"}:
                continue
            text = file.read_text(encoding="utf-8", errors="ignore")
            for pat in FORBIDDEN_PATTERNS:
                if pat.search(text):
                    hits.append(f"{file}: matched {pat.pattern}")

    if hits:
        print("REDTEAM FAILED — forbidden patterns found:")
        for h in hits:
            print(" -", h)
        sys.exit(1)

    # Ensure Cursor rules exist (repo discipline)
    assert (root / ".cursorrules").exists(), "Missing .cursorrules"
    assert (root / ".cursor" / "rules.md").exists(), "Missing .cursor/rules.md"

    print("OK: red-team checks passed")

if __name__ == "__main__":
    main()
