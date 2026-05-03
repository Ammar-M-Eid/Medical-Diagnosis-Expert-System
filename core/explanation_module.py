"""
AIE212 - Medical Diagnosis Expert System
core/explanation_module.py

Responsibility: Convert the raw inference trace produced by WorkingMemory
into plain-language explanations at two levels of detail.
"""

import re


class ExplanationModule:
    """
    Converts the raw inference trace into human-readable explanations.

    summary() returns the patient-facing reasoning process. detailed() returns
    the full rule trace for users who want to inspect every fired rule.
    """

    def summary(self, results: dict) -> str:
        """
        Return a plain-language explanation of how the top diagnosis was chosen.
        """
        primary = results.get("primary")
        if not primary:
            return (
                "Insufficient data - no diagnosis could be determined.\n\n"
                "The engine did not find enough matching rules from the provided "
                "facts. Add symptoms, abnormal vitals, or pain details and run "
                "the assessment again."
            )

        primary_entries = []
        boost_entries = []
        for entry in results.get("trace", []):
            if primary.diagnosis in entry.get("conclusion", ""):
                if "boosted" in entry.get("conclusion", ""):
                    boost_entries.append(entry)
                else:
                    primary_entries.append(entry)

        lines = ["HOW THE SYSTEM DETERMINED THE ILLNESS", ""]
        lines.append(
            "1. The assessment form was converted into facts: patient details, "
            "vital signs, selected symptoms, and pain details when provided."
        )
        lines.append(
            "2. The inference engine compared those facts against the medical "
            "knowledge-base rules."
        )

        if primary_entries:
            first_match = primary_entries[0]
            lines.append(
                f"3. The strongest matching rule for {primary.display_name} was "
                f"{first_match['rule_id']}: {first_match['description']}"
            )
            facts = ", ".join(first_match["facts_matched"])
            lines.append(f"   Matching evidence: {facts}.")
        else:
            lines.append(
                f"3. The engine found supporting evidence for {primary.display_name}."
            )

        if boost_entries:
            boosts = "; ".join(
                f"{entry['rule_id']} ({', '.join(entry['facts_matched'])})"
                for entry in boost_entries
            )
            lines.append(
                f"4. Risk-factor modifier rules adjusted the certainty score: {boosts}."
            )
        else:
            lines.append(
                "4. No risk-factor modifier rule changed the primary certainty score."
            )

        lines.append(
            f"5. The final certainty factor was CF={primary.cf}, labelled "
            f"{primary.confidence} confidence."
        )

        if results.get("red_flags"):
            flag_names = "; ".join(
                f"{r['flag'].replace('_', ' ')} ({r['reason']})"
                for r in results["red_flags"]
            )
            lines.append(f"6. Red flags were triggered: {flag_names}.")
            lines.append(
                "   Red flags are treated as safety-critical and can push urgency "
                "to IMMEDIATE."
            )
        else:
            lines.append("6. No red-flag override was triggered.")

        lines.append(
            f"7. Diagnoses were ranked by urgency first, then by certainty factor. "
            f"The top result was {primary.display_name} with urgency "
            f"{primary.urgency}. Rules fired: {', '.join(primary.rules_fired)}."
        )

        if results.get("differentials"):
            alts = ", ".join(
                f"{d.display_name} (CF={d.cf})" for d in results["differentials"]
            )
            lines.append(f"Other diagnoses considered: {alts}.")

        summary_text = "\n".join(lines)
        conflict_explanation = self.explain_conflicts(results)
        if conflict_explanation:
            summary_text += "\n" + conflict_explanation
        return summary_text

    def explain_conflicts(self, results: dict) -> str:
        """
        Explain how conflicts between competing diagnoses were resolved.
        """
        if len(results.get("differentials", [])) < 2:
            return ""

        primary = results["primary"]
        lines = ["", "CONFLICT RESOLUTION EXPLANATION:"]

        for diff in results["differentials"]:
            if diff.urgency == primary.urgency and diff.cf > primary.cf * 0.8:
                lines.append(
                    f"- {diff.display_name} was considered but ranked lower "
                    f"because the strongest matched evidence favored "
                    f"{primary.display_name}."
                )

        return "\n".join(lines) if len(lines) > 2 else ""

    def detailed(self, results: dict) -> str:
        """
        Return a structured reasoning audit plus the chronological rule trace.
        """
        trace = results.get("trace", [])
        if not trace:
            return "No rules fired - insufficient input data provided."

        ranked = [results["primary"]] if results.get("primary") else []
        ranked.extend(results.get("differentials", []))

        hypothesis_entries = {}
        modifier_entries = []
        other_entries = []

        for entry in trace:
            diagnosis = self._diagnosis_from_conclusion(entry.get("conclusion", ""))
            if "boosted" in entry.get("conclusion", ""):
                modifier_entries.append(entry)
            elif diagnosis:
                hypothesis_entries.setdefault(diagnosis, []).append(entry)
            else:
                other_entries.append(entry)

        lines = [
            "REASONING AUDIT TRACE",
            "=" * 72,
            "",
            "FINAL RANKING",
            "-" * 72,
        ]

        if ranked:
            for index, result in enumerate(ranked, 1):
                marker = "PRIMARY" if index == 1 else f"DIFFERENTIAL #{index - 1}"
                lines.append(
                    f"{index}. {marker}: {result.display_name} | "
                    f"CF={result.cf} | confidence={result.confidence} | "
                    f"urgency={result.urgency} | rules={', '.join(result.rules_fired)}"
                )
        else:
            lines.append("No ranked diagnosis was produced.")

        lines.extend(["", "MATCHED DIAGNOSIS RULES", "-" * 72])
        if hypothesis_entries:
            ordered_diagnoses = [r.diagnosis for r in ranked]
            ordered_diagnoses.extend(
                d for d in hypothesis_entries if d not in ordered_diagnoses
            )

            for diagnosis in ordered_diagnoses:
                entries = hypothesis_entries.get(diagnosis)
                if not entries:
                    continue
                display_name = diagnosis.replace("_", " ")
                lines.append(f"\n{display_name}")
                for entry in entries:
                    cf, urgency = self._score_from_conclusion(entry["conclusion"])
                    score = f"CF={cf}, urgency={urgency}" if cf else entry["conclusion"]
                    lines.append(
                        f"  [{entry['rule_id']}] {entry['description']} -> {score}"
                    )
                    for fact in entry.get("facts_matched", []):
                        lines.append(f"      evidence: {fact}")
        else:
            lines.append("No diagnosis-producing rules fired.")

        lines.extend(["", "CERTAINTY MODIFIERS", "-" * 72])
        if modifier_entries:
            for entry in modifier_entries:
                lines.append(f"[{entry['rule_id']}] {entry['description']}")
                lines.append(f"    matched : {', '.join(entry['facts_matched'])}")
                lines.append(f"    effect  : {entry['conclusion']}")
        else:
            lines.append("No modifier rules changed a certainty factor.")

        lines.extend(["", "RED FLAGS", "-" * 72])
        if results.get("red_flags"):
            for flag in results["red_flags"]:
                lines.append(f"- {flag['flag'].replace('_', ' ')}")
                lines.append(f"    reason: {flag['reason']}")
        else:
            lines.append("No red flags were triggered.")

        if other_entries:
            lines.extend(["", "OTHER TRACE ENTRIES", "-" * 72])
            for entry in other_entries:
                lines.append(f"[{entry['rule_id']}] {entry['description']}")
                lines.append(f"    matched    : {', '.join(entry['facts_matched'])}")
                lines.append(f"    conclusion : {entry['conclusion']}")

        lines.extend(["", "CHRONOLOGICAL RULE LOG", "-" * 72])
        for i, entry in enumerate(results["trace"], 1):
            lines.append(f"\nStep {i}  [{entry['rule_id']}]  {entry['description']}")
            lines.append(f"  Facts matched : {', '.join(entry['facts_matched'])}")
            lines.append(f"  Conclusion    : {entry['conclusion']}")
        return "\n".join(lines)

    @staticmethod
    def _diagnosis_from_conclusion(conclusion: str) -> str:
        if not conclusion or " boosted " in conclusion:
            return ""
        return conclusion.split(" [", 1)[0].strip()

    @staticmethod
    def _score_from_conclusion(conclusion: str) -> tuple:
        match = re.search(r"CF=([0-9.]+), urgency=([A-Z_]+)", conclusion)
        if not match:
            return "", ""
        return match.group(1), match.group(2)
