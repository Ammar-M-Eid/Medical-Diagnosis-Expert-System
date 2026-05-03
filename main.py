"""
AIE212 — Medical Diagnosis Expert System
main.py

Entry point. Composes all subsystems into an interactive session loop.

Run:
    python main.py

OOP Structure
─────────────────────────────────────────────────────────
  App — main application controller (entry point)
        Composes: IntakeForm, InferenceEngine,
                  ResultRenderer, DataPersistence
─────────────────────────────────────────────────────────
"""

from core.inference_engine   import InferenceEngine
from interface.console_style import ConsoleStyle
from interface.intake_form   import IntakeForm
from interface.result_renderer import ResultRenderer
from utils.data_persistence  import DataPersistence


class App:
    """
    Main application controller.

    Composes IntakeForm, InferenceEngine, ResultRenderer, and
    DataPersistence into a complete interactive session loop.

    Usage
    -----
        app = App()
        app.run()
    """

    def __init__(self):
        self._form        = IntakeForm()
        self._engine      = InferenceEngine()
        self._renderer    = ResultRenderer()
        self._persistence = DataPersistence()

    def run(self) -> None:
        """Start the interactive application loop."""
        self._print_banner()
        while True:
            choice = self._main_menu()
            if choice == "1":
                self._run_assessment()
            elif choice == "2":
                self._view_saved_assessment()
            elif choice == "0":
                print("\n  Goodbye.\n")
                break

    # ── Private helpers ────────────────────────────────────────────────────

    def _run_assessment(self) -> None:
        """Collect patient data, run inference, render results."""
        patient_data = self._form.collect()
        print(f"\n{ConsoleStyle.dim('  Running inference engine...')}")
        results = self._engine.run(patient_data)
        self._renderer.render(results)

        save_choice = input("  Save this assessment? (y/N): ").strip().lower()
        if save_choice in ("y", "yes"):
            filename = self._persistence.save_assessment(patient_data, results)
            print(ConsoleStyle.dim(f"  Assessment saved to {filename}"))

        input("\n  Press Enter to return to the main menu...")

    def _view_saved_assessment(self) -> None:
        """View a previously saved assessment by patient name."""
        saved = self._persistence.list_saved_patients()

        if saved:
            print("\n  Saved patients:")
            for name in saved:
                print(f"    - {name}")
            print()
        else:
            print(ConsoleStyle.dim("\n  No saved assessments found.\n"))
            input("  Press Enter to return to the main menu...")
            return

        patient_name = input("  Enter patient name to load: ").strip()
        if not patient_name:
            print(ConsoleStyle.dim("  No name entered."))
            input("  Press Enter to continue...")
            return

        try:
            data = self._persistence.load_assessment(patient_name)
            print(f"\n{ConsoleStyle.bold('  LOADED ASSESSMENT')}")
            print(f"  Patient Name: {data['patient_data'].get('name', 'Unknown')}")
            print(f"  Timestamp   : {data['timestamp']}")
            primary = data["results"]["primary"]
            print(f"  Primary Diagnosis: {primary['diagnosis'] if primary else 'None'}")
        except FileNotFoundError:
            print(ConsoleStyle.dim(f"  No assessment found for '{patient_name}'."))
        except Exception as e:
            print(ConsoleStyle.dim(f"  Error loading file: {e}"))

        input("\n  Press Enter to return to the main menu...")

    @staticmethod
    def _main_menu() -> str:
        print(ConsoleStyle.bold("\n  MAIN MENU"))
        print("  [1]  New patient assessment")
        print("  [2]  View saved assessment")
        print("  [0]  Exit")
        return input("\n  Choice: ").strip()

    @staticmethod
    def _print_banner() -> None:
        print(ConsoleStyle.bold(
            "\n"
            "  ╔══════════════════════════════════════════════════════╗\n"
            "  ║   AIE212 — Medical Diagnosis Expert System           ║\n"
            "  ║   Clinical Triage & Preliminary Diagnosis KBS        ║\n"
            "  ║   Alamein International University                   ║\n"
            "  ╚══════════════════════════════════════════════════════╝"
        ))
        print(ConsoleStyle.dim(
            "\n  This system is a DECISION-SUPPORT TOOL ONLY.\n"
            "  All outputs must be reviewed by a licensed clinician.\n"
        ))


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    App().run()
