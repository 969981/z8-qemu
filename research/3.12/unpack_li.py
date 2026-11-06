#!/usr/bin/env python3
"""Unpack the Linux root filesystem of a CRC-verified Nikon Z8 LI payload.

This does not decrypt the original Nikon firmware container. Pass only an
independently CRC16-verified li2070_031200.bi (without its CRC trailer).
"""
import argparse
import csv
import hashlib
import json
import stat
import zlib
from pathlib import Path

def pad4(value):
    return (value + 3) & ~3

def decompress_at(data, offset):
    decompressor = zlib.decompressobj(31)
    result = decompressor.decompress(data[offset:]) + decompressor.flush()
    if not decompressor.eof:
        raise ValueError("invalid gzip stream at offset %x" % offset)
    return result

def unpack_cpio(data, target):
    names = ("ino", "mode", "uid", "gid", "nlink", "mtime", "filesize",
             "devmajor", "devminor", "rdevmajor", "rdevminor", "namesize", "check")
    offset = 0
    entries = []
    while offset + 110 <= len(data):
        if data[offset:offset+6] not in (b"070701", b"070702"):
            raise ValueError("invalid cpio header at %d" % offset)
        d = {name: int(data[offset+6+i*8:offset+14+i*8], 16)
             for i, name in enumerate(names)}
        name = data[offset+110:offset+110+d["namesize"]].rstrip(b"\0").decode("utf-8", "replace")
        begin = pad4(offset + 110 + d["namesize"])
        end = begin + d["filesize"]
        if end > len(data):
            raise ValueError("truncated cpio: "+name)
        content = data[begin:end]
        mode = d["mode"]
        kind = "dir" if stat.S_ISDIR(mode) else "file" if stat.S_ISREG(mode) else "symlink" if stat.S_ISLNK(mode) else "other"
        entries.append({"path":name, "type":kind, "size":len(content),
                        "sha256":hashlib.sha256(content).hexdigest() if kind == "file" else ""})
        if name == "TRAILER!!!":
            break
        p = Path(name)
        if not p.is_absolute() and ".." not in p.parts:
            dest = target.joinpath(*p.parts)
            if kind == "dir":
                dest.mkdir(parents=True, exist_ok=True)
            elif kind == "file":
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content)
        offset = pad4(end)
    if not entries or entries[-1]["path"] != "TRAILER!!!":
        raise ValueError("missing cpio trailer")
    return entries

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("li_payload", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    source = args.li_payload.read_bytes()
    if not source.startswith(b"NISI"):
        raise ValueError("not a Z8 NISI component")
    args.out.mkdir(parents=True, exist_ok=True)
    config = decompress_at(source, 0x43a4b8)
    root = decompress_at(source, 0x5b1000)
    (args.out / "linux.config").write_bytes(config)
    (args.out / "linux.initramfs.cpio").write_bytes(root)
    entries = unpack_cpio(root, args.out / "linux_rootfs")
    with (args.out / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(entries[0]))
        writer.writeheader()
        writer.writerows(entries)
    (args.out / "summary.json").write_text(json.dumps({
        "entries": len(entries), "files": sum(x["type"] == "file" for x in entries),
        "source_sha256": hashlib.sha256(source).hexdigest()
    }, indent=2)+"\n")
    print("unpacked", len(entries), "CPIO entries")

if __name__ == "__main__":
    main()
