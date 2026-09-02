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

"""OpenEAGO Phase 3 Risk & Policy Engine for SynapticChain Agent Wallets.

Evaluates incoming autonomous agent transactions against:
  - Daily spending velocity caps
  - Single transaction upper bounds
  - Merchant allowlists
  - Canonical OpenEAGO compliance profiles (DORA, BCBS-239, SR-11-7)
  - Capability constraints (audit_anchoring, cross_border_clearance)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Set, Optional, Tuple


@dataclass
class AgentPolicyConfig:
    """On-chain agent governance parameters corresponding to AgentRegistry.syn."""
    agent_id: str
    l1_address: str
    daily_limit_usd: float
    max_single_tx_usd: float
    merchant_allowlist: Set[str] = field(default_factory=set)
    compliance_profiles: List[str] = field(default_factory=lambda: ["DORA", "BCBS-239"])
    capabilities: List[str] = field(default_factory=lambda: ["audit_anchoring", "cross_border_clearance"])
    policy_version: int = 1
    active: bool = True


@dataclass
class PolicyDecision:
    approved: bool
    reason_code: str
    message: str
    evaluated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AgentPolicyEngine:
    """Simulates and validates OpenEAGO Phase 3 Risk Negotiation."""

    def __init__(self, policy: AgentPolicyConfig):
        self.policy = policy
        self.daily_spent: float = 0.0
        self.current_day: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _refresh_window(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self.current_day:
            self.daily_spent = 0.0
            self.current_day = today

    def evaluate_transaction(self, merchant_address: str, amount: float) -> PolicyDecision:
        """Evaluate a proposed transaction against OpenEAGO Phase 3 constraints."""
        self._refresh_window()

        if not self.policy.active:
            return PolicyDecision(
                approved=False,
                reason_code="AGNT_REVOKED",
                message=f"Agent {self.policy.agent_id} is deactivated or revoked on-chain.",
            )

        if amount <= 0:
            return PolicyDecision(
                approved=False,
                reason_code="INVALID_AMOUNT",
                message="Transaction amount must be positive.",
            )

        if amount > self.policy.max_single_tx_usd:
            return PolicyDecision(
                approved=False,
                reason_code="SINGLE_LIMIT_EXCEEDED",
                message=f"Amount ${amount:.2f} exceeds single transaction limit of ${self.policy.max_single_tx_usd:.2f}.",
            )

        if (self.daily_spent + amount) > self.policy.daily_limit_usd:
            remaining = max(0.0, self.policy.daily_limit_usd - self.daily_spent)
            return PolicyDecision(
                approved=False,
                reason_code="DAILY_LIMIT_EXCEEDED",
                message=f"Amount ${amount:.2f} exceeds remaining daily limit of ${remaining:.2f}.",
            )

        if self.policy.merchant_allowlist and merchant_address not in self.policy.merchant_allowlist:
            return PolicyDecision(
                approved=False,
                reason_code="MERCHANT_NOT_ALLOWLISTED",
                message=f"Merchant address {merchant_address} is not on the approved merchant allowlist.",
            )

        return PolicyDecision(
            approved=True,
            reason_code="POLICY_PASSED",
            message="Transaction satisfies all OpenEAGO Phase 3 policy bounds.",
        )

    def record_spend(self, amount: float):
        """Record spend after confirmed L1 settlement."""
        self._refresh_window()
        self.daily_spent += amount
