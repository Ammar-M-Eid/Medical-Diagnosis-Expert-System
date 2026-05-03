"""
AIE212 — Medical Diagnosis Expert System
interface/intake_form.py

Responsibility: Collect a structured patient data dictionary from
standard input via an interactive CLI form.

All input is validated: numeric fields are range-checked, and free-text
selections are constrained to allowed option lists.
Returns a dict compatible with InferenceEngine.run().
"""

from interface.console_style import ConsoleStyle


class IntakeForm:
    """
    Interactive CLI patient intake form.

    Collects demographics, medical history, vital signs, and symptoms.
    All fields are validated before returning the completed patient dict.

    Public method
    -------------
    collect() -> dict
    """

    # ── Available option lists (shown to user) ─────────────────────────────

    SYMPTOM_OPTIONS: list = [
        "chest_pain", "shortness_of_breath", "fever", "cough",
        "headache", "nausea", "vomiting", "dysuria", "urinary_frequency",
        "flank_pain", "right_lower_quadrant_pain", "facial_drooping",
        "arm_weakness", "slurred_speech", "diaphoresis", "myalgia",
        "rash", "neck_stiffness", "runny_nose", "sore_throat",
        "vision_change", "dizziness", "abdominal_pain", "back_pain",
        "wheezing", "chills", "joint_pain", "tinnitus", "hearing_loss",
        "bloating", "epigastric_pain", "green_sputum",
    ]

    CONDITION_OPTIONS: list = [
        "hypertension", "diabetes_mellitus", "asthma",
        "cardiac_disease", "renal_disease", "gastric_ulcer", "GERD",
    ]

    PAIN_CHARACTERS: list = [
        "crushing", "pressure", "sharp", "burning",
        "tearing", "dull", "tightness",
    ]

    PAIN_RADIATIONS: list = [
        "left_arm", "jaw", "back", "shoulder", "none",
    ]

    PAIN_SYMPTOMS: set = {
        "chest_pain", "headache", "right_lower_quadrant_pain",
        "flank_pain", "abdominal_pain", "back_pain",
        "epigastric_pain", "joint_pain",
    }

    # ── Public entry point ─────────────────────────────────────────────────

    def collect(self) -> dict:
        """
        Run the full interactive intake form and return a patient data dict.

        Returns
        -------
        dict — patient data compatible with InferenceEngine.run()
        """
        self._section("PATIENT INTAKE FORM")
        data = {}
        data.update(self._collect_demographics())
        data.update(self._collect_history())
        data.update(self._collect_vitals())
        data.update(self._collect_symptoms())
        return data

    # ── Section collectors ─────────────────────────────────────────────────

    def _collect_demographics(self) -> dict:
        self._subsection("[1] Patient Demographics")
        name = self._ask_raw("Full Name", "")
        age = self._ask_int("Age (years)", 18, 80, default=40)
        sex = self._ask_choice("Sex", ["male", "female"], default="male")
        return {"name": name, "age": age, "sex": sex}

    def _collect_history(self) -> dict:
        self._subsection("[2] Medical History")
        print(ConsoleStyle.dim(
            "  Known conditions: " + ", ".join(self.CONDITION_OPTIONS)
        ))
        raw = self._ask_raw("Known conditions (comma-separated, or Enter to skip)", "")
        conditions = [
            c.strip() for c in raw.split(",")
            if c.strip() in self.CONDITION_OPTIONS
        ]
        smoking = self._ask_bool("Current smoker?", default=False)
        alcohol = self._ask_bool("Regular alcohol use?", default=False)
        return {"known_conditions": conditions, "smoking": smoking, "alcohol": alcohol}

    def _collect_vitals(self) -> dict:
        self._subsection("[3] Vital Signs")
        temp = self._ask_float("Body temperature (°C)", 35.0, 42.0, default=37.0)
        hr   = self._ask_int("Heart rate (bpm)", 30, 250, default=75)
        sbp  = self._ask_int("Systolic BP (mmHg)", 60, 260, default=120)
        dbp  = self._ask_int("Diastolic BP (mmHg)", 40, 160, default=80)
        spo2 = self._ask_int("SpO2 (%)", 50, 100, default=98)
        rr   = self._ask_int("Respiratory rate (breaths/min)", 5, 60, default=16)
        cons = self._ask_choice(
            "Level of consciousness",
            ["alert", "confused", "unresponsive"],
            default="alert",
        )
        return {
            "temperature": temp, "heart_rate": hr,
            "systolic_bp": sbp,  "diastolic_bp": dbp,
            "spo2": spo2, "resp_rate": rr, "consciousness": cons,
        }

    def _collect_symptoms(self) -> dict:
        self._subsection("[4] Symptoms")
        print(ConsoleStyle.dim(
            "  Available: " + ", ".join(self.SYMPTOM_OPTIONS)
        ))
        raw = self._ask_raw("Symptoms present (comma-separated)", "")
        symptom_names = [
            s.strip() for s in raw.split(",")
            if s.strip() in self.SYMPTOM_OPTIONS
        ]

        if not symptom_names:
            print(ConsoleStyle.dim("  No recognised symptoms entered."))
            return {"symptoms": [], "pain_detail": None}

        symptoms = []
        for name in symptom_names:
            print(f"\n  {ConsoleStyle.bold(name.upper())}")
            sev  = self._ask_int("  Severity (1–10)", 1, 10, default=5)
            dur  = self._ask_float("  Duration (days)", 0.0, 365.0, default=1.0)
            ons  = self._ask_choice("  Onset", ["sudden", "gradual"], default="gradual")
            prog = self._ask_choice(
                "  Progression",
                ["improving", "stable", "worsening"],
                default="stable",
            )
            symptoms.append({
                "name": name, "severity": sev,
                "duration_days": dur, "onset": ons, "progression": prog,
            })

        pain_detail = None
        if self.PAIN_SYMPTOMS.intersection(symptom_names):
            self._subsection("[5] Pain Detail")
            char = self._ask_choice("Pain character", self.PAIN_CHARACTERS, default="sharp")
            rad  = self._ask_choice("Pain radiation", self.PAIN_RADIATIONS, default="none")
            pain_detail = {"character": char, "radiation": rad}

        return {"symptoms": symptoms, "pain_detail": pain_detail}

    # ── Section formatting helpers ─────────────────────────────────────────

    @staticmethod
    def _section(title: str) -> None:
        print(f"\n{ConsoleStyle.bold('=' * 60)}")
        print(f"{ConsoleStyle.bold(f'  {title}')}")
        print(ConsoleStyle.bold("=" * 60))

    @staticmethod
    def _subsection(title: str) -> None:
        print(f"\n  {ConsoleStyle.bold(title)}")

    # ── Low-level validated input helpers ─────────────────────────────────

    @staticmethod
    def _ask_raw(prompt: str, default: str) -> str:
        suffix = f" [{default}]" if default != "" else ""
        val = input(f"  {prompt}{suffix}: ").strip()
        return val if val else default

    @staticmethod
    def _ask_int(prompt: str, lo: int, hi: int, default: int) -> int:
        while True:
            raw = input(f"  {prompt} [{default}]: ").strip()
            val = default if raw == "" else None
            if val is None:
                try:
                    val = int(raw)
                except ValueError:
                    pass
            if val is not None and lo <= val <= hi:
                return val
            print(ConsoleStyle.dim(
                f"  Please enter a whole number between {lo} and {hi}."
            ))

    @staticmethod
    def _ask_float(prompt: str, lo: float, hi: float, default: float) -> float:
        while True:
            raw = input(f"  {prompt} [{default}]: ").strip()
            val = default if raw == "" else None
            if val is None:
                try:
                    val = float(raw)
                except ValueError:
                    pass
            if val is not None and lo <= val <= hi:
                return val
            print(ConsoleStyle.dim(
                f"  Please enter a number between {lo} and {hi}."
            ))

    @staticmethod
    def _ask_choice(prompt: str, options: list, default: str) -> str:
        opts_str = " / ".join(options)
        while True:
            raw = input(f"  {prompt} ({opts_str}) [{default}]: ").strip().lower()
            val = raw if raw else default
            if val in options:
                return val
            print(ConsoleStyle.dim(f"  Please choose from: {opts_str}"))

    @staticmethod
    def _ask_bool(prompt: str, default: bool) -> bool:
        label = "[Y/n]" if default else "[y/N]"
        raw = input(f"  {prompt} {label}: ").strip().lower()
        if raw == "":
            return default
        return raw in ("y", "yes")
