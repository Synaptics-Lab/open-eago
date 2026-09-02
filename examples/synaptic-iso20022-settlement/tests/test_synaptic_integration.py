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

from sdk.synaptic_client import SynapticL1Client
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sdk.iso20022_messages import Pacs008Message


class TestSynapticIntegration(unittest.TestCase):
    def test_2048_lane_distribution(self):
        client = SynapticL1Client()
        lanes = set()
        for i in range(100):
            msg = Pacs008Message.create(
                debtor_agent=f"agent-{i}",
                debtor_account=f"syn1qaccount{i:04d}",
                creditor_agent="vendor",
                creditor_account="syn1qvendor",
                amount=10.0 + i,
            )
            lane = client._calculate_lane(msg.debtor_account, msg.payload_hash())
            self.assertTrue(0 <= lane < 2048)
            lanes.add(lane)
        # 100 random messages should map to many distinct lanes
        self.assertGreater(len(lanes), 70)


if __name__ == "__main__":
    unittest.main()
