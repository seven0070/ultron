"""
Fusion — make multiple LLMs produce ONE unified answer.

Three real levels of fusion (from lightest to deepest):

  L2  FusionChain    Sequential refinement. Draft → refine → polish across N
                     models. Works with any models, any tokenizers.
                     User sees a single answer that has been shaped by all.

  L3  FusionEnsembleTokens
                     Streamed token-level majority voting when models share
                     a tokenizer. Every K tokens, models "vote" and the group
                     continues from the winning sequence.

  L4  FusionLogits   Deepest achievable fusion on consumer hardware. At each
                     generation step, we take a weighted average of the raw
                     logit distributions from all models, then sample once.
                     Feels like a single model. Requires same tokenizer OR
                     the alignment adapter.

Above L4 (weight-level model merging) is IMPOSSIBLE across architecture families
(Qwen ≠ DeepSeek ≠ Llama). We don't pretend otherwise.

Public API:
    FusionOrchestrator          top-level entry
    FusionChain                 L2 strategy
    FusionEnsembleTokens        L3 strategy
    FusionLogits                L4 strategy
    TokenizerAligner            detects compatibility
    FusionResult                unified result type
"""

from monad.orchestration.fusion.aligner import TokenizerAligner, TokenizerCompatibility
from monad.orchestration.fusion.chain import FusionChain, ChainStage
from monad.orchestration.fusion.ensemble_tokens import FusionEnsembleTokens
from monad.orchestration.fusion.logits import FusionLogits
from monad.orchestration.fusion.orchestrator import FusionOrchestrator, FusionResult, FusionMode

__all__ = [
    "FusionOrchestrator", "FusionResult", "FusionMode",
    "FusionChain", "ChainStage",
    "FusionEnsembleTokens",
    "FusionLogits",
    "TokenizerAligner", "TokenizerCompatibility",
]
