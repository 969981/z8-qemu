# SPDX-License-Identifier: GPL-2.0-or-later
"""Acceptance validator must refuse a clean exit without actual guest evidence."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"research/3.12/ci/verify_runtime_evidence.py"
spec=importlib.util.spec_from_file_location("z8_runtime_evidence",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample(version):
    key="312" if version=="312" else "311"
    p=module.SITES[key]
    rows=[
        {"expected_pc":hex(v),"timeout":False,"registers":[f"PC={v:016x} SP=0000000040150000"]}
        for n,v in p.items() if n!="framebuffer"
    ]
    result={
        "firmware_sha256":module.HASHES[key],
        "stops":rows,
        "boot_callback_hits":[{"pc":hex(p["framebuffer"]),"cpu":0,"from":"qmp-info-registers"}],
        "lens_reply_evidence":[{"runtime_pc":hex(p["lens"]),"status_word":0,
                                "completion_byte":0,"reply_bytes":8}],
        "checks":[{"name":"lens status","passed":True},{"name":"no unmodeled MMIO","passed":True}],
        "error":None,
        "final_pipeline":{"raw-pipeline-state":{"frames":8},
                          "engine1548-scanout-state":{"frames":8}},
    }
    if key=="312":
        result["unqualified_c312_site_profile"]={
            "runtime_qualified":False,
            "site_hits":dict.fromkeys(("battery_callback","lens_controller_reply","framebuffer_event"),{})
        }
    return result


class Z8RuntimeEvidence(unittest.TestCase):
    def test_both_versions_have_complete_bounded_guest_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            for ver in ("311","312"):
                path=Path(tmp)/f"boot{ver}.json"
                path.write_text(json.dumps(sample(ver)))
                result=module.inspect_guest(path,ver)
                self.assertTrue(result["bounded_boot_evidence_passed"])
                self.assertFalse(result["still_photo_capture_qualified"])
                self.assertFalse(result["video_recording_qualified"])
                self.assertFalse(result["physical_lens_operation_qualified"])

    def test_missing_runtime_framebuffer_does_not_qualify(self):
        with tempfile.TemporaryDirectory() as tmp:
            row=sample("312")
            row["boot_callback_hits"]=[]
            path=Path(tmp)/"missing.json"
            path.write_text(json.dumps(row))
            self.assertFalse(module.inspect_guest(path,"312")["bounded_boot_evidence_passed"])

    def test_bad_lens_status_or_wrong_adc_pc_does_not_qualify(self):
        with tempfile.TemporaryDirectory() as tmp:
            row=sample("312")
            row["lens_reply_evidence"][0]["status_word"]=3
            row["stops"][0]["registers"]=["PC=0000000041181504"]
            path=Path(tmp)/"bad.json"
            path.write_text(json.dumps(row))
            result=module.inspect_guest(path,"312")
            self.assertEqual(result["adc_actual_hits"],0)
            self.assertEqual(result["lens_valid_reply_count"],0)
            self.assertFalse(result["bounded_boot_evidence_passed"])


if __name__=="__main__":
    unittest.main()
