# SPDX-License-Identifier: GPL-2.0-or-later
"""Guest NEF catalog attempts must never be mistaken for RAW pixel verification."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"research/3.12/ci/summarize_still_capture.py"
spec=importlib.util.spec_from_file_location("z8_still_evidence",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Z8StillCaptureEvidence(unittest.TestCase):
    def test_missing_card_is_unqualified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            receipt=root/"result.json"
            receipt.write_text(json.dumps({"error":None,"checks":[{"passed":True}]}))
            data=module.summarize(receipt,root/"nonexistent-card.raw",0)
            self.assertFalse(data["guest_created_nef"])
            self.assertFalse(data["photo_capture_end_to_end_qualified"])
            self.assertFalse(data["raw_pixels_independently_decoded"])

    def test_bad_card_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            receipt=root/"result.json"
            receipt.write_text(json.dumps({"error":None}))
            card=root/"card.raw"; card.write_bytes(b"not a card")
            data=module.summarize(receipt,card,0)
            self.assertFalse(data["exfat_catalog_valid"])
            self.assertFalse(data["guest_created_nef"])

    def test_no_receipt_is_not_clean_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            data=module.summarize(root/"missing.json",root/"missing.raw",1)
            self.assertFalse(data["guest_receipt_exists"])
            self.assertFalse(data["guest_still_write_observed"])


if __name__=="__main__":
    unittest.main()
