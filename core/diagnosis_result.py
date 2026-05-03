"""
AIE212 — Medical Diagnosis Expert System
core/diagnosis_result.py

Responsibility: Immutable result data-class representing one ranked
diagnostic hypothesis. Produced by WorkingMemory.get_ranked_results().
"""

from dataclasses import dataclass, field


@dataclass
class DiagnosisResult:
    """
    Immutable result object for a single diagnostic hypothesis.

    Attributes
    ----------
    diagnosis   : str   — internal diagnosis identifier (underscore-separated)
    cf          : float — combined Certainty Factor (0.0 – 1.0)
    confidence  : str   — human-readable label: 'Low'|'Medium'|'High'|'Very High'
    urgency     : str   — triage level: 'NON_URGENT'|'SEMI_URGENT'|'URGENT'|'IMMEDIATE'
    rules_fired : list  — list of rule IDs that contributed to this hypothesis

    Properties
    ----------
    display_name : str — diagnosis name with underscores replaced by spaces
    """

    diagnosis  : str
    cf         : float
    confidence : str
    urgency    : str
    rules_fired: list = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """Return a human-readable name (underscores replaced with spaces)."""
        return self.diagnosis.replace("_", " ")
