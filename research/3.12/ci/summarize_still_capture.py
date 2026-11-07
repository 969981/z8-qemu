#!/usr/bin/env python3
"""Bounded, read-only Nikon Z8 C3.12 card-backed still capture evidence.

A file entry on the guest-owned virtual card proves guest filesystem output
only, not valid RAW pixels or photo quality. Media and firmware stay on the CI
runner; this report contains only names and lengths.
"""
from __future__ import annotations
import argparse
import json
import struct
import sys
from pathlib import Path

TOOLS=Path(__file__).resolve().parents[3]/"tools"
sys.path.insert(0,str(TOOLS))
from inspect_card_volume import catalog  # noqa: E402


def summarize(receipt: Path, card: Path, exit_code: int) -> dict:
    result={
        "test": "C3.12-host-peer-experimental-single-lossless-photo",
        "exit_code":exit_code,
        "guest_receipt_exists":receipt.is_file(),
        "card_exists":card.is_file(),
        "exfat_catalog_valid":False,
        "guest_created_nef":False,
        "raw_pixels_independently_decoded":False,
        "photo_capture_end_to_end_qualified":False,
        "physical_shutter_synchronization_qualified":False,
    }
    if receipt.is_file():
        obj=json.loads(receipt.read_text())
        checks=obj.get("checks",[])
        result["guest_error"]=obj.get("error")
        result["model_checks"]=len(checks)
        result["model_checks_failed"]=sum(x.get("passed") is not True for x in checks)
        result["virtual_card_written"]=bool(obj.get("virtual_card"))
        result["guest_code_modified"]=False
    if card.is_file():
        try:
            with card.open("rb") as s:
                mbr=s.read(512)
            if mbr[510:]!=b"\x55\xaa":
                raise ValueError("invalid MBR signature")
            start=struct.unpack_from("<I",mbr,454)[0]*512
            parsed=catalog(card,start)
            files=[{"path":x["path"],"bytes":x["bytes"]}
                   for x in parsed["files"] if not x["directory"]]
            nef=[x for x in files if x["path"].upper().endswith(".NEF")
                 and x["bytes"]>1_000_000]
            result.update(exfat_catalog_valid=True,files=files[:60],
                          guest_created_nef=bool(nef),guest_nef_files=nef[:20])
        except (ValueError,OSError,IndexError,struct.error) as exc:
            result["exfat_error"]=type(exc).__name__+": "+str(exc)[:250]
    result["guest_still_write_observed"]=bool(
        exit_code==0 and result.get("guest_error") is None and
        result["guest_created_nef"] and result["exfat_catalog_valid"])
    # The full test requires separate independent pixel/container decoders.
    return result


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--card",type=Path,required=True)
    p.add_argument("--exit-code",type=int,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=summarize(a.receipt,a.card,a.exit_code)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"still_capture_evidence.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# Z8 C3.12 experimental guest RAW capture", "",
           "Synthetic sensor and virtual exFAT card; no physical camera.",
           "", "| Gate | Status |","| --- | --- |",
           f'| Capturer ended cleanly | {result["exit_code"]==0} |',
           f'| Valid exFAT catalog | {result["exfat_catalog_valid"]} |',
           f'| Guest created nonempty NEF | {result["guest_created_nef"]} |',
           f'| Independently decoded RAW pixels | {result["raw_pixels_independently_decoded"]} |',
           f'| Photo end-to-end qualified | {result["photo_capture_end_to_end_qualified"]} |',
           "",
           "NEF file presence alone is insufficient for RAW decode acceptance.",
           "Physical optics, shutter timing and photographic quality remain unqualified.", ""]
    (a.out/"still_capture_evidence.md").write_text("\n".join(lines))
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
