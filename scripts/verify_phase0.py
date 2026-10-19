#!/usr/bin/env python3
"""Phase 0 verification: document integrity and Gate 0 decision.

Usage:
    python3 scripts/verify_phase0.py          # integrity checks (exit 0 = docs consistent)
    python3 scripts/verify_phase0.py --gate   # also require Gate 0 conditions (exit 0 = gate passes)

Standard library only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "MASTER_BUILD_SPEC.md",
    "AGENTS.md",
    "README.md",
    "docs/decision-log.md",
    "docs/phase-0-assessment.md",
    "docs/architecture.md",
    "docs/threat-model.md",
    "docs/development-plan.md",
]
REQUIRED_FIELDS = [
    "Decision", "Date", "Tier", "Owner", "Approver", "Context", "Alternatives",
    "Rationale", "Security/Ops impact", "Reversibility", "Evidence", "Status",
]
ALLOWED_STATUS = {"Approved", "Proposed", "Rejected", "Superseded"}
# Spec section 2 open decisions -> keyword that must appear in the assessment coverage table.
SPEC_OPEN_DECISIONS = [
    "VPS provider", "AI provider", "Data sensitivity", "Pack manifest",
    "Backup destination", "Per-tenant encryption", "reference pack",
    "Webhook providers", "RPO and RTO", "Approval owners", "Minimum UI",
]
PLACEHOLDER_RE = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b|待补")
DEC_HEADER_RE = re.compile(r"^### (D-\d{3}) (.+)$", re.M)
FIELD_RE = re.compile(r"^- \*\*(.+?):\*\* ?(.*)$", re.M)
THREAT_ROW_RE = re.compile(r"^\| (T-\d{2}) \|.*?\| (RT-\d{2}) \|", re.M)
LINK_RE = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.passed = 0

    def check(self, ok: bool, msg: str) -> None:
        if ok:
            self.passed += 1
        else:
            self.errors.append(msg)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def parse_decisions(text: str) -> dict[str, dict[str, str]]:
    decisions: dict[str, dict[str, str]] = {}
    headers = list(DEC_HEADER_RE.finditer(text))
    for i, h in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[h.end():end]
        fields = {m.group(1).strip(): m.group(2).strip() for m in FIELD_RE.finditer(body)}
        fields["_title"] = h.group(2).strip()
        decisions[h.group(1)] = fields
    return decisions


def main(gate: bool) -> int:
    r = Report()

    # 1. Required files
    for f in REQUIRED_FILES:
        r.check((ROOT / f).is_file(), f"missing required file: {f}")
    if r.errors:
        return finish(r, gate, None)

    docs = {f: read(f) for f in REQUIRED_FILES}

    # 2. Decision log structure
    decisions = parse_decisions(docs["docs/decision-log.md"])
    r.check(len(decisions) > 0, "no decisions found in decision-log.md")
    ids = list(decisions)
    r.check(len(ids) == len(set(ids)), "duplicate decision IDs")
    expected = [f"D-{n:03d}" for n in range(1, len(ids) + 1)]
    r.check(ids == expected, f"decision IDs not sequential: {ids}")
    for did, fields in decisions.items():
        for field in REQUIRED_FIELDS:
            r.check(bool(fields.get(field)), f"{did}: missing or empty field '{field}'")
        status = fields.get("Status", "")
        r.check(status in ALLOWED_STATUS, f"{did}: invalid status '{status}'")
        r.check(fields.get("Tier", "") in {"1", "2", "3"}, f"{did}: Tier must be 1, 2 or 3")
        if status == "Approved":
            r.check("待定" not in fields.get("Evidence", ""),
                    f"{did}: Approved but Evidence still pending")

    # 3. Every D-xxx referenced anywhere exists
    for f, text in docs.items():
        if f == "MASTER_BUILD_SPEC.md":
            continue
        for ref in set(re.findall(r"\bD-\d{3}\b", text)):
            r.check(ref in decisions, f"{f}: references unknown decision {ref}")

    # 4. Spec open decisions covered in assessment
    assessment = docs["docs/phase-0-assessment.md"]
    for kw in SPEC_OPEN_DECISIONS:
        r.check(kw in assessment, f"assessment does not cover open decision: {kw}")

    # 5. Threat model: every threat maps to a unique red-team test
    threats = THREAT_ROW_RE.findall(docs["docs/threat-model.md"])
    r.check(len(threats) >= 20, f"threat model has only {len(threats)} mapped threats")
    t_ids = [t for t, _ in threats]
    rt_ids = [rt for _, rt in threats]
    r.check(len(t_ids) == len(set(t_ids)), "duplicate threat IDs")
    r.check(len(rt_ids) == len(set(rt_ids)), "duplicate red-team test IDs")
    known_t = set(t_ids)
    for f, text in docs.items():
        if f == "MASTER_BUILD_SPEC.md":
            continue
        for ref in set(re.findall(r"\bT-\d{2}\b", text)):
            r.check(ref in known_t, f"{f}: references unknown threat {ref}")
    known_rt = set(rt_ids)
    for f in ("docs/development-plan.md", "docs/decision-log.md", "docs/threat-model.md"):
        for ref in set(re.findall(r"\bRT-\d{2}\b", docs[f])):
            r.check(ref in known_rt, f"{f}: references unknown red-team test {ref}")
    # every RT test is scheduled in the development plan (ranges like RT-01 至 RT-05 count)
    plan = docs["docs/development-plan.md"]
    scheduled: set[str] = set(re.findall(r"\bRT-\d{2}\b", plan))
    for a, b in re.findall(r"RT-(\d{2}) 至 RT-(\d{2})", plan):
        scheduled |= {f"RT-{n:02d}" for n in range(int(a), int(b) + 1)}
    for rt in rt_ids:
        r.check(rt in scheduled, f"{rt} is not scheduled in development-plan.md")

    # 6. No placeholders
    for f, text in docs.items():
        if f == "MASTER_BUILD_SPEC.md":
            continue
        for m in PLACEHOLDER_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            r.check(False, f"{f}:{line}: placeholder '{m.group(0)}'")

    # 7. Relative links resolve
    for f, text in docs.items():
        base = (ROOT / f).parent
        for target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            r.check((base / target).exists(), f"{f}: broken link -> {target}")

    return finish(r, gate, decisions)


def finish(r: Report, gate: bool, decisions: dict[str, dict[str, str]] | None) -> int:
    print(f"Integrity checks passed: {r.passed}")
    if r.errors:
        print(f"Integrity checks FAILED: {len(r.errors)}")
        for e in r.errors:
            print(f"  ✗ {e}")
        return 1
    print("Integrity: OK")

    assert decisions is not None
    by_status: dict[str, list[str]] = {}
    for did, fields in decisions.items():
        by_status.setdefault(fields["Status"], []).append(did)
    summary = ", ".join(f"{k}={len(v)}" for k, v in sorted(by_status.items()))
    print(f"Decisions: {summary}")

    proposed = by_status.get("Proposed", [])
    r01 = [d for d, f in decisions.items()
           if "ELIO" in f["_title"] and "分工" in f["_title"] and f["Status"] == "Approved"]
    gate_ok = not proposed and bool(r01)
    if gate_ok:
        print("Gate 0: PASS")
    else:
        print("Gate 0: PENDING APPROVAL")
        if proposed:
            print(f"  - still Proposed: {', '.join(proposed)}")
        if not r01:
            print("  - missing Approved decision titled with 'ELIO' and '分工' (risk R-01)")
    if gate and not gate_ok:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(gate="--gate" in sys.argv[1:]))
