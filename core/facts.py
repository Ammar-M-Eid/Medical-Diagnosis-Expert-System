"""
AIE212 — Medical Diagnosis Expert System
core/facts.py

Responsibility: Define all experta Fact subclasses that represent
Working Memory atoms (patient data inputs).

Classes
-------
PatientInfo  — demographics and medical history
Symptom      — a single reported symptom
PainDetail   — qualitative pain character and radiation
Vital        — measured vital signs
"""

import collections
import collections.abc

# Compatibility shim for Python 3.10+ / experta
collections.Mapping = collections.abc.Mapping

from experta import Fact


class PatientInfo(Fact):
    """
    Core patient demographics and medical history.

    Fields
    ------
    age              : int   — patient age in years
    sex              : str   — 'male' | 'female'
    known_conditions : list  — e.g. ['hypertension', 'diabetes_mellitus']
    smoking          : bool  — current smoker?
    alcohol          : bool  — regular alcohol use?
    """
    pass


class Symptom(Fact):
    """
    A single reported symptom.

    Fields
    ------
    name          : str   — symptom identifier (e.g. 'chest_pain')
    severity      : int   — 1–10 self-reported severity scale
    duration_days : float — number of days symptom has been present
    onset         : str   — 'sudden' | 'gradual'
    progression   : str   — 'improving' | 'stable' | 'worsening'
    """
    pass


class PainDetail(Fact):
    """
    Qualitative detail about pain when pain is part of the chief complaint.

    Fields
    ------
    character : str — 'crushing' | 'pressure' | 'sharp' | 'burning' |
                      'tearing' | 'dull' | 'tightness'
    radiation : str — 'left_arm' | 'jaw' | 'back' | 'shoulder' | 'none'
    """
    pass


class Vital(Fact):
    """
    Measured vital signs for the current patient.

    Fields
    ------
    temperature   : float — body temperature in degrees Celsius
    heart_rate    : int   — heart rate in beats per minute
    systolic_bp   : int   — systolic blood pressure in mmHg
    diastolic_bp  : int   — diastolic blood pressure in mmHg
    spo2          : int   — blood oxygen saturation percentage
    resp_rate     : int   — respiratory rate in breaths per minute
    consciousness : str   — 'alert' | 'confused' | 'unresponsive'
    """
    pass
