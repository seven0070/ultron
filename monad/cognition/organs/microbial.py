"""
Microbial organs — 15 total (from user's canonical spec).
"""

from __future__ import annotations

from monad.cognition.organs.base import OrganCategory
from monad.cognition.organs.stub import make_stub


MICROBIAL: list[tuple[str, str, str, list[str], str]] = [
    ("Precision Editing", "S. pyogenes",
     "CRISPR-Cas9 surgical strategy editing",
     ["EditSite", "PrecisionCut"], "crispr_targeted_search"),
    ("Signal Amplification", "T. aquaticus",
     "Taq polymerase exponential amplification",
     ["AmplifiedSignal", "ExponentialChain"], "pcr_amplification_chain"),
    ("Extreme Resilience", "D. radiodurans",
     "Self-repair after shattering damage",
     ["ShatterEvent", "ReassemblyPath"], "fragment_reassembly"),
    ("Predatory Swarm Intelligence", "M. xanthus",
     "Coordinated pack hunting of inefficiencies",
     ["SwarmTarget", "CoordinatedAttack"], "swarm_coordinated_search"),
    ("Metabolic Flexibility", "E. coli",
     "Seamless regime switching in any condition",
     ["RegimeSwitch", "MetabolicPathway"], "adaptive_pathway_search"),
    ("Synthetic Construction", "M. mycoides",
     "Builds strategies from first principles",
     ["SyntheticModule", "FirstPrincipleComponent"], "synthetic_assembly_search"),
    ("Extremophile Adaptability", "S. acidocaldarius",
     "Operates in boiling acid; any environment",
     ["ExtremeCondition", "AdaptationMarker"], "extremophile_robust_search"),
    ("Self-Assembly", "Bacteriophage T4",
     "Autonomous construction from simple rules",
     ["AssemblyStep", "SelfOrganizingCluster"], "self_assembly_trace"),
    ("Eukaryotic Compartmentalization", "S. cerevisiae",
     "Prevents cross-contamination of strategies",
     ["CompartmentBoundary", "IsolationMembrane"], "compartment_isolated_search"),
    ("Horizontal Gene Transfer", "A. tumefaciens",
     "Imports external skills seamlessly",
     ["TransferEvent", "ImportedCapability"], "cross_boundary_learning"),
    ("Nucleation State Change", "P. syringae",
     "Triggers controlled phase transitions",
     ["NucleationPoint", "PhaseTransitionTrigger"], "nucleation_detection"),
    ("Cooperative Swarming", "P. vortex",
     "Fractal pattern recognition via distributed cooperation",
     ["FractalSwarm", "CooperativeTrail"], "vortex_fractal_search"),
    ("Minimal Multicellularity", "T. adhaerens",
     "Fundamental principles of cellular cooperation",
     ["CooperationBridge", "MulticellularUnit"], "cooperation_principle_search"),
    ("Network Optimization", "P. polycephalum",
     "Innate training-free optimal path finding",
     ["OptimalPath", "NetworkSolution"], "physarum_path_optimization"),
    ("Environmental Sensing", "A. thaliana",
     "Integrates multiple environmental cues",
     ["EnvironmentalCue", "IntegratedSignal"], "multi_cue_integration"),
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
