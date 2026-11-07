#!/usr/bin/env python3
"""Summarize independent Nikon Z8 C3.12 original-EX Photo/Movie experiment.

This is NOT a binary still-photo or video recording validator. It inspects
native original EX / original MAIN communication, source/display frame counts
and explicit mode-contact history. No vendor bytes, RAM dumps, or guest media
are included in reports.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def as_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            result = json.loads(value)
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def summarize(path: Path | None, exit_code: int | None) -> dict:
    record = {
        "scope": "experimental-original-ex-native-communication-and-mode-recovery",
        "exit_code": exit_code,
        "test_receipt_exists": bool(path and path.is_file()),
        "still_nef_file_qualified": False,
        "encoded_movie_file_qualified": False,
        "physical_lens_af_qualified": False,
        "mode_recovery_qualified": False,
        "original_ex_mcu_communication_qualified": False,
    }
    if not record["test_receipt_exists"]:
        return record
    data = json.loads(path.read_text())
    samples = data.get("native_samples", [])
    delivered = data.get("delivered_contacts", [])
    metrics = []
    for s in samples:
        clock = as_dict(s.get("runtime-clock-state"))
        raw = as_dict(s.get("raw-pipeline-state"))
        lcd = as_dict(s.get("engine1548-scanout-state"))
        try:
            ui = int.from_bytes(bytes.fromhex(s["ui_control_hex"])[4:8], "little")
        except (ValueError, TypeError, KeyError):
            ui = None
        metrics.append({
            "virtual_seconds": clock.get("virtual_ns", 0) / 1e9,
            "raw_frames": raw.get("frames"),
            "lcd_frames": lcd.get("frames"),
            "ui_mode": ui,
        })
    exstate = as_dict(data.get("final_native_mcu"))
    model = as_dict(data.get("native_model_state"))
    movie = as_dict(model.get("engine1543-control-state"))
    rows = data.get("checks", [])
    presses = [x.get("value") for x in delivered if x.get("property") == "mcu-contacts"]
    saw_movie = "23.10=0" in presses
    saw_photo = "23.10=1" in presses
    before_movie = max((x["raw_frames"] for x in metrics
                       if x["virtual_seconds"] < 20 and isinstance(x["raw_frames"], int)), default=None)
    after_photo = max((x["raw_frames"] for x in metrics
                       if x["virtual_seconds"] >= 38 and isinstance(x["raw_frames"], int)), default=None)
    record.update({
        "original_mcu_firmware_used": data.get("native_mcu") is True,
        "host_mcu_replies_disabled": data.get("host_mcu_messages") is False,
        "delivered_contacts": len(delivered),
        "movie_selector_contact_delivered": saw_movie,
        "photo_selector_return_contact_delivered": saw_photo,
        "original_ex_final_state": {k: v for k,v in exstate.items()
                                    if k in ("frames","bad_frames","main_frames","mcu_frames","checksum_errors",
                                             "tx_frames","rx_frames","main_nonidle","mcu_nonidle")},
        "movie_model_counters": {k:v for k,v in movie.items()
                                 if isinstance(v,(bool,int,float))},
        "first_raw_frames": before_movie, "raw_frames_after_photo_return": after_photo,
        "last_virtual_seconds": metrics[-1]["virtual_seconds"] if metrics else None,
        "observed_ui_modes": sorted({x["ui_mode"] for x in metrics
                                   if x["ui_mode"] is not None}),
        "harness_checks":len(rows),
        "harness_checks_failed":sum(x.get("passed") is not True for x in rows),
        "guest_error":data.get("error"),
    })
    clean = bool(exit_code == 0 and data.get("error") is None
                 and rows and all(x.get("passed") is True for x in rows))
    record["original_ex_mcu_communication_qualified"] = bool(
        clean and record["original_mcu_firmware_used"] and
        record["host_mcu_replies_disabled"] and len(delivered) >= 4)
    record["mode_recovery_qualified"] = bool(
        record["original_ex_mcu_communication_qualified"] and saw_movie and saw_photo
        and before_movie is not None and after_photo is not None
        and after_photo > before_movie)
    # A successful mode recovery is NOT evidence of video-encoded output or NEF.
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args=parser.parse_args()
    row=summarize(args.receipt,args.exit_code)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"native_ex_features.json").write_text(json.dumps(row,indent=2)+"\n")
    lines=["# Nikon Z8 3.12 — independent original EX firmware feature probe","",
        "The EX03.00 and MAIN3.12 components are actual CRC-verified Nikon firmware.",
        "Photo/Movie control contacts and frame counters use declared QEMU hardware fixtures.",
        "",
        "| Feature | Result |","| --- | --- |",
        f'| Original EX MCU communication | {row["original_ex_mcu_communication_qualified"]} |',
        f'| Movie lever to Photo mode recovery | {row["mode_recovery_qualified"]} |',
        f'| Actual saved NEF | {row["still_nef_file_qualified"]} (not tested) |',
        f'| Actual saved movie file | {row["encoded_movie_file_qualified"]} (not tested) |',
        f'| Physical lens AF/aperture | {row["physical_lens_af_qualified"]} (not tested) |',
        "", "A clean execution without the relevant counters and original EX communication",
        "does not automatically qualify a shooting or recording feature.", ""]
    (args.out/"native_ex_features.md").write_text("\n".join(lines))
    print(json.dumps(row,indent=2))


if __name__=="__main__":
    main()
