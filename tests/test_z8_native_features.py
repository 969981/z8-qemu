# SPDX-License-Identifier: GPL-2.0-or-later
"""Native EX diagnostics must not be confused with saved-photo/movie validation."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"research/3.12/ci/summarize_native_features.py"
spec=importlib.util.spec_from_file_location("z8_native_features", SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sample():
    def row(vt, frames, ui):
        return {"runtime-clock-state":{"virtual_ns":int(vt*1_000_000_000)},
                "raw-pipeline-state":{"frames":frames},
                "engine1548-scanout-state":{"frames":frames},
                "ui_control_hex":(b'\x01\x00\x00\x00'+ui.to_bytes(4,'little')).hex()}
    return {
        "native_mcu":True, "host_mcu_messages":False, "error":None,
        "delivered_contacts":[
            {"property":"mcu-pins","value":"G1=0"},
            {"property":"mcu-pins","value":"G1=1"},
            {"property":"mcu-contacts","value":"23.10=0"},
            {"property":"mcu-contacts","value":"23.10=1"},
        ],
        "native_samples":[row(10,10,6),row(22,25,2),row(39,40,6)],
        "checks":[{"name":"native run has no unmodeled MMIO","passed":True}],
        "final_native_mcu":{"frames":80,"bad_frames":0},
        "native_model_state":{"engine1543-control-state":{"movie_frames":20}},
    }


class IndependentNativeFeatures(unittest.TestCase):
    def test_reports_bounded_original_ex_recovery_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"native.json"
            p.write_text(json.dumps(sample()))
            data=module.summarize(p,0)
            self.assertTrue(data["original_ex_mcu_communication_qualified"])
            self.assertTrue(data["mode_recovery_qualified"])
            self.assertFalse(data["still_nef_file_qualified"])
            self.assertFalse(data["encoded_movie_file_qualified"])
            self.assertFalse(data["physical_lens_af_qualified"])

    def test_no_guest_evidence_cannot_qualify(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"native.json"
            x=sample()
            x["native_samples"]=[]
            x["checks"]=[]
            p.write_text(json.dumps(x))
            self.assertFalse(module.summarize(p,0)["mode_recovery_qualified"])
            self.assertFalse(module.summarize(p,0)["original_ex_mcu_communication_qualified"])

    def test_exit_failure_is_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"native.json"
            p.write_text(json.dumps(sample()))
            self.assertFalse(module.summarize(p,1)["mode_recovery_qualified"])


if __name__=="__main__":
    unittest.main()
