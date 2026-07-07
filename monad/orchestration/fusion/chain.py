"""
FusionChain — L2 fusion via sequential refinement.

Each model in the chain plays a specific role:
    DRAFT    (reasoning model)  — produces first attempt
    REFINE   (coding model)     — critiques + rewrites for precision
    POLISH   (creative model)   — improves clarity, style, structure

The output the user sees is ONE final answer, but it has been shaped by
every model. Works with any model combo, any tokenizers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from monad.core.logger import get_logger

log = get_logger(__name__)


class ChainStage(str, Enum):
    DRAFT = "draft"
    REFINE = "refine"
    POLISH = "polish"


@dataclass
class ChainStep:
    stage: ChainStage
    model_id: str
    input_text: str
    output_text: str
    latency_ms: float = 0.0


@dataclass
class ChainRun:
    steps: list[ChainStep] = field(default_factory=list)
    final: str = ""

    @property
    def models_used(self) -> list[str]:
        return [s.model_id for s in self.steps]


class FusionChain:
    """Sequential draft → refine → polish across N models."""

    # Default prompts per stage (kept short — model does the work)
    STAGE_PROMPTS: dict[ChainStage, str] = {
        ChainStage.DRAFT: (
            "You are the DRAFTER. Answer the user's question thoughtfully. "
            "Be complete but not exhaustive. Write in your own voice.\n\n"
            "USER QUESTION:\n{prompt}\n\nDRAFT ANSWER:"
        ),
        ChainStage.REFINE: (
            "You are the REFINER. A colleague drafted the answer below. "
            "Rewrite it to be more precise, correct any errors, tighten "
            "reasoning, and remove filler. Preserve the intent. "
            "Output ONLY the revised answer.\n\n"
            "USER QUESTION:\n{prompt}\n\n"
            "DRAFT ANSWER:\n{previous}\n\nREFINED ANSWER:"
        ),
        ChainStage.POLISH: (
            "You are the POLISHER. Read the answer below and produce the "
            "FINAL version the user will see. Improve clarity, structure, "
            "and readability. Keep all factual content. Do not add commentary "
            "or mention this process. Output ONLY the final answer.\n\n"
            "USER QUESTION:\n{prompt}\n\n"
            "ANSWER SO FAR:\n{previous}\n\nFINAL ANSWER:"
        ),
    }

    def __init__(self, executor, stage_models: dict[ChainStage, str],
                 stage_prompts: dict[ChainStage, str] | None = None) -> None:
        """
        executor: ParallelExecutor (we use its .run_one method)
        stage_models: {DRAFT: 'longcat2', REFINE: 'glm5', POLISH: 'llama2'}
        """
        self.executor = executor
        self.stage_models = stage_models
        self.stage_prompts = {**self.STAGE_PROMPTS, **(stage_prompts or {})}

    def run(self, prompt: str, max_tokens: int = 1024,
            temperature_by_stage: dict[ChainStage, float] | None = None) -> ChainRun:
        """Run the full chain and return the final unified answer."""
        temps = {
            ChainStage.DRAFT: 0.7,
            ChainStage.REFINE: 0.35,
            ChainStage.POLISH: 0.55,
            **(temperature_by_stage or {}),
        }

        run = ChainRun()
        previous = ""

        for stage in (ChainStage.DRAFT, ChainStage.REFINE, ChainStage.POLISH):
            model_id = self.stage_models.get(stage)
            if not model_id:
                log.debug("FusionChain: skipping {} (no model assigned)", stage.value)
                continue

            template = self.stage_prompts[stage]
            stage_prompt = template.format(prompt=prompt, previous=previous)

            result = self.executor.run_one(
                model_id, stage_prompt,
                max_tokens=max_tokens,
                temperature=temps[stage], top_p=0.9,
            )
            output = result.text if result.ok else previous or "[all stages failed]"
            step = ChainStep(
                stage=stage, model_id=model_id,
                input_text=stage_prompt, output_text=output,
                latency_ms=result.latency_ms,
            )
            run.steps.append(step)
            log.debug("FusionChain: {} via {} → {} chars",
                      stage.value, model_id, len(output))
            previous = output

        run.final = previous
        return run
