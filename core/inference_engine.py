"""
AIE212 — Medical Diagnosis Expert System
core/inference_engine.py

Responsibility: Orchestrate one complete patient assessment cycle.

Steps
-----
1. Accept a structured patient data dictionary.
2. Instantiate a fresh WorkingMemory and KnowledgeBase.
3. Load all patient facts into the KB (fact assertion).
4. Run the KB (forward-chaining inference via experta).
5. Return ranked results, red flags, and inference trace.
"""

from core.working_memory import WorkingMemory
from core.facts import PatientInfo, Symptom, PainDetail, Vital
from knowledge.knowledge_base import KnowledgeBase


class InferenceEngine:
    """
    Orchestrates one complete patient assessment cycle.

    Stateless — safe to reuse across multiple patient sessions.

    Usage
    -----
        engine  = InferenceEngine()
        results = engine.run(patient_data_dict)
    """

    def run(self, patient_data: dict) -> dict:
        """
        Execute a full forward-chaining diagnostic inference cycle.

        Parameters
        ----------
        patient_data : dict
            Expected keys:
              age, sex, known_conditions, smoking, alcohol,
              temperature, heart_rate, systolic_bp, diastolic_bp,
              spo2, resp_rate, consciousness,
              symptoms (list of dicts), pain_detail (dict | None)

        Returns
        -------
        dict with keys:
            primary       : DiagnosisResult | None
            differentials : list[DiagnosisResult]  (up to 3)
            red_flags     : list[dict]
            trace         : list[dict]
        """
        wm = WorkingMemory()
        kb = KnowledgeBase(wm)
        kb.reset()

        self._load_facts(kb, patient_data)
        kb.run()

        ranked = wm.get_ranked_results()
        return {
            "primary"      : ranked[0] if ranked else None,
            "differentials": ranked[1:4],
            "red_flags"    : wm.red_flags,
            "trace"        : wm.trace,
        }

    @staticmethod
    def _load_facts(kb: KnowledgeBase, data: dict) -> None:
        """
        Convert a patient data dictionary into experta Facts and declare
        them into the KnowledgeBase working memory.

        Parameters
        ----------
        kb   : KnowledgeBase — target engine to declare facts into
        data : dict          — raw patient data dictionary
        """
        kb.declare(PatientInfo(
            age              = data.get("age", 30),
            sex              = data.get("sex", "male"),
            known_conditions = data.get("known_conditions", []),
            smoking          = data.get("smoking", False),
            alcohol          = data.get("alcohol", False),
        ))

        kb.declare(Vital(
            temperature   = data.get("temperature", 37.0),
            heart_rate    = data.get("heart_rate", 75),
            systolic_bp   = data.get("systolic_bp", 120),
            diastolic_bp  = data.get("diastolic_bp", 80),
            spo2          = data.get("spo2", 98),
            resp_rate     = data.get("resp_rate", 16),
            consciousness = data.get("consciousness", "alert"),
        ))

        for sym in data.get("symptoms", []):
            kb.declare(Symptom(
                name         = sym["name"],
                severity     = sym.get("severity", 5),
                duration_days= sym.get("duration_days", 1),
                onset        = sym.get("onset", "gradual"),
                progression  = sym.get("progression", "stable"),
            ))

        if data.get("pain_detail"):
            kb.declare(PainDetail(
                character = data["pain_detail"]["character"],
                radiation = data["pain_detail"]["radiation"],
            ))
