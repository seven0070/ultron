"""
Microbial Life organs — 15 total.

Inspired by microbial strategies: parallelism, redundancy, symbiosis, and
adaptation without nervous systems.
"""

from __future__ import annotations

from monad.cognition.organs.base import OrganCategory
from monad.cognition.organs.stub import make_stub


MICROBIAL: list[tuple[str, str, str, list[str], str]] = [
    ("shortest_path_finder", "Slime_mold",
     "Physarum-style: finds efficient paths through resource networks.",
     ["Node","Edge","Path"], "graph_only"),
    ("population_selector", "Bacterial_colony",
     "Massive-parallel candidate generation + selection pressure.",
     ["Candidate"], "vector_only"),
    ("quorum_sensor", "Vibrio",
     "Trigger action only above population/consensus threshold.",
     ["Signal","Threshold"], "hybrid"),
    ("horizontal_gene_transfer", "Plasmid_exchange",
     "Adopts useful subroutines from other agents on the fly.",
     ["Skill","Transfer"], "graph_only"),
    ("extremophile", "Deinococcus",
     "Robust reasoning under corrupted or adversarial input.",
     ["Corruption","Recovery"], "hybrid"),
    ("biofilm_persistence", "Streptococcus_biofilm",
     "Persistent state via redundant substrate.",
     ["State","Redundancy"], "graph_only"),
    ("chemotactic_gradient", "Ecoli_chemotaxis",
     "Follows gradients — improves-worsens signal instead of goal search.",
     ["Gradient"], "vector_only"),
    ("sporulation", "Bacillus_spore",
     "Suspend computation cheaply, resume on trigger.",
     ["State","Trigger"], "graph_only"),
    ("photosynthetic", "Cyanobacterium",
     "Extract energy/utility from ambient signal.",
     ["Signal","Energy"], "vector_only"),
    ("symbiotic_partner", "Mitochondrion",
     "Deeply integrated cooperation with another agent as a subsystem.",
     ["Partner","Contract"], "graph_only"),
    ("nitrogen_fixer", "Rhizobium",
     "Converts abundant-but-inert input into useful form.",
     ["Input","Conversion"], "hybrid"),
    ("methanogen", "Archaea_methanogen",
     "Anaerobic reasoning — works in low-signal environments.",
     ["Sparse","Trace"], "vector_only"),
    ("viral_injector", "Bacteriophage",
     "Injects hypothesis into another module and hijacks output.",
     ["Hypothesis","Payload"], "graph_only"),
    ("lichenoid_composite", "Lichen",
     "Composite organism of otherwise-unrelated organs.",
     ["Composite"], "hybrid"),
    ("crispr_memoirist", "CRISPR_bacterium",
     "Immunological memory — remembers past attacks/errors precisely.",
     ["Error","Signature"], "graph_only"),
]

assert len(MICROBIAL) == 15, f"expected 15 microbial organs, got {len(MICROBIAL)}"


def build_microbial_organs() -> list:
    return [
        make_stub(
            name=name,
            inspiration=inspiration,
            category=OrganCategory.MICROBIAL,
            description=description,
            node_types=node_types,
            search_strategy=search_strategy,
        )
        for (name, inspiration, description, node_types, search_strategy) in MICROBIAL
    ]
