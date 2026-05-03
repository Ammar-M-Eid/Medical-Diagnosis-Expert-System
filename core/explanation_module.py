"""
AIE212 — Medical Diagnosis Expert System
core/explanation_module.py

Responsibility: Convert the raw inference trace produced by WorkingMemory
into plain-language explanations at two levels of detail.

Methods
-------
summary(results)         — 4–6 plain-language sentences (primary + flags)
explain_conflicts(results) — how competing diagnoses were resolved
detailed(results)        — full step-by-step rule firing trace
"""


class ExplanationModule:
    """
    Converts the raw inference trace into human-readable explanations.

    Two levels of output are available:

    summary()   — Concise narrative covering the primary diagnosis, key
                  supporting evidence, red flags, and top differentials.

    detailed()  — Full step-by-step rule trace showing each rule that fired,
                  the facts it matched, and the conclusion it drew.
    """

    def summary(self, results: dict) -> str:
        """
        Return a concise, plain-language explanation of the primary diagnosis.

        Parameters
        ----------
        results : dict — output from InferenceEngine.run()

        Returns
        -------
        str — multi-line explanation text
        """
        primary = results.get("primary")
        if not primary:
            return "Insufficient data — no diagnosis could be determined."

        lines = []
        lines.append(
            f"The system identified '{primary.display_name}' as the most likely "
            f"diagnosis with {primary.confidence} confidence (CF = {primary.cf})."
        )

        # Find the first trace entry that mentions this diagnosis
        for entry in results["trace"]:
            if primary.diagnosis in entry["conclusion"]:
                facts = ", ".join(entry["facts_matched"])
                lines.append(f"Key supporting findings: {facts}.")
                break

        if results["red_flags"]:
            flag_names = "; ".join(r["flag"] for r in results["red_flags"])
            lines.append(f"RED FLAG(S) triggered: {flag_names}.")
            lines.append(
                "Red flags override all priority levels — urgency is set to IMMEDIATE."
            )

        lines.append(
            f"Urgency level: {primary.urgency}. "
            f"Rules fired: {', '.join(primary.rules_fired)}."
        )

        if results["differentials"]:
            alts = ", ".join(
                f"{d.display_name} (CF={d.cf})" for d in results["differentials"]
            )
            lines.append(f"Alternative diagnoses considered: {alts}.")

        summary_text = "\n".join(lines)

        # Append conflict resolution note when multiple differentials exist
        if len(results["differentials"]) >= 2:
            conflict_explanation = self.explain_conflicts(results)
            if conflict_explanation:
                summary_text += "\n" + conflict_explanation

        return summary_text

    def explain_conflicts(self, results: dict) -> str:
        """
        Explain how conflicts between competing diagnoses were resolved.

        Only produces output when two or more differentials are present and
        at least one has a CF close to the primary.

        Parameters
        ----------
        results : dict — output from InferenceEngine.run()

        Returns
        -------
        str — conflict resolution explanation, or empty string if not applicable
        """
        if len(results["differentials"]) < 2:
            return ""

        primary = results["primary"]
        lines = ["\nCONFLICT RESOLUTION EXPLANATION:"]

        for diff in results["differentials"]:
            if diff.urgency == primary.urgency and diff.cf > primary.cf * 0.8:
                lines.append(
                    f"- {diff.display_name} was considered but ranked lower due to: "
                    f"specific symptom patterns favouring {primary.display_name}."
                )

        return "\n".join(lines) if len(lines) > 1 else ""

    def detailed(self, results: dict) -> str:
        """
        Return a full step-by-step rule firing trace with facts and conclusions.

        Parameters
        ----------
        results : dict — output from InferenceEngine.run()

        Returns
        -------
        str — formatted multi-line trace
        """
        if not results["trace"]:
            return "No rules fired — insufficient input data provided."

        lines = ["DETAILED RULE TRACE", "-" * 52]
        for i, entry in enumerate(results["trace"], 1):
            lines.append(f"\nStep {i}  [{entry['rule_id']}]  {entry['description']}")
            lines.append(f"  Facts matched : {', '.join(entry['facts_matched'])}")
            lines.append(f"  Conclusion    : {entry['conclusion']}")
        return "\n".join(lines)
