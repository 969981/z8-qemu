# SPDX-License-Identifier: GPL-2.0-or-later
"""Fail-closed, opt-in C3.12 research breakpoint address resolution.

With no research environment variables this module returns *exactly* the
existing C3.11 literal breakpoint address. It does not modify firmware bytes.
3.12 candidate addresses remain unqualified and can be used only after
explicit acceptance in an isolated runtime test.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

C312_SHA = "ec6f069e38f7bc4635fc7e6e9ae6304b3901953fadfdb9f33f011e4485b5b867"


def pc(g, site: str, original: int) -> int:
    source = os.environ.get("Z8_C312_SITE_PROFILE")
    if not source:
        return original
    if os.environ.get("Z8_C312_ALLOW_UNQUALIFIED_BOOT") != "1":
        raise RuntimeError("C3.12 research profile requires explicit unqualified-boot opt-in")
    profile = getattr(g, "_z8_c312_research_profile", None)
    if profile is None:
        profile = json.loads(Path(source).read_text(encoding="utf-8"))
        if (profile.get("schema") != "nikon-z8-breakpoint-sites-v1"
                or profile.get("firmware_version") != "3.12"
                or profile.get("engine_sha256") != C312_SHA
                or profile.get("runtime_qualified") is not False):
            raise ValueError("invalid or wrongly qualified C3.12 research site profile")
        # Verify actual guest payload, independent of the site's self-reported hash.
        with g.firmware.open("rb") as inp:
            actual = hashlib.file_digest(inp, "sha256").hexdigest()
        if actual != C312_SHA:
            raise ValueError("C3.12 breakpoint profile is not valid for this guest image")
        g._z8_c312_research_profile = profile
        g.data["unqualified_c312_site_profile"] = {
            "version": "3.12", "guest_sha256": actual,
            "runtime_qualified": False, "static_candidate_only": True,
            "site_hits": {}}
    entry = profile["sites"].get(site)
    evidence = profile.get("evidence", {}).get(site, {})
    if not isinstance(entry, str) or evidence.get("reference_pc", "").lower() != hex(original):
        raise RuntimeError(f"unresolved or mismatched C3.12 research site: {site}")
    result = int(entry, 16)
    if result % 4 or not 0x40160000 <= result < 0x45000000:
        raise ValueError(f"invalid C3.12 breakpoint address for {site}")
    g.data["unqualified_c312_site_profile"]["site_hits"][site] = {
        "reference_pc": hex(original), "candidate_pc": hex(result),
        "candidate_only": True}
    return result
