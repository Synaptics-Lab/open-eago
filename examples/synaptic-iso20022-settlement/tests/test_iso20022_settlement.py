# Copyright 2026 Synaptics-Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sdk.iso20022_messages import Pacs008Message, ClearingStatus
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sdk.synaptic_client import SynapticL1Client


class TestISO20022Settlement(unittest.TestCase):
    def setUp(self):
        self.client = SynapticL1Client()
        self.msg = Pacs008Message.create(
            debtor_agent="spiffe://finos.org/citi/treasury-01",
            debtor_account="syn1qagent11111111111111111111111111111",
            creditor_agent="Cloud Services LLC",
            creditor_account="syn1qcloud22222222222222222222222222222",
            amount=750.0,
            currency="USD",
        )

    def test_pacs008_hashing_and_xml(self):
        msg_hash = self.msg.payload_hash()
        self.assertEqual(len(msg_hash), 64)
        xml = self.msg.to_xml()
        self.assertIn("<FIToFICstmrCdtTrf>", xml)
        self.assertIn(self.msg.message_id, xml)
        self.assertIn("750.00", xml)

    def test_successful_settlement(self):
        res = self.client.submit_settlement(self.msg, policy_approved=True, policy_reason="Approved")
        self.assertEqual(res.receipt.status, ClearingStatus.ACCP)
        self.assertEqual(res.receipt.reason_code, "ACTC")
        self.assertTrue(res.receipt.l1_tx_hash.startswith("0x"))
        self.assertGreaterEqual(res.receipt.l1_lane_index, 0)
        self.assertLess(res.receipt.l1_lane_index, 2048)
        self.assertIn("<FIToFIPmtStsRpt>", res.receipt.to_xml())

    def test_rejected_settlement_audit_anchor(self):
        res = self.client.submit_settlement(self.msg, policy_approved=False, policy_reason="Cap Exceeded")
        self.assertEqual(res.receipt.status, ClearingStatus.RJCT)
        self.assertEqual(res.receipt.reason_code, "NARR")
        self.assertTrue(len(res.receipt.l1_state_root) == 64)


if __name__ == "__main__":
    unittest.main()
