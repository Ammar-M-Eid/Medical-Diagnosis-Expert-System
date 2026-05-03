"""
AIE212 — Medical Diagnosis Expert System
tests/test_medical_system.py

Phase 5 test suite covering four key clinical scenarios.
Run with:  python -m pytest tests/ -v
           OR: python -m unittest tests.test_medical_system
"""

import unittest
import sys
import os

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.inference_engine import InferenceEngine


class TestMedicalSystem(unittest.TestCase):
    """Unit tests for the Medical Diagnosis Expert System (Phase 4 implementation)."""

    def setUp(self):
        """Create a fresh InferenceEngine for each test case."""
        self.engine = InferenceEngine()

    # ── Test 1: Acute Myocardial Infarction ───────────────────────────────

    def test_mi_detection(self):
        """Acute Myocardial Infarction should be primary with CF ≥ 0.90 and IMMEDIATE urgency."""
        patient_data = {
            "age": 58, "sex": "male",
            "known_conditions": ["hypertension"],
            "smoking": True, "alcohol": False,
            "temperature": 37.0, "heart_rate": 102,
            "systolic_bp": 140, "diastolic_bp": 90,
            "spo2": 94, "resp_rate": 18,
            "consciousness": "alert",
            "symptoms": [
                {"name": "chest_pain",          "severity": 9,  "duration_days": 0.1, "onset": "sudden",  "progression": "worsening"},
                {"name": "diaphoresis",          "severity": 7,  "duration_days": 0.1, "onset": "sudden",  "progression": "stable"},
                {"name": "shortness_of_breath",  "severity": 6,  "duration_days": 0.1, "onset": "sudden",  "progression": "worsening"},
            ],
            "pain_detail": {"character": "crushing", "radiation": "left_arm"},
        }
        results = self.engine.run(patient_data)
        self.assertIsNotNone(results["primary"])
        self.assertEqual(results["primary"].diagnosis, "Acute_Myocardial_Infarction")
        self.assertGreaterEqual(results["primary"].cf, 0.90)
        self.assertEqual(results["primary"].urgency, "IMMEDIATE")

    # ── Test 2: Lower UTI ─────────────────────────────────────────────────

    def test_uti_detection(self):
        """Lower UTI should be primary with CF ≥ 0.70 for a young female with classic symptoms."""
        patient_data = {
            "age": 24, "sex": "female",
            "known_conditions": [],
            "smoking": False, "alcohol": False,
            "temperature": 37.8, "heart_rate": 85,
            "systolic_bp": 120, "diastolic_bp": 80,
            "spo2": 98, "resp_rate": 16,
            "consciousness": "alert",
            "symptoms": [
                {"name": "dysuria",            "severity": 7, "duration_days": 2, "onset": "gradual", "progression": "worsening"},
                {"name": "urinary_frequency",  "severity": 6, "duration_days": 2, "onset": "gradual", "progression": "stable"},
            ],
            "pain_detail": None,
        }
        results = self.engine.run(patient_data)
        self.assertIsNotNone(results["primary"])
        self.assertEqual(results["primary"].diagnosis, "UTI_Lower")
        self.assertGreaterEqual(results["primary"].cf, 0.70)

    # ── Test 3: Sepsis ────────────────────────────────────────────────────

    def test_sepsis_detection(self):
        """Sepsis should be primary with CF ≥ 0.80 and IMMEDIATE urgency."""
        patient_data = {
            "age": 45, "sex": "male",
            "known_conditions": [],
            "smoking": False, "alcohol": False,
            "temperature": 39.0, "heart_rate": 110,
            "systolic_bp": 90, "diastolic_bp": 60,
            "spo2": 95, "resp_rate": 22,
            "consciousness": "alert",
            "symptoms": [
                {"name": "fever",  "severity": 8, "duration_days": 1, "onset": "sudden", "progression": "worsening"},
                {"name": "chills", "severity": 7, "duration_days": 1, "onset": "sudden", "progression": "stable"},
            ],
            "pain_detail": None,
        }
        results = self.engine.run(patient_data)
        self.assertIsNotNone(results["primary"])
        self.assertEqual(results["primary"].diagnosis, "Sepsis")
        self.assertGreaterEqual(results["primary"].cf, 0.80)
        self.assertEqual(results["primary"].urgency, "IMMEDIATE")

    # ── Test 4: Asthma Exacerbation ───────────────────────────────────────

    def test_asthma_exacerbation(self):
        """Asthma Exacerbation should be primary with CF ≥ 0.70 for known asthmatic with SOB + wheezing."""
        patient_data = {
            "age": 25, "sex": "female",
            "known_conditions": ["asthma"],
            "smoking": False, "alcohol": False,
            "temperature": 37.0, "heart_rate": 90,
            "systolic_bp": 120, "diastolic_bp": 80,
            "spo2": 94, "resp_rate": 25,
            "consciousness": "alert",
            "symptoms": [
                {"name": "shortness_of_breath", "severity": 8, "duration_days": 1, "onset": "sudden", "progression": "worsening"},
                {"name": "wheezing",             "severity": 7, "duration_days": 1, "onset": "sudden", "progression": "worsening"},
            ],
            "pain_detail": None,
        }
        results = self.engine.run(patient_data)
        self.assertIsNotNone(results["primary"])
        self.assertEqual(results["primary"].diagnosis, "Asthma_Exacerbation")
        self.assertGreaterEqual(results["primary"].cf, 0.70)


if __name__ == "__main__":
    unittest.main()
