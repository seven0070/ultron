"""
Human Genius organs — 58 total.

⚠️ PLACEHOLDER ROSTER. The user's prompt referenced a specific 58-genius list
but did not paste it. Below are 58 broadly-influential thinkers spanning
science, math, philosophy, art, engineering, and social thought. Replace with
the user's actual roster when it arrives — the API stays identical.

Each entry mirrors the pattern:
    (organ_name, inspiration, description, node_types, search_strategy)
"""

from __future__ import annotations

from monad.cognition.organs.base import OrganCategory
from monad.cognition.organs.stub import make_stub


HUMAN_GENIUSES: list[tuple[str, str, str, list[str], str]] = [
    # Physics & cosmology
    ("thought_experimentalist", "Einstein",  "Runs gedankenexperiments on unfamiliar problems.",  ["Concept","Analogy"], "graph_only"),
    ("mechanics_and_motion",    "Newton",    "Classical mechanistic causal reasoning.",           ["CausalLink"], "graph_only"),
    ("field_theorist",          "Faraday",   "Reasons about invisible fields and influences.",    ["Field","Influence"], "hybrid"),
    ("wave_electromagneticist", "Maxwell",   "Unifies apparently-distinct phenomena into equations.", ["Unification"], "graph_only"),
    ("quantum_intuitionist",    "Feynman",   "Path-integral style: consider all possibilities at once.", ["Path","Possibility"], "hybrid"),
    ("uncertainty_reasoner",    "Heisenberg","Reasons under fundamental uncertainty.",             ["Probability"], "vector_only"),
    ("relativist",              "Poincaré",  "Frame-of-reference and topology reasoning.",         ["Frame","Topology"], "graph_only"),
    ("cosmologist",             "Hubble",    "Scale-invariant, large-scale reasoning.",            ["Scale"], "temporal"),

    # Math & logic
    ("proof_architect",         "Euclid",    "Axiomatic deductive reasoning.",                     ["Axiom","Theorem"], "graph_only"),
    ("infinity_reasoner",       "Cantor",    "Handles infinite sets and hierarchies.",             ["Cardinality"], "graph_only"),
    ("incompleteness_checker",  "Gödel",     "Detects self-reference and undecidability.",         ["MetaClaim"], "graph_only"),
    ("computation_theorist",    "Turing",    "Reasons in terms of computable procedures.",         ["Procedure"], "graph_only"),
    ("universal_analyst",       "Euler",     "Finds elegant closed-form patterns.",                ["Pattern"], "graph_only"),
    ("category_theorist",       "Grothendieck","Reasons in terms of structural morphisms.",        ["Morphism"], "graph_only"),
    ("statistics_reasoner",     "Fisher",    "Rigorous inference under uncertainty.",              ["Estimate"], "vector_only"),
    ("bayesian_updater",        "Laplace",   "Updates beliefs via prior + evidence.",              ["Belief","Evidence"], "hybrid"),

    # Chemistry & biology
    ("chemical_intuitionist",   "Curie",     "Reasons about materials and transformations.",       ["Material","Reaction"], "hybrid"),
    ("evolutionist",            "Darwin",    "Reasons via variation + selection.",                 ["Trait","Selection"], "temporal"),
    ("genetic_reasoner",        "Mendel",    "Discrete inheritance and lineage reasoning.",        ["Trait","Lineage"], "graph_only"),
    ("molecular_biologist",     "Watson-Crick","Structure-function reasoning.",                    ["Structure","Function"], "graph_only"),
    ("ecosystem_thinker",       "Carson",    "Reasons about interconnected consequences.",         ["Impact","Cascade"], "graph_only"),
    ("neuroscientist",          "Cajal",     "Network and connectivity reasoning.",                ["Network","Connection"], "hybrid"),

    # Engineering & invention
    ("polymath_synthesizer",    "da_Vinci",  "Cross-domain analogical reasoning.",                 ["Analogy"], "hybrid"),
    ("systems_engineer",        "Tesla",     "Whole-system electrical reasoning.",                 ["System"], "hybrid"),
    ("iterative_inventor",      "Edison",    "Fast trial-and-error at scale.",                     ["Experiment"], "vector_only"),
    ("aerospace_thinker",       "von_Braun", "Trajectory and staged-plan reasoning.",              ["Plan","Stage"], "temporal"),
    ("computer_architect",      "von_Neumann","Reasons about computation architecture.",           ["Architecture"], "graph_only"),
    ("info_theorist",           "Shannon",   "Reasons in terms of information and entropy.",       ["Message","Channel"], "vector_only"),
    ("interface_designer",      "Engelbart", "Human-computer symbiosis reasoning.",                ["Interface"], "hybrid"),
    ("systems_thinker",         "Wiener",    "Feedback and cybernetic reasoning.",                 ["Feedback"], "graph_only"),

    # Philosophy & epistemology
    ("first_principles",        "Aristotle", "Ground everything in first principles.",             ["Principle"], "graph_only"),
    ("dialectician",            "Socrates",  "Reasons by systematic questioning.",                 ["Question"], "graph_only"),
    ("skeptic",                 "Descartes", "Doubts systematically to find bedrock.",             ["Doubt"], "graph_only"),
    ("empiricist",              "Hume",      "Insists on observational grounding.",                ["Observation"], "vector_only"),
    ("transcendentalist",       "Kant",      "Distinguishes structure of experience from world.",  ["Category"], "graph_only"),
    ("phenomenologist",         "Husserl",   "First-person structure of experience.",              ["Experience"], "vector_only"),
    ("pragmatist",              "James",     "Truth = what works, iteratively.",                   ["Utility"], "hybrid"),
    ("falsificationist",        "Popper",    "Tries to falsify hypotheses, not confirm.",          ["Falsifier"], "graph_only"),
    ("paradigm_shifter",        "Kuhn",      "Detects paradigm changes and anomalies.",            ["Anomaly"], "graph_only"),

    # Social sciences & economics
    ("economist_marginalist",   "Smith",     "Reasons about incentives and equilibria.",           ["Incentive"], "graph_only"),
    ("systems_political",       "Marx",      "Reasons about power and material conditions.",       ["PowerRelation"], "graph_only"),
    ("moral_reasoner",          "Rawls",     "Reasons behind a veil of ignorance for fairness.",   ["Fairness"], "graph_only"),
    ("behavioral_economist",    "Kahneman",  "System-1/System-2 dual-process reasoning.",          ["Bias"], "hybrid"),
    ("historian",               "Thucydides","Cause-and-consequence in human affairs.",            ["Event","Cause"], "temporal"),

    # Language & narrative
    ("linguistic_deep",         "Chomsky",   "Deep-structure linguistic reasoning.",               ["DeepStructure"], "graph_only"),
    ("narrative_engineer",      "Shakespeare","Character, motive, dramatic structure.",            ["Character","Motive"], "graph_only"),
    ("rhetorician",             "Cicero",    "Persuasive structure and audience adaptation.",      ["Argument","Audience"], "hybrid"),
    ("mythologist",             "Campbell",  "Detects archetypal patterns across stories.",        ["Archetype"], "graph_only"),

    # Art, music, design
    ("visual_composer",         "Michelangelo","Spatial composition and form.",                    ["Form","Composition"], "vector_only"),
    ("musical_structurer",      "Bach",      "Contrapuntal and hierarchical structure.",           ["Voice","Structure"], "graph_only"),
    ("harmonic_intuitionist",   "Mozart",    "Rapid generation with elegant constraints.",         ["Motif"], "hybrid"),
    ("abstract_expressionist",  "Picasso",   "Deliberate multi-perspective decomposition.",        ["Perspective"], "hybrid"),
    ("designer",                "Ive",       "Reasons about form-follows-function purity.",        ["Design"], "hybrid"),

    # Contemplation & interior life
    ("compassion_reasoner",     "Gandhi",    "Non-violent problem framing.",                       ["Value"], "graph_only"),
    ("dignity_reasoner",        "MLK",       "Justice-oriented framing.",                          ["Justice"], "graph_only"),
    ("mindful_observer",        "Buddha",    "Present-moment observation of process.",             ["Process"], "vector_only"),
    ("wisdom_traditionalist",   "Confucius", "Role, duty, and long-term relational reasoning.",    ["Role","Duty"], "graph_only"),
    ("existentialist",          "Sartre",    "Radical responsibility and choice reasoning.",       ["Choice"], "graph_only"),
]

assert len(HUMAN_GENIUSES) == 58, f"expected 58 human geniuses, got {len(HUMAN_GENIUSES)}"


def build_human_genius_organs() -> list:
    return [
        make_stub(
            name=name,
            inspiration=inspiration,
            category=OrganCategory.HUMAN_GENIUS,
            description=description,
            node_types=node_types,
            search_strategy=search_strategy,
        )
        for (name, inspiration, description, node_types, search_strategy) in HUMAN_GENIUSES
    ]
