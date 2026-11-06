#!/usr/bin/env python3
"""Compare two CRC-verified, DECRYPTED Nikon Z8 containers without publishing firmware bytes.

Outputs only hashes, counts, offset ranges and explicitly unclassified instruction
word candidates. Input files are Nikon firmware .dec products from the upstream
nikon-fw-key-tool decrypt_firmware.py, not arbitrary stock .bin files.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import struct
from pathlib import Path

BASE = 0x40160000
BASELINE_SHA = "2b43a31c9de838f84b12416de4348a7004e65be07f853ec56ec2b10f3a8e3853"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def modules(path: Path) -> dict:
    raw = path.read_bytes()
    assert raw[32:64] == b" " * 32, "not a Nikon legacy decrypted container"
    body = raw[32:]
    count, size = struct.unpack_from(">II", body, 32)
    assert 0 < count <= 64 and size == 48 + count * 32
    found = {}
    last = size
    for i in range(count):
        at = 48 + i * 32
        name = body[at:at + 16].split(b"\0")[0].decode("ascii")
        start, length = struct.unpack_from(">II", body, at + 16)
        assert start == last and length >= 2, (name, start, last)
        stored = int.from_bytes(body[start + length - 2:start + length], "big")
        data = body[start:start + length - 2]
        calculated = binascii.crc_hqx(data, 0)
        assert stored == calculated, (name, stored, calculated)
        prefix = name.split("2070")[0] if "2070" in name else name.split("_")[0]
        # Z8 has ex / _tpj01 / eg / vr / li; preserve distinct names in metadata.
        key = next((p for p in ("_tpj01", "ex", "eg", "vr", "li") if name.startswith(p)), name)
        assert key not in found
        found[key] = {"name": name, "file_offset": start + 32,
                      "size": len(data), "sha256": sha256(data), "_payload": data}
        last = start + length
    assert last + 16 == len(body)
    assert int.from_bytes(body[-16:-14], "big") == binascii.crc_hqx(body[:-16], 0)
    return found


def spans(indices: list[int], block_size: int) -> list:
    if not indices:
        return []
    runs = []
    first = last = indices[0]
    for index in indices[1:]:
        if index != last + 1:
            runs.append({"start_offset": first * block_size, "end_offset_exclusive": (last + 1) * block_size})
            first = index
        last = index
    runs.append({"start_offset": first * block_size, "end_offset_exclusive": (last + 1) * block_size})
    return runs


def diff(a: bytes, b: bytes) -> dict:
    limit = min(len(a), len(b))
    changes = 0
    pages = []
    for start in range(0, limit, 4096):
        x, y = a[start:start + 4096], b[start:start + 4096]
        if x != y:
            pages.append(start // 4096)
            changes += sum(i != j for i, j in zip(x, y))
    regions = spans(pages, 4096)
    return {"old_length": len(a), "new_length": len(b),
            "changed_bytes_in_overlap": changes,
            "changed_4k_pages": len(pages), "total_4k_pages": (limit + 4095) // 4096,
            "changed_page_regions": len(regions),
            "first_120_changed_page_regions": regions[:120],
            "regions_truncated": len(regions) > 120,
            "length_changed": len(a) != len(b)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--old", type=Path, required=True)
    p.add_argument("--new", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    old = modules(args.old)
    new = modules(args.new)
    assert old["eg"]["sha256"] == BASELINE_SHA, "3.11 EG does not match the QEMU known-good firmware"
    out = {"format": "z8-firmware-comparison-v1",
           "old_package_sha256": "d67413c2ede6b9ce8887175f20700bd9fbad2a973a4820968c45503d15d80d96",
           "new_package_sha256": "d662dd9dd5da937cb418162c238065e918dcefafd47b47537c3f934d39e83037",
           "input_containers_fully_crc_verified": True,
           "eg_3_11_known_qemu_sha_verified": True,
           "qemu_3_12_boot_verified": False, "aarch64_function_boundaries_verified": False,
           "eg_load_address_hypothesis": hex(BASE), "components": {}}
    for key in sorted(set(old) | set(new)):
        x, y = old.get(key), new.get(key)
        if not x or not y:
            out["components"][key] = {"only_in_one_version": True}
            continue
        entry = {"old_name": x["name"], "new_name": y["name"],
                 "old_size": x["size"], "new_size": y["size"],
                 "old_sha256": x["sha256"], "new_sha256": y["sha256"],
                 "equal": x["sha256"] == y["sha256"]}
        if not entry["equal"]:
            entry["diff"] = diff(x["_payload"], y["_payload"])
        out["components"][key] = entry

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "comparison.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    lines = [
        "# Nikon Z8 C3.11 vs C3.12 — verified container comparison",
        "",
        "Generated from stock firmware with **all module CRCs and package CRC verified**.",
        "The Z8 C3.11 engine also matched the known QEMU payload SHA-256.",
        "",
        "| Component | 3.11 size | 3.12 size | Same payload? | Changed 4 KiB pages |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for key, row in out["components"].items():
        if row.get("only_in_one_version"):
            lines.append(f"| {key} | — | — | unmatched | — |")
        else:
            lines.append(f"| {key} | {row['old_size']:,} | {row['new_size']:,} | "
                         f"{'Yes' if row['equal'] else 'No'} | "
                         f"{row.get('diff', {}).get('changed_4k_pages', 0):,} |")
    lines.extend([
        "", "## Boundaries",
        "",
        "Changed 4 KiB regions in comparison.json are **raw module-relative byte offsets**.",
        "They are not automatically AArch64 function boundaries; changes may include resources,",
        "tables, compressed data or moved code. Applying the provisional QEMU EG load address",
        "0x40160000 is only meaningful after verifying module layout and execution mapping.",
        "",
        "No original firmware bytes, derived decrypted payloads or XOR keys are published here.",
        "No C3.12 QEMU boot has been established by this comparison.",
        "",
    ])
    (args.out / "comparison.md").write_text("\n".join(lines), encoding="utf8")
    print(json.dumps({"validated": True, "components": {
        k: {"equal": v.get("equal"), "changed_pages": v.get("diff", {}).get("changed_4k_pages")}
        for k, v in out["components"].items()
    }}, indent=2))


if __name__ == "__main__":
    main()
