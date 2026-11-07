#!/usr/bin/env python3
"""Validate Z8 C3.11/C3.12 boot evidence from actual QEMU guest result.json.

Fails closed for missing ADC, lens reply or framebuffer guest-PC evidence.
Only qualifies a *bounded headless boot smoke*, never photo/video/physical lens
operation. Outputs a compact JSON/Markdown report without firmware or RAM dumps.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

SITES = {
    "311": {"adc": 0x41181504, "lens": 0x4106E690, "framebuffer": 0x40FAC9BC},
    "312": {"adc": 0x4118156C, "lens": 0x4106E6F8, "framebuffer": 0x40FACA24},
}
HASHES = {
    "311": "2b43a31c9de838f84b12416de4348a7004e65be07f853ec56ec2b10f3a8e3853",
    "312": "ec6f069e38f7bc4635fc7e6e9ae6304b3901953fadfdb9f33f011e4485b5b867",
}


def stop_pc_verified(row: dict, pc: int) -> bool:
    if row.get("timeout") or row.get("expected_pc", "").lower() != hex(pc):
        return False
    for cpu_registers in row.get("registers", []):
        match = re.search(r"\bPC=([0-9a-fA-F]+)", cpu_registers)
        if match and int(match.group(1), 16) == pc:
            return True
    return False


def inspect_guest(path: Path, version: str) -> dict:
    src = json.loads(path.read_text())
    required = SITES[version]
    stops = src.get("stops", [])
    observed = src.get("boot_callback_hits", [])
    replies = src.get("lens_reply_evidence", [])
    all_checks = src.get("checks", [])
    events = {name: sum(stop_pc_verified(row, pc) for row in stops)
              for name, pc in required.items() if name != "framebuffer"}
    frame_hits = sum(hit.get("pc", "").lower() == hex(required["framebuffer"])
                     for hit in observed if hit.get("from") == "qmp-info-registers")
    lens_good = [r for r in replies if r.get("runtime_pc", "").lower() == hex(required["lens"])
                 and r.get("status_word") == 0 and r.get("reply_bytes") == 8]
    profile = src.get("unqualified_c312_site_profile")
    profile_ok = (version != "312" or (isinstance(profile, dict)
        and profile.get("runtime_qualified") is False
        and all(k in profile.get("site_hits", {})
                for k in ("battery_callback", "lens_controller_reply", "framebuffer_event"))))
    raw = src.get("final_pipeline", {}).get("raw-pipeline-state", {})
    lcd = src.get("final_pipeline", {}).get("engine1548-scanout-state", {})
    result = {
        "version": f"3.{version[-2:]}",
        "expected_engine_sha256": HASHES[version],
        "actual_firmware_sha256": src.get("firmware_sha256"),
        "firmware_identity_ok": src.get("firmware_sha256") == HASHES[version],
        "runtime_qualified_profile_recorded": profile_ok,
        "adc_pc": hex(required["adc"]), "adc_actual_hits": events["adc"],
        "lens_pc": hex(required["lens"]), "lens_actual_hits": events["lens"],
        "lens_reply_count": len(replies), "lens_valid_reply_count": len(lens_good),
        "lens_reply_status_words": [r.get("status_word") for r in replies[:12]],
        "lens_completion_bytes": [r.get("completion_byte") for r in replies[:12]],
        "framebuffer_pc": hex(required["framebuffer"]),
        "framebuffer_qmp_confirmed_hits": frame_hits,
        "model_checks_total": len(all_checks),
        "model_checks_failed": sum(x.get("passed") is not True for x in all_checks),
        "raw_frames": raw.get("frames"), "lcd_frames": lcd.get("frames"),
        "guest_error": src.get("error"),
    }
    result["bounded_boot_evidence_passed"] = all([
        result["firmware_identity_ok"], profile_ok,
        events["adc"] >= 1, events["lens"] >= 1, len(lens_good) >= 1,
        frame_hits >= 1, bool(all_checks), result["model_checks_failed"] == 0,
        src.get("error") is None,
    ])
    # A boot smoke never proves actual lens AF/optics, NEF capture or video encode.
    result["still_photo_capture_qualified"] = False
    result["video_recording_qualified"] = False
    result["physical_lens_operation_qualified"] = False
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--old", type=Path, required=True)
    p.add_argument("--new", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    data = {"schema": "z8-c312-bounded-boot-evidence-v1",
            "capture_or_video_claims": "NOT VALIDATED BY THIS SMOKE",
            "c3_11": inspect_guest(args.old, "311"),
            "c3_12": inspect_guest(args.new, "312")}
    data["bounded_both_versions_pass"] = bool(
        data["c3_11"]["bounded_boot_evidence_passed"] and
        data["c3_12"]["bounded_boot_evidence_passed"])
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "runtime_evidence.json").write_text(json.dumps(data, indent=2) + "\n")
    rows = ["# Nikon Z8 3.11 / 3.12 — real guest PC acceptance evidence", "",
            "Actual vCPU PC stops, checks and lens reply words are parsed from QEMU receipts.",
            "This report **does not** establish photo capture, video recording or physical lens operation.", "",
            "| Check | C3.11 | C3.12 |", "| --- | ---: | ---: |"]
    for label, field in (
        ("Expected ADC breakpoint actual hits", "adc_actual_hits"),
        ("Lens callback actual hits", "lens_actual_hits"),
        ("Valid lens reply status=0", "lens_valid_reply_count"),
        ("Framebuffer guest PC hits", "framebuffer_qmp_confirmed_hits"),
        ("Model checks failed", "model_checks_failed"),
        ("Bounded boot evidence passed", "bounded_boot_evidence_passed"),
    ):
        rows.append(f'| {label} | {data["c3_11"][field]} | {data["c3_12"][field]} |')
    rows.extend(["", f'**Both versions passed:** {data["bounded_both_versions_pass"]}.', "",
                 "A fully-qualified camera requires separately recorded still photo, movie and physical-lens tests.", ""])
    (args.out / "runtime_evidence.md").write_text("\n".join(rows))
    print(json.dumps(data, indent=2))
    raise SystemExit(0 if data["bounded_both_versions_pass"] else 1)


if __name__ == "__main__":
    main()
