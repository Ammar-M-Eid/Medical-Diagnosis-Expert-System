"""
AIE212 — Medical Diagnosis Expert System
core/working_memory.py

Responsibility: Session-scoped, volatile store for all facts derived
during one patient assessment.

Manages
-------
- Diagnostic hypotheses (keyed by diagnosis name)
- Red-flag alerts
- Ordered inference trace (for ExplanationModule)
- MYCIN CF combination on repeated hypothesis assertion
- Urgency promotion (urgency is only ever raised, never lowered)
"""

from core.certainty_factor import CertaintyFactor
from core.diagnosis_result import DiagnosisResult


class WorkingMemory:
    """
    Session-scoped, volatile store for all facts derived during one
    patient assessment.

    Usage
    -----
    Instantiate once per patient session.  The KnowledgeBase holds a
    reference and calls assert_hypothesis / boost_hypothesis / add_red_flag
    as rules fire. After the engine run, call get_ranked_results() to obtain
    sorted DiagnosisResult objects.
    """

    def __init__(self):
        self._hypotheses: dict = {}   # diagnosis_name -> {cf, urgency, rules}
        self._red_flags:  list = []
        self._trace:      list = []

    # ── Hypothesis management ──────────────────────────────────────────────

    def assert_hypothesis(
        self,
        diagnosis    : str,
        cf           : float,
        urgency      : str,
        rule_id      : str,
        description  : str,
        facts_matched: list,
    ) -> None:
        """
        Insert or update a diagnostic hypothesis.

        If the diagnosis already exists:
          - Combine CFs using the MYCIN formula.
          - Promote urgency if the new rule assigns a higher urgency level.
          - Guard against the same rule firing twice (idempotent).

        Parameters
        ----------
        diagnosis     : str   — internal diagnosis identifier
        cf            : float — Certainty Factor from this rule
        urgency       : str   — urgency level from this rule
        rule_id       : str   — rule identifier (e.g. 'R-08')
        description   : str   — human-readable rule description
        facts_matched : list  — list of fact strings that matched
        """
        if diagnosis in self._hypotheses:
            entry = self._hypotheses[diagnosis]
            if rule_id in entry["rules"]:
                return                              # idempotent guard
            entry["cf"] = CertaintyFactor.combine(entry["cf"], cf)
            if CertaintyFactor.urgency_rank(urgency) > \
               CertaintyFactor.urgency_rank(entry["urgency"]):
                entry["urgency"] = urgency
            entry["rules"].append(rule_id)
        else:
            self._hypotheses[diagnosis] = {
                "cf"     : cf,
                "urgency": urgency,
                "rules"  : [rule_id],
            }

        self._trace.append({
            "rule_id"      : rule_id,
            "description"  : description,
            "facts_matched": facts_matched,
            "conclusion"   : f"{diagnosis} [CF={cf:.2f}, urgency={urgency}]",
        })

    def boost_hypothesis(
        self,
        diagnosis  : str,
        boost      : float,
        rule_id    : str,
        description: str,
        fact       : str,
    ) -> None:
        """
        Apply a CF boost to an existing hypothesis (risk-factor modifier).

        No-op if the hypothesis has not yet been asserted (safe to call
        speculatively from risk-factor rules).

        Parameters
        ----------
        diagnosis   : str   — hypothesis to boost
        boost       : float — CF increment to combine
        rule_id     : str   — modifier rule identifier (e.g. 'RF-01')
        description : str   — human-readable description of the boost
        fact        : str   — the risk-factor fact that triggered the boost
        """
        if diagnosis not in self._hypotheses:
            return
        entry  = self._hypotheses[diagnosis]
        old_cf = entry["cf"]
        entry["cf"] = CertaintyFactor.combine(old_cf, boost)
        self._trace.append({
            "rule_id"      : rule_id,
            "description"  : description,
            "facts_matched": [fact],
            "conclusion"   : (
                f"{diagnosis} CF boosted "
                f"{old_cf:.3f} → {entry['cf']:.4f}"
            ),
        })

    def add_red_flag(self, flag: str, reason: str) -> None:
        """
        Add a red-flag alert entry.  Idempotent: duplicate flags are ignored.

        Parameters
        ----------
        flag   : str — short flag identifier (e.g. 'Suspected_Acute_MI')
        reason : str — plain-language reason for the flag
        """
        if not any(r["flag"] == flag for r in self._red_flags):
            self._red_flags.append({"flag": flag, "reason": reason})

    # ── Read-only accessors ────────────────────────────────────────────────

    @property
    def red_flags(self) -> list:
        """Return a copy of the current red-flag list."""
        return list(self._red_flags)

    @property
    def trace(self) -> list:
        """Return a copy of the ordered inference trace."""
        return list(self._trace)

    def get_ranked_results(self) -> list:
        """
        Return a list of DiagnosisResult objects sorted by clinical priority.

        Sort order
        ----------
        Pass 1 : IMMEDIATE urgency is always ranked first (safety-first).
        Pass 2 : Within the same urgency tier, descending CF score.

        Returns
        -------
        list[DiagnosisResult]
        """
        results = [
            DiagnosisResult(
                diagnosis   = diag,
                cf          = round(data["cf"], 3),
                confidence  = CertaintyFactor.label(data["cf"]),
                urgency     = data["urgency"],
                rules_fired = list(data["rules"]),
            )
            for diag, data in self._hypotheses.items()
        ]
        results.sort(key=lambda r: (
            -CertaintyFactor.urgency_rank(r.urgency),
            -r.cf,
        ))
        return results
