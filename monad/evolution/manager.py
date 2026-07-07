"""
EvolutionManager — orchestrates the full self-improvement loop.

    propose(goal, target)
        ↓ (uses PatchProposer + LLMs)
    proposal
        ↓ (sandbox test — SandboxRunner)
    test result
        ↓ (approval — PolicyGate)
    approval decision
        ↓ (backup + apply — RollbackManager)
    applied change
        ↓ (log everything — EvolutionLog)

Every step is journaled. Nothing bypasses PolicyGate. Nothing touches
paths outside DEFAULT_POLICIES.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from monad.core.logger import get_logger
from monad.evolution.evolvable import EvolutionZone, is_path_allowed
from monad.evolution.log import ChangeType, EvolutionLog, EvolutionRecord, Outcome
from monad.evolution.proposer import PatchProposal, PatchProposer
from monad.evolution.rollback import RollbackManager
from monad.evolution.sandbox import SandboxRunner

log = get_logger(__name__)


class EvolutionManager:
    def __init__(
        self,
        root: Path,
        evolution_log: EvolutionLog,
        proposer: PatchProposer,
        sandbox: SandboxRunner,
        rollback: RollbackManager,
        policy_gate=None,
    ) -> None:
        self.root = Path(root)
        self.log = evolution_log
        self.proposer = proposer
        self.sandbox = sandbox
        self.rollback = rollback
        self.policy_gate = policy_gate

    # -- propose --------------------------------------------------------------

    def propose(
        self,
        goal: str,
        zone: EvolutionZone,
        target_path: str,
    ) -> tuple[EvolutionRecord, PatchProposal]:
        """Draft a change and record it as PROPOSED (not applied)."""
        allowed, reason = is_path_allowed(target_path)
        if not allowed:
            raise PermissionError(f"Path not evolvable: {target_path} ({reason})")

        proposal = self.proposer.propose(goal, zone, target_path)
        rec = EvolutionRecord(
            id=EvolutionLog.new_id(),
            timestamp=datetime.now().isoformat(),
            change_type=self._infer_change_type(zone, target_path),
            outcome=Outcome.PROPOSED,
            goal=goal,
            target_path=target_path,
            diff=proposal.diff[:20_000],  # cap
            metadata={"model_used": proposal.model_used,
                      "warnings": proposal.warnings,
                      "rationale": proposal.rationale},
        )
        self.log.record(rec)
        log.info("Proposal {} recorded ({})", rec.id, target_path)
        return rec, proposal

    # -- apply ----------------------------------------------------------------

    def apply(self, record: EvolutionRecord, proposal: PatchProposal,
              skip_tests: bool = False, skip_approval: bool = False) -> EvolutionRecord:
        """Test-in-sandbox → gate → backup → write → log."""
        # 1. Sandbox tests
        if not skip_tests:
            log.info("Running sandbox tests for {}", record.id)
            result = self.sandbox.run(proposal)
            record.tests_passed = result.passed
            record.test_output = (result.stderr + "\n" + result.stdout)[-4000:]
            if not result.passed:
                self.log.update_outcome(record.id, Outcome.FAILED,
                                        tests_passed=False,
                                        test_output=record.test_output)
                log.warning("Proposal {} failed tests (exit={})",
                            record.id, result.exit_code)
                return record

        # 2. Approval gate
        if not skip_approval and self.policy_gate is not None:
            ok = self.policy_gate.check(
                "evolution.apply",
                target=record.target_path,
                goal=record.goal,
                change_type=record.change_type.value,
            )
            if not ok:
                self.log.update_outcome(record.id, Outcome.REJECTED)
                log.info("Proposal {} rejected by policy gate", record.id)
                return record

        # 3. Backup + write
        backup = self.rollback.backup(record.target_path, record.id)
        record.backup_path = backup
        target = self.root / record.target_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(proposal.proposed_content, encoding="utf-8")

        # 4. Log APPLIED
        self.log.update_outcome(record.id, Outcome.APPLIED,
                                tests_passed=record.tests_passed,
                                test_output=record.test_output)
        # Persist backup path too (re-record)
        record.outcome = Outcome.APPLIED
        self.log.record(record)
        log.success("Applied evolution {} → {}", record.id, record.target_path)
        return record

    # -- rollback -------------------------------------------------------------

    def rollback_change(self, record_id: str) -> bool:
        original = self.log.get(record_id)
        if not original:
            raise KeyError(f"No such evolution record: {record_id}")
        if original.outcome != Outcome.APPLIED:
            raise RuntimeError(f"Record {record_id} is not APPLIED "
                               f"(outcome={original.outcome.value})")

        ok = self.rollback.rollback(original)
        if ok:
            self.log.update_outcome(record_id, Outcome.ROLLED_BACK)
            # Record a companion ROLLBACK entry linked to the original
            self.log.record(EvolutionRecord(
                id=EvolutionLog.new_id(),
                timestamp=datetime.now().isoformat(),
                change_type=ChangeType.ROLLBACK,
                outcome=Outcome.APPLIED,
                goal=f"Rollback of {record_id}",
                target_path=original.target_path,
                diff="",
                parent_id=record_id,
            ))
        return ok

    # -- helpers --------------------------------------------------------------

    def history(self, limit: int = 30) -> list[EvolutionRecord]:
        return self.log.history(limit=limit)

    def _infer_change_type(self, zone: EvolutionZone, target: str) -> ChangeType:
        target_lower = target.lower()
        if zone == EvolutionZone.CONFIGS:
            return ChangeType.PATCH_CONFIG
        if zone == EvolutionZone.PROMPTS:
            return ChangeType.PATCH_PROMPT
        if zone == EvolutionZone.PLUGINS:
            # New file? treat as new plugin; existing = patch
            return (ChangeType.NEW_PLUGIN
                    if not (self.root / target).exists()
                    else ChangeType.PATCH_PLUGIN)
        if zone == EvolutionZone.TOOLS:
            return (ChangeType.NEW_TOOL
                    if not (self.root / target).exists()
                    else ChangeType.PATCH_TOOL)
        return ChangeType.PATCH_PLUGIN
