"""
AIE212 — Medical Diagnosis Expert System
core/certainty_factor.py

Responsibility: MYCIN-style Certainty Factor (CF) calculus utilities.
All methods are static; this class is never instantiated.
"""


class CertaintyFactor:
    """
    Static utility class for MYCIN-style Certainty Factor operations.

    MYCIN CF combination formula (two independent rules for same hypothesis):
        CF_combined = CF1 + CF2 × (1 − CF1)

    Urgency levels and their numeric ranks (higher = more urgent):
        IMMEDIATE   → 4
        URGENT      → 3
        SEMI_URGENT → 2
        NON_URGENT  → 1
    """

    URGENCY_RANK: dict = {
        "IMMEDIATE":   4,
        "URGENT":      3,
        "SEMI_URGENT": 2,
        "NON_URGENT":  1,
    }

    @staticmethod
    def combine(cf1: float, cf2: float) -> float:
        """
        Combine two independent CFs using the MYCIN formula.

        Parameters
        ----------
        cf1 : float  — existing hypothesis CF
        cf2 : float  — new rule CF to combine

        Returns
        -------
        float — combined CF, rounded to 4 decimal places
        """
        return round(cf1 + cf2 * (1.0 - cf1), 4)

    @staticmethod
    def label(cf: float) -> str:
        """
        Map a numeric CF value to a human-readable confidence label.

        Thresholds
        ----------
        ≥ 0.85  → 'Very High'
        ≥ 0.70  → 'High'
        ≥ 0.50  → 'Medium'
        < 0.50  → 'Low'
        """
        if cf >= 0.85:
            return "Very High"
        if cf >= 0.70:
            return "High"
        if cf >= 0.50:
            return "Medium"
        return "Low"

    @staticmethod
    def urgency_rank(urgency: str) -> int:
        """
        Return the numeric rank of an urgency string.
        Higher value means more urgent. Returns 0 for unknown levels.
        """
        return CertaintyFactor.URGENCY_RANK.get(urgency, 0)
