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

from sdk.agent_policy import AgentPolicyConfig, AgentPolicyEngine


class TestAgentPolicy(unittest.TestCase):
    def setUp(self):
        self.config = AgentPolicyConfig(
            agent_id="spiffe://finos.org/agent/unit-test",
            l1_address="syn1qtestagent0000000000000000000000000000",
            daily_limit_usd=5000.0,
            max_single_tx_usd=1000.0,
            merchant_allowlist={"syn1qmerchant001", "syn1qmerchant002"},
            compliance_profiles=["DORA", "BCBS-239"],
            capabilities=["audit_anchoring", "cross_border_clearance"],
        )
        self.engine = AgentPolicyEngine(self.config)

    def test_compliant_transaction(self):
        decision = self.engine.evaluate_transaction("syn1qmerchant001", 500.0)
        self.assertTrue(decision.approved)
        self.assertEqual(decision.reason_code, "POLICY_PASSED")

    def test_single_limit_exceeded(self):
        decision = self.engine.evaluate_transaction("syn1qmerchant001", 1500.0)
        self.assertFalse(decision.approved)
        self.assertEqual(decision.reason_code, "SINGLE_LIMIT_EXCEEDED")

    def test_daily_limit_exceeded(self):
        self.engine.record_spend(4500.0)
        decision = self.engine.evaluate_transaction("syn1qmerchant001", 600.0)
        self.assertFalse(decision.approved)
        self.assertEqual(decision.reason_code, "DAILY_LIMIT_EXCEEDED")

    def test_merchant_not_allowlisted(self):
        decision = self.engine.evaluate_transaction("syn1qunauthorized", 100.0)
        self.assertFalse(decision.approved)
        self.assertEqual(decision.reason_code, "MERCHANT_NOT_ALLOWLISTED")

    def test_deactivated_agent(self):
        self.config.active = False
        decision = self.engine.evaluate_transaction("syn1qmerchant001", 100.0)
        self.assertFalse(decision.approved)
        self.assertEqual(decision.reason_code, "AGNT_REVOKED")


if __name__ == "__main__":
    unittest.main()
