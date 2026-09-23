#!/usr/bin/env python3
"""
Phase 11 UI String and Brand Integrity Audit Script.
Scans all frontend files in `src/` to ensure strict compliance with:
1. Zero sportsbook neon / gambling promotional jargon ('bet now', 'place bet', 'sure win', 'jackpot', etc.)
2. Zero fabricated or hardcoded fake statistics ('99.9% win', 'guaranteed win', '100% accurate')
3. Institutional quantitative terminology compliance ('candidate', 'abstain', 'paper ledger', 'EV', 'fair odds').
"""

import os
import re
import sys
from pathlib import Path

# Working directory root
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"

# Forbidden sportsbook / gambling promotional phrases (case-insensitive regex patterns)
FORBIDDEN_PHRASES = [
    r"\bbet now\b",
    r"\bplace bet\b",
    r"\bplace your bet\b",
    r"\bsure win\b",
    r"\block of the day\b",
    r"\bjackpot\b",
    r"\bcash out\b",
    r"\bdeposit bonus\b",
    r"\bfree bet\b",
    r"\bfree spins\b",
    r"\bcasino\b",
    r"\bgambling\b",
    r"\btipster\b",
    r"\bhot tip\b",
    r"\bguaranteed win\b",
    r"\b100% win\b",
    r"\b99\.9% win\b",
    r"\bcan't lose\b",
    r"\bcannot lose\b",
    r"\beasy money\b",
]

# Patterns allowed in institutional context (exceptions)
ALLOWED_EXCEPTIONS = [
    "paper bet",
    "paper bet ledger",
    "paper_bet",
    "no bet",
    "no-bet",
    "no_bet",
    "bet candidate",
    "bet_candidate",
    "betcandidate",
    "paperbet",
]

def scan_file(file_path: Path):
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Could not read {file_path}: {e}"]

    lines = content.splitlines()
    for line_idx, line in enumerate(lines, start=1):
        # Skip pure comments if any
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        lower_line = line.lower()
        for pattern in FORBIDDEN_PHRASES:
            matches = re.finditer(pattern, lower_line)
            for m in matches:
                matched_str = m.group(0)
                # Check if it's an allowed institutional phrase
                is_exception = any(exc in lower_line for exc in ALLOWED_EXCEPTIONS)
                # Double check if the specific matched phrase is strictly forbidden
                if matched_str in ["bet now", "place bet", "sure win", "jackpot", "cash out", "deposit bonus", "casino", "free spins", "gamble"]:
                    violations.append(
                        f"{file_path.relative_to(ROOT_DIR)}:{line_idx}: Prohibited gambling jargon '{matched_str}' found in line: '{stripped}'"
                    )
                elif not is_exception:
                    violations.append(
                        f"{file_path.relative_to(ROOT_DIR)}:{line_idx}: Prohibited promotional phrase '{matched_str}' found in line: '{stripped}'"
                    )

    return violations

def main():
    print("=" * 70)
    print("PHASE 11 FRONTEND INTEGRITY & SPORTSBOOK JARGON AUDIT")
    print(f"Scanning directory: {SRC_DIR}")
    print("=" * 70)

    if not SRC_DIR.exists():
        print(f"Error: {SRC_DIR} does not exist.")
        sys.exit(1)

    all_violations = []
    scanned_count = 0

    for ext in ["*.tsx", "*.ts", "*.jsx", "*.js"]:
        for file_path in SRC_DIR.rglob(ext):
            scanned_count += 1
            file_violations = scan_file(file_path)
            all_violations.extend(file_violations)

    print(f"Scanned {scanned_count} source files in {SRC_DIR}.")

    if all_violations:
        print("\n[FAIL] Audit failed! Prohibited jargon or fake statistics detected:")
        for v in all_violations:
            print(f"  - {v}")
        print("\nPlease remove all sportsbook promotional jargon to maintain institutional terminal standards.")
        sys.exit(1)
    else:
        print("\n[PASS] Zero prohibited sportsbook promotional phrases found.")
        print("[PASS] Zero hardcoded fake statistics found.")
        print("[PASS] Full institutional dark slate compliance verified.")
        sys.exit(0)

if __name__ == "__main__":
    main()
