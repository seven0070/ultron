"""
Monad — the top-level cognitive orchestrator.

Wires the 9-layer architecture together and exposes a single `.think(prompt)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from monad.cognition.executive import ExecutiveController, ExecutiveDecision
from monad.cognition.memory import MemoryLayer, QueryRouter
from monad.cognition.mcp import MCPBridge
from monad.cognition.organs import OrganRegistry, register_all
from monad.cognition.organs.base import OrganResult
from monad.cognition.perception import PerceptionLayer
from monad.cognition.reasoning import ModelRouter, ReflexionEngine
from monad.cognition.self_model import SelfModel


@dataclass
class MonadConfig:
    strategy: str = "weighted_vote"            # or "highest_confidence"
    enabled_organs: list[str] = field(default_factory=list)     # empty = all enabled
    max_organs_per_cycle: int = 8               # keep latency sane
    memory_backend: str = "auto"                # auto | cognee | inmem
    reflexion_threshold: float = 0.3
    register_all_as_mcp_tools: bool = False     # export all 83 as MCP


@dataclass
class ThoughtCycle:
    prompt: str
    query_mode: str = ""
    activated_organs: list[str] = field(default_factory=list)
    organ_results: list[dict] = field(default_factory=list)
    decision: dict | None = None
    memory_hits: list[dict] = field(default_factory=list)
    routing: dict | None = None
    output: str = ""


class Monad:
    """The cognitive OS. One .think() drives the full 9-layer pass."""

    def __init__(self, config: MonadConfig | None = None) -> None:
        self.config = config or MonadConfig()

        # Layers
        self.perception = PerceptionLayer()                                       # 1
        self.memory = MemoryLayer(backend=self.config.memory_backend)             # 2
        self.query_router = QueryRouter()
        self.reflexion = ReflexionEngine(memory=self.memory)                      # 4 (reasoning)
        self.model_router = ModelRouter()
        self.executive = ExecutiveController(                                     # 5
            strategy=self.config.strategy,
            reflexion_threshold=self.config.reflexion_threshold,
            model_router=self.model_router,
            reflexion_engine=self.reflexion,
        )
        self.organs: OrganRegistry = register_all()                               # 6
        self.self_model = SelfModel().build()                                     # 7
        self.mcp = MCPBridge()                                                    # (MCP layer)

        # Apply enabled_organs filter
        if self.config.enabled_organs:
            active = set(self.config.enabled_organs)
            for organ in self.organs.all():
                organ.enabled = organ.name in active

        # Optionally export all organs as MCP tools
        if self.config.register_all_as_mcp_tools:
            for organ in self.organs.enabled_only():
                self.mcp.register_organ_as_tool(organ)

    # -- public API -----------------------------------------------------------

    def think(self, input_data) -> ThoughtCycle:
        """Run the full cognitive pipeline once."""
        cycle = ThoughtCycle(prompt="")

        # Layer 1: Perception
        percept = self.perception.perceive(input_data)
        cycle.prompt = percept.text

        # Layer 2: Memory recall (via QueryRouter)
        mode = self.query_router.route(percept.text)
        cycle.query_mode = mode.value
        cycle.memory_hits = self.memory.recall(percept.text, mode=mode.value, top_k=5)

        # Layer 4: Model routing decision
        routing = self.model_router.route(percept.text)
        cycle.routing = {"tier": routing.tier.value, "model_id": routing.model_id,
                         "reason": routing.reason}

        # Layer 6: Organ activation (bounded)
        active = self._select_organs(percept.text)
        organ_results: list[OrganResult] = []
        context = {"memory_hits": cycle.memory_hits, "routing": cycle.routing}
        for organ in active:
            try:
                r = organ.process(percept.text, context=context)
            except Exception as e:
                r = OrganResult(organ_name=organ.name, output=f"[error: {e}]",
                                confidence=0.0, reasoning=str(e))
            organ_results.append(r)
        cycle.activated_organs = [o.name for o in active]
        cycle.organ_results = [
            {"organ": r.organ_name, "confidence": r.confidence,
             "reasoning": r.reasoning, "output": str(r.output)[:200]}
            for r in organ_results
        ]

        # Layer 5: Executive decision (+ optional reflexion inside)
        decision: ExecutiveDecision = self.executive.decide(organ_results, prompt=percept.text)
        cycle.decision = {
            "strategy": decision.strategy,
            "winning_organs": decision.winning_organs,
            "confidence": decision.confidence,
            "reflexion_triggered": decision.reflexion_triggered,
            "conflicts": decision.conflicts,
        }

        # Layer 7: Self-model recording
        cyc_idx = self.self_model.record_cycle(percept.text, cycle.decision)
        for r in organ_results:
            self.self_model.record_activation(r.organ_name,
                                              {"confidence": r.confidence,
                                               "output": str(r.output)[:120]},
                                              cycle_idx=cyc_idx)
        for c in decision.conflicts:
            self.self_model.add_conflict(str(c), c.get("organs", []),
                                         decision.final_output)

        # Layer 9: Action (currently just return the text)
        cycle.output = decision.final_output
        return cycle

    # -- helpers --------------------------------------------------------------

    def _select_organs(self, prompt: str) -> list:
        """Pick which organs to consult on this cycle.

        Placeholder policy: rotate through all enabled organs up to max_organs_per_cycle.
        Future: heuristic / learned organ selection per intent.
        """
        enabled = self.organs.enabled_only()
        return enabled[: self.config.max_organs_per_cycle]

    # -- diagnostics ----------------------------------------------------------

    def info(self) -> dict:
        return {
            "version": "0.2.0",
            "organs": self.organs.counts(),
            "memory": self.memory.size(),
            "self_model": self.self_model.stats(),
            "mcp_tools": len(self.mcp.list_tools()),
            "config": {
                "strategy": self.config.strategy,
                "max_organs_per_cycle": self.config.max_organs_per_cycle,
                "memory_backend": self.memory.backend,
            },
        }
