"""
AIE212 — Medical Diagnosis Expert System
interface/result_renderer.py

Responsibility: Render a results dict (from InferenceEngine.run()) to
the terminal. Composes ConsoleStyle, ActionLibrary, and ExplanationModule.
"""

from interface.console_style import ConsoleStyle
from interface.action_library import ActionLibrary
from core.explanation_module import ExplanationModule
from core.diagnosis_result import DiagnosisResult


class ResultRenderer:
    """
    Renders a diagnostic results dict to the console.

    Calls ExplanationModule internally for the reasoning narrative.

    Public method
    -------------
    render(results: dict) -> None
    """

    def __init__(self):
        self._explainer = ExplanationModule()

    def render(self, results: dict) -> None:
        """
        Print the full assessment output to stdout.

        Parameters
        ----------
        results : dict — output from InferenceEngine.run()
        """
        print(f"\n{'=' * 60}")
        print(ConsoleStyle.bold("  ASSESSMENT RESULTS"))
        print(f"{'=' * 60}")

        self._render_red_flags(results["red_flags"])
        self._render_primary(results)
        self._render_differentials(results["differentials"])
        self._render_actions(results["primary"])
        self._render_explanation(results)
        self._render_disclaimer()

    # ── Section renderers ──────────────────────────────────────────────────

    @staticmethod
    def _render_red_flags(red_flags: list) -> None:
        if not red_flags:
            return
        print(f"\n{ConsoleStyle.apply('  RED FLAGS DETECTED', ConsoleStyle.BOLD, ConsoleStyle.RED)}")
        for rf in red_flags:
            print(f"  {'!' * 3}  {ConsoleStyle.bold(rf['flag'])}")
            print(f"         {rf['reason']}")

    @staticmethod
    def _render_primary(results: dict) -> None:
        p = results.get("primary")
        if not p:
            print(ConsoleStyle.dim(
                "\n  No matching diagnosis found. "
                "Please check inputs or consult a clinician."
            ))
            return
        print(f"\n{ConsoleStyle.bold('  PRIMARY DIAGNOSIS')}")
        print(f"  {ConsoleStyle.bold(p.display_name)}")
        print(f"  Confidence  : {ConsoleStyle.bold(p.confidence)} (CF = {p.cf})")
        print(f"  Urgency     : {ConsoleStyle.urgency(p.urgency)}")
        print(f"  Rules fired : {ConsoleStyle.dim(', '.join(p.rules_fired))}")

    @staticmethod
    def _render_differentials(differentials: list) -> None:
        if not differentials:
            return
        print(f"\n{ConsoleStyle.bold('  DIFFERENTIAL DIAGNOSES')}")
        header = f"  {'#':<3}  {'Diagnosis':<35}  {'CF':<6}  {'Confidence':<12}  Urgency"
        print(ConsoleStyle.dim(header))
        print(ConsoleStyle.dim("  " + "-" * 68))
        for i, d in enumerate(differentials, 2):
            print(
                f"  {i:<3}  {d.display_name:<35}  {d.cf:<6}  "
                f"{d.confidence:<12}  {d.urgency}"
            )

    @staticmethod
    def _render_actions(primary: DiagnosisResult) -> None:
        if not primary:
            return
        actions = ActionLibrary.get(primary.diagnosis)
        print(f"\n{ConsoleStyle.bold('  RECOMMENDED ACTIONS')}")
        for action in actions:
            prefix = (
                ConsoleStyle.apply("  [!]", ConsoleStyle.BOLD, ConsoleStyle.RED)
                if action.startswith("CALL") or action.startswith("ADMINISTER")
                else "  [ ]"
            )
            print(f"{prefix}  {action}")

    def _render_explanation(self, results: dict) -> None:
        print(f"\n{ConsoleStyle.bold('  REASONING EXPLANATION')}")
        summary = self._explainer.summary(results)
        for line in summary.split("\n"):
            print(f"  {line}")

        choice = input("\n  Show full rule trace? (y/N): ").strip().lower()
        if choice in ("y", "yes"):
            print()
            detailed = self._explainer.detailed(results)
            for line in detailed.split("\n"):
                print(f"  {line}")

    @staticmethod
    def _render_disclaimer() -> None:
        print(f"\n{'─' * 60}")
        print(ConsoleStyle.dim(
            "  DISCLAIMER: This system is a decision-support tool only.\n"
            "  All outputs must be reviewed by a licensed clinician.\n"
            "  Do not act on these results without professional oversight."
        ))
        print(f"{'─' * 60}\n")
