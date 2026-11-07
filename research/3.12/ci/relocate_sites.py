#!/usr/bin/env python3
"""Discover C3.12 candidates for *known C3.11 breakpoints*, without activation.

Uses unique, byte-identical AArch64 neighborhood anchors on CRC-verified main
images. The output is an independent evidence-bearing candidate profile. A
neighbor match is NOT proof that the candidate has the same runtime semantics.
Uncertain mappings stay null; QEMU must not silently fall back to 3.11 addresses.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path

from compare_z8 import BASE, BASELINE_SHA, modules

NEW_SHA = "ec6f069e38f7bc4635fc7e6e9ae6304b3901953fadfdb9f33f011e4485b5b867"
ANCHOR_BYTES = 24
MAX_DISPLACEMENT = 0x20000


def resolve(old: bytes, new: bytes, pc: int, *, search_radius=MAX_DISPLACEMENT) -> dict:
    index = pc - BASE
    if not 0 <= index <= min(len(old), len(new)) - ANCHOR_BYTES:
        return {"status": "outside_payload", "candidate_pc": None}
    if old[index:index + 64] == new[index:index + 64]:
        return {"status": "byte_identical", "candidate_pc": hex(pc),
                "confidence": "exact_bytes_not_runtime_tested",
                "shift": 0, "unique_anchors": 0}
    lo = max(0, index - search_radius)
    hi = min(len(new), index + search_radius + ANCHOR_BYTES)
    window = new[lo:hi]
    evidence = []
    # Include anchors in both directions to detect insertion/deletion offsets.
    for rel in range(-768, 769, 16):
        origin = index + rel
        if origin < 0 or origin + ANCHOR_BYTES > len(old):
            continue
        token = old[origin:origin + ANCHOR_BYTES]
        first = window.find(token)
        if first < 0 or window.find(token, first + 1) >= 0:
            continue  # Require unique occurrence inside the relocation window.
        match = lo + first
        shift = match - origin
        if abs(shift) > search_radius:
            continue
        evidence.append({"delta": shift, "old_relative": rel, "new_relative": match-index})
    by_delta = collections.defaultdict(list)
    for e in evidence:
        by_delta[e["delta"]].append(e)
    ranked = sorted(by_delta.items(), key=lambda kv: (
        -len(kv[1]), min(abs(e["old_relative"]) for e in kv[1]), abs(kv[0])))
    if not ranked:
        return {"status": "unresolved", "candidate_pc": None, "unique_anchors": 0}
    best_delta, hits = ranked[0]
    runners = len(ranked) > 1 and len(ranked[1][1]) >= len(hits) * 0.75
    left = [e for e in hits if e["old_relative"] <= -ANCHOR_BYTES]
    right = [e for e in hits if e["old_relative"] >= 4]
    near_left = min((abs(e["old_relative"]) for e in left), default=None)
    near_right = min((abs(e["old_relative"]) for e in right), default=None)
    # Confidence is strict: several unique anchors BOTH sides, no similar shift,
    # and at least one nearby on each side. Otherwise do not activate candidate.
    supported = (not runners and len(hits) >= 5 and len(left) >= 2
                 and len(right) >= 2 and near_left <= 256 and near_right <= 256)
    new_offset = index + best_delta
    result = {"status": "two_sided_anchor_candidate" if supported else "ambiguous",
              "candidate_pc": hex(BASE + new_offset) if supported else None,
              "confidence": "static_candidate_not_runtime_validated" if supported else "insufficient",
              "candidate_shift": best_delta, "unique_anchors": len(evidence),
              "supporting_anchors": len(hits),
              "support_before": len(left), "support_after": len(right),
              "nearest_before_bytes": near_left, "nearest_after_bytes": near_right,
              "runner_up_support": len(ranked[1][1]) if len(ranked) > 1 else 0,
              "neighbor_at_candidate_identical": old[index:index+4] == new[new_offset:new_offset+4]}
    # Only keep shifts / support metadata, no firmware bytes.
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", type=Path, required=True)
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--profile", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    old = modules(a.old)["eg"]
    new = modules(a.new)["eg"]
    assert old["sha256"] == BASELINE_SHA, "C3.11 baseline mismatch"
    assert new["sha256"] == NEW_SHA, "C3.12 image mismatch"
    profile = json.loads(a.profile.read_text(encoding="utf-8"))
    assert profile["engine_sha256"] == BASELINE_SHA
    result = {
        "schema": "nikon-z8-c312-static-address-candidates-v1",
        "version": "3.12",
        "input_engine_sha256": NEW_SHA,
        "reference_engine_sha256": BASELINE_SHA,
        "runtime_qualified": False,
        "provenance": "CRC-verified stock C3.11/C3.12 EG module byte-neighborhood anchors",
        "sites": {}
    }
    for name, pc in profile["sites"].items():
        row = resolve(old["_payload"], new["_payload"], int(pc, 16))
        row["reference_pc"] = pc
        result["sites"][name] = row
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "relocation_candidates.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    status = collections.Counter(x["status"] for x in result["sites"].values())
    lines = ["# Z8 C3.12 static breakpoint relocation candidates", "",
             "All firmware modules and package CRCs verified. **No runtime equivalence verified.**",
             "Ambiguous sites have a null candidate PC, by design.", "",
             "| Site | C3.11 PC | C3.12 candidate PC | Status | Anchors |",
             "| --- | --- | --- | --- | ---: |"]
    for name, row in result["sites"].items():
        lines.append(f'| {name} | `{row["reference_pc"]}` | '
                     f'`{row.get("candidate_pc") or "UNRESOLVED"}` | {row["status"]} | '
                     f'{row.get("supporting_anchors", 0)} |')
    lines.extend(["", f"Status counts: `{dict(status)}`", "",
                  "Do not use an unvalidated address profile for capture or physical firmware changes.", ""])
    (a.out / "relocation_candidates.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status_counts": dict(status),
                      "adc": result["sites"]["battery_callback"],
                      "lens": result["sites"]["lens_controller_reply"],
                      "framebuffer": result["sites"]["framebuffer_event"]}, indent=2))


if __name__ == "__main__":
    main()
