"""
AIE212 — Medical Diagnosis Expert System
knowledge/knowledge_base.py

Responsibility: All IF-THEN production rules encoded as experta @Rule methods.

The KnowledgeBase does NOT own its WorkingMemory; a WorkingMemory instance
is injected at construction time by the InferenceEngine. This decouples
rule logic from result storage (Dependency Injection pattern).

Rule Groups
-----------
Simple rules   R-01 – R-04   Single vital/symptom → hypothesis
Complex rules  R-05 – R-30   Multi-condition       → specific diagnosis
Modifier rules RF-01 – RF-02 Risk-factor CF boosters (no new hypothesis)
"""

import collections
import collections.abc

collections.Mapping = collections.abc.Mapping

from experta import KnowledgeEngine, Rule, MATCH, TEST, NOT

from core.facts import PatientInfo, Symptom, PainDetail, Vital
from core.working_memory import WorkingMemory


class KnowledgeBase(KnowledgeEngine):
    """
    All IF-THEN production rules encoded as experta @Rule methods.

    Dependency injection
    --------------------
    A WorkingMemory instance must be passed to __init__. The KB writes
    all conclusions to the injected WorkingMemory; it never stores results
    itself.
    """

    def __init__(self, working_memory: WorkingMemory):
        super().__init__()
        self._wm = working_memory

    # ── Private shorthand helpers ──────────────────────────────────────────

    def _assert(self, diagnosis, cf, urgency, rule_id, desc, facts):
        """Delegate assertion to the injected WorkingMemory."""
        self._wm.assert_hypothesis(diagnosis, cf, urgency, rule_id, desc, facts)

    def _flag(self, flag, reason):
        """Delegate red-flag registration to the injected WorkingMemory."""
        self._wm.add_red_flag(flag, reason)

    def _boost(self, diagnosis, boost, rule_id, desc, fact):
        """Delegate CF boost to the injected WorkingMemory."""
        self._wm.boost_hypothesis(diagnosis, boost, rule_id, desc, fact)

    # ══════════════════════════════════════════════════════════════════════
    # SIMPLE RULES — single vital / symptom → hypothesis
    # ══════════════════════════════════════════════════════════════════════

    @Rule(Vital(temperature=MATCH.t), TEST(lambda t: t > 38.0))
    def r01_fever_infection(self, t):
        """R-01 — Elevated temperature → generic infection present."""
        self._assert(
            "Infection_Present", 0.55, "SEMI_URGENT", "R-01",
            "Elevated temperature suggests infection present",
            [f"temperature={t}°C"],
        )

    @Rule(Vital(spo2=MATCH.s), TEST(lambda s: s < 90))
    def r02_critical_spo2(self, s):
        """R-02 — SpO2 < 90 % → respiratory emergency (red flag)."""
        self._flag(
            "SpO2_Critical",
            f"SpO2 = {s}% (below 90%) — possible respiratory failure",
        )
        self._assert(
            "Respiratory_Emergency", 1.0, "IMMEDIATE", "R-02",
            "Critical SpO2 triggers immediate respiratory emergency",
            [f"spo2={s}%"],
        )

    @Rule(Symptom(name="fever"), Symptom(name="cough"))
    def r03_influenza_simple(self):
        """R-03 — Fever + cough → possible influenza (low-confidence seed)."""
        self._assert(
            "Possible_Influenza", 0.50, "NON_URGENT", "R-03",
            "Fever + cough → possible influenza (low-confidence seed)",
            ["fever", "cough"],
        )

    @Rule(Vital(consciousness="unresponsive"))
    def r04_unresponsive(self):
        """R-04 — Unresponsive patient → immediate emergency (red flag)."""
        self._flag(
            "Unresponsive_Patient",
            "Patient is unresponsive — undifferentiated emergency",
        )
        self._assert(
            "Undifferentiated_Emergency", 1.0, "IMMEDIATE", "R-04",
            "Unresponsive patient triggers undifferentiated emergency",
            ["consciousness=unresponsive"],
        )

    # ══════════════════════════════════════════════════════════════════════
    # COMPLEX RULES — multi-symptom / vital → specific diagnosis
    # ══════════════════════════════════════════════════════════════════════

    @Rule(
        Symptom(name="fever"), Symptom(name="cough"), Symptom(name="myalgia"),
        Symptom(onset=MATCH.o), TEST(lambda o: o == "sudden"),
    )
    def r05_influenza_multi(self, o):
        """R-05 — Sudden fever + cough + myalgia → probable influenza."""
        self._assert(
            "Influenza", 0.74, "NON_URGENT", "R-05",
            "Sudden onset fever + cough + myalgia → probable influenza",
            ["fever", "cough", "myalgia", "onset=sudden"],
        )

    @Rule(
        Symptom(name="headache", severity=MATCH.sev), TEST(lambda sev: sev <= 6),
        NOT(Symptom(name="fever")),
        NOT(Symptom(name="neck_stiffness")),
        NOT(Symptom(name="vision_change")),
    )
    def r06_tension_headache(self, sev):
        """R-06 — Mild/moderate headache, no neurological signs → tension headache."""
        self._assert(
            "Tension_Headache", 0.72, "NON_URGENT", "R-06",
            "Headache without fever or neurological signs → tension headache",
            [f"headache severity={sev}", "no fever", "no neck stiffness"],
        )

    @Rule(
        Symptom(name="runny_nose"), Symptom(name="sore_throat"),
        Vital(temperature=MATCH.t), TEST(lambda t: t < 38.0),
    )
    def r07_common_cold(self, t):
        """R-07 — Runny nose + sore throat + no fever → URTI / common cold."""
        self._assert(
            "URTI_Common_Cold", 0.78, "NON_URGENT", "R-07",
            "Runny nose + sore throat + afebrile → URTI/common cold",
            ["runny_nose", "sore_throat", f"temperature={t}°C"],
        )

    @Rule(
        PatientInfo(age=MATCH.age), TEST(lambda age: age >= 40),
        Symptom(name="chest_pain"),
        PainDetail(character=MATCH.ch), TEST(lambda ch: ch in ["crushing", "pressure"]),
        PainDetail(radiation=MATCH.rad), TEST(lambda rad: rad in ["left_arm", "jaw"]),
        Symptom(name="diaphoresis"),
        Vital(spo2=MATCH.s, heart_rate=MATCH.hr),
        TEST(lambda s, hr: s < 95 or hr > 100),
    )
    def r08_acute_mi(self, age, ch, rad, s, hr):
        """R-08 — RED FLAG: Suspected Acute Myocardial Infarction."""
        self._flag(
            "Suspected_Acute_MI",
            f"Age {age}, {ch} chest pain → {rad}, diaphoresis, "
            f"SpO2={s}%, HR={hr}bpm",
        )
        self._assert(
            "Acute_Myocardial_Infarction", 0.95, "IMMEDIATE", "R-08",
            "Age≥40 + crushing/pressure chest pain + left-arm/jaw radiation "
            "+ diaphoresis + abnormal vitals",
            [f"age={age}", f"pain={ch}", f"radiation={rad}",
             "diaphoresis", f"spo2={s}", f"HR={hr}"],
        )

    @Rule(
        PatientInfo(age=MATCH.age), TEST(lambda age: age >= 35),
        Symptom(name="chest_pain"),
        PainDetail(character=MATCH.ch),
        TEST(lambda ch: ch in ["pressure", "crushing", "tightness"]),
        NOT(Symptom(name="diaphoresis")),
    )
    def r09_unstable_angina(self, age, ch):
        """R-09 — Chest pressure/crushing without diaphoresis → unstable angina."""
        self._assert(
            "Unstable_Angina", 0.68, "URGENT", "R-09",
            "Chest pressure/crushing without diaphoresis, age≥35 → unstable angina",
            [f"age={age}", f"pain character={ch}", "no diaphoresis"],
        )

    @Rule(
        Symptom(name="abdominal_pain"),
        Symptom(name="fever"),
        Symptom(name="nausea"),
        Vital(temperature=MATCH.t), TEST(lambda t: t >= 38.0),
        NOT(Symptom(name="right_lower_quadrant_pain")),
    )
    def r10_gastroenteritis(self, t):
        """R-10 — Abdominal pain + fever + nausea → gastroenteritis."""
        self._assert(
            "Gastroenteritis", 0.70, "SEMI_URGENT", "R-10",
            "Abdominal pain + fever + nausea → gastroenteritis",
            ["abdominal_pain", "fever", "nausea", f"temperature={t}°C"],
        )

    @Rule(
        Symptom(name="chest_pain"),
        PainDetail(character="tearing"),
        Symptom(name="back_pain"),
        Vital(systolic_bp=MATCH.sbp), TEST(lambda sbp: sbp >= 160),
        Symptom(onset="sudden"),
    )
    def r11_aortic_dissection(self, sbp):
        """R-11 — RED FLAG: Tearing chest pain + back pain + hypertension → aortic dissection."""
        self._flag(
            "Suspected_Aortic_Dissection",
            "Tearing chest pain + back pain + hypertension — possible aortic dissection",
        )
        self._assert(
            "Aortic_Dissection", 0.90, "IMMEDIATE", "R-11",
            "Tearing chest pain + back pain + hypertension + sudden onset → aortic dissection",
            ["chest_pain", "pain=tearing", "back_pain", f"SBP={sbp}", "onset=sudden"],
        )

    @Rule(
        Symptom(name="shortness_of_breath"),
        Symptom(name="wheezing"),
        PatientInfo(known_conditions=MATCH.conds),
        TEST(lambda conds: "asthma" in conds),
        Vital(resp_rate=MATCH.rr), TEST(lambda rr: rr > 22),
    )
    def r12_asthma_exacerbation(self, conds, rr):
        """R-12 — SOB + wheezing + known asthma → asthma exacerbation."""
        self._assert(
            "Asthma_Exacerbation", 0.80, "URGENT", "R-12",
            "SOB + wheezing + known asthma + elevated RR → asthma exacerbation",
            ["shortness_of_breath", "wheezing", "asthma", f"RR={rr}"],
        )

    @Rule(
        Symptom(name="fever"),
        Symptom(name="chills"),
        Vital(heart_rate=MATCH.hr), TEST(lambda hr: hr > 100),
        Vital(systolic_bp=MATCH.sbp), TEST(lambda sbp: sbp < 100),
    )
    def r13_sepsis(self, hr, sbp):
        """R-13 — RED FLAG: Fever + chills + tachycardia + hypotension → sepsis."""
        self._flag(
            "Suspected_Sepsis",
            "Fever + chills + tachycardia + hypotension — possible sepsis",
        )
        self._assert(
            "Sepsis", 0.88, "IMMEDIATE", "R-13",
            "Fever + chills + tachycardia + hypotension → sepsis",
            ["fever", "chills", f"HR={hr}", f"SBP={sbp}"],
        )

    @Rule(
        Symptom(name="facial_drooping"),
        Symptom(name="arm_weakness"),
        Symptom(name="slurred_speech"),
        Symptom(onset=MATCH.o), TEST(lambda o: o == "sudden"),
        Symptom(duration_days=MATCH.d), TEST(lambda d: d <= 1),
    )
    def r14_ischemic_stroke(self, o, d):
        """R-14 — RED FLAG: FAST-positive → suspected ischemic stroke."""
        self._flag(
            "Suspected_Ischemic_Stroke",
            "FAST protocol positive: facial drooping + arm weakness "
            "+ slurred speech, sudden onset",
        )
        self._assert(
            "Ischemic_Stroke", 0.97, "IMMEDIATE", "R-14",
            "FAST positive: facial drooping + arm weakness + slurred speech, sudden onset",
            ["facial_drooping", "arm_weakness", "slurred_speech", "onset=sudden"],
        )

    @Rule(
        Symptom(name="headache"),
        Symptom(name="vision_change"),
        Symptom(name="nausea"),
        Vital(systolic_bp=MATCH.sbp), TEST(lambda sbp: sbp >= 160),
        PatientInfo(known_conditions=MATCH.conds),
        TEST(lambda conds: "hypertension" in conds),
    )
    def r15_hypertensive_encephalopathy(self, sbp, conds):
        """R-15 — Headache + vision changes + nausea + severe hypertension → hypertensive encephalopathy."""
        self._assert(
            "Hypertensive_Encephalopathy", 0.75, "URGENT", "R-15",
            "Headache + vision changes + nausea + severe hypertension "
            "→ hypertensive encephalopathy",
            ["headache", "vision_change", "nausea", f"SBP={sbp}", "hypertension"],
        )

    @Rule(
        Symptom(name="joint_pain"),
        Symptom(name="rash"),
        Symptom(name="fever"),
        Vital(temperature=MATCH.t), TEST(lambda t: t >= 38.0),
    )
    def r16_viral_arthropathy(self, t):
        """R-16 — Joint pain + rash + fever → viral arthropathy."""
        self._assert(
            "Viral_Arthropathy", 0.65, "SEMI_URGENT", "R-16",
            "Joint pain + rash + fever → viral arthropathy",
            ["joint_pain", "rash", "fever", f"temperature={t}°C"],
        )

    @Rule(
        Symptom(name="dizziness"),
        Symptom(name="tinnitus"),
        Symptom(name="hearing_loss"),
        Symptom(onset="sudden"),
    )
    def r17_labyrinthitis(self):
        """R-17 — Dizziness + tinnitus + hearing loss + sudden onset → labyrinthitis."""
        self._assert(
            "Labyrinthitis", 0.68, "SEMI_URGENT", "R-17",
            "Dizziness + tinnitus + hearing loss + sudden onset → labyrinthitis",
            ["dizziness", "tinnitus", "hearing_loss", "onset=sudden"],
        )

    @Rule(
        Symptom(name="chest_pain"),
        Symptom(name="shortness_of_breath"),
        Symptom(onset=MATCH.o), TEST(lambda o: o == "sudden"),
        Vital(heart_rate=MATCH.hr), TEST(lambda hr: hr > 100),
        NOT(Symptom(name="fever")),
    )
    def r18_pulmonary_embolism(self, o, hr):
        """R-18 — Sudden chest pain + SOB + tachycardia, no fever → PE."""
        self._assert(
            "Pulmonary_Embolism", 0.65, "URGENT", "R-18",
            "Sudden chest pain + SOB + tachycardia without fever → pulmonary embolism",
            ["chest_pain", "shortness_of_breath", "onset=sudden", f"HR={hr}"],
        )

    @Rule(
        Symptom(name="epigastric_pain"),
        Symptom(name="nausea"),
        Symptom(name="bloating"),
        PatientInfo(known_conditions=MATCH.conds),
        TEST(lambda conds: "gastric_ulcer" in conds or "GERD" in conds),
    )
    def r19_gastritis(self, conds):
        """R-19 — Epigastric pain + nausea + bloating + gastric history → gastritis."""
        self._assert(
            "Gastritis", 0.72, "SEMI_URGENT", "R-19",
            "Epigastric pain + nausea + bloating + gastric history → gastritis",
            ["epigastric_pain", "nausea", "bloating", "gastric_history"],
        )

    @Rule(
        Symptom(name="cough"),
        Symptom(name="green_sputum"),
        Symptom(name="fever"),
        Vital(temperature=MATCH.t), TEST(lambda t: t >= 38.5),
    )
    def r20_bronchitis(self, t):
        """R-20 — Cough + green sputum + fever → acute bronchitis."""
        self._assert(
            "Acute_Bronchitis", 0.70, "SEMI_URGENT", "R-20",
            "Cough + green sputum + fever → acute bronchitis",
            ["cough", "green_sputum", "fever", f"temperature={t}°C"],
        )

    @Rule(
        Symptom(name="flank_pain"),
        Symptom(name="fever"),
        Symptom(name="dysuria"),
        Vital(temperature=MATCH.t), TEST(lambda t: t >= 38.5),
    )
    def r21_pyelonephritis_alt(self, t):
        """R-21 — Flank pain + fever + dysuria → pyelonephritis."""
        self._assert(
            "Pyelonephritis", 0.78, "URGENT", "R-21",
            "Flank pain + fever + dysuria → pyelonephritis",
            ["flank_pain", "fever", "dysuria", f"temperature={t}°C"],
        )

    @Rule(
        PatientInfo(sex="female"),
        Symptom(name="dysuria"),
        Symptom(name="urinary_frequency"),
        Symptom(duration_days=MATCH.d), TEST(lambda d: d >= 1),
        Vital(temperature=MATCH.t), TEST(lambda t: t < 38.5),
        NOT(Symptom(name="flank_pain")),
    )
    def r22_lower_uti(self, d, t):
        """R-22 — Female + dysuria + frequency + no flank pain → lower UTI."""
        self._assert(
            "UTI_Lower", 0.82, "SEMI_URGENT", "R-22",
            "Female + dysuria + urinary frequency + no flank pain + afebrile → lower UTI",
            ["sex=female", "dysuria", "urinary_frequency",
             f"duration={d}d", f"temp={t}°C"],
        )

    @Rule(
        Symptom(name="dysuria"),
        Symptom(name="flank_pain"),
        Vital(temperature=MATCH.t), TEST(lambda t: t >= 38.5),
    )
    def r23_pyelonephritis(self, t):
        """R-23 — Dysuria + flank pain + high fever → pyelonephritis."""
        self._assert(
            "Pyelonephritis", 0.80, "URGENT", "R-23",
            "Dysuria + flank pain + fever ≥38.5 °C → pyelonephritis",
            ["dysuria", "flank_pain", f"temperature={t}°C"],
        )

    @Rule(
        Symptom(name="right_lower_quadrant_pain", severity=MATCH.sev),
        TEST(lambda sev: sev >= 5),
        Symptom(name="nausea"),
        Vital(temperature=MATCH.t), TEST(lambda t: 37.5 <= t <= 39.0),
    )
    def r24_appendicitis(self, sev, t):
        """R-24 — RLQ pain ≥5 + nausea + low-grade fever → suspected appendicitis."""
        self._assert(
            "Acute_Appendicitis", 0.78, "URGENT", "R-24",
            "RLQ pain ≥5/10 + nausea + low-grade fever → suspected acute appendicitis",
            [f"RLQ pain severity={sev}", "nausea", f"temperature={t}°C"],
        )

    @Rule(
        Symptom(name="fever"),
        Symptom(name="cough"),
        Symptom(name="shortness_of_breath"),
        Vital(temperature=MATCH.t), TEST(lambda t: t >= 38.5),
        Vital(resp_rate=MATCH.rr), TEST(lambda rr: rr > 20),
    )
    def r25_pneumonia(self, t, rr):
        """R-25 — Fever + cough + SOB + high temp + elevated RR → pneumonia."""
        self._assert(
            "Pneumonia", 0.76, "URGENT", "R-25",
            "Fever + cough + SOB + temp≥38.5°C + RR>20 → pneumonia",
            ["fever", "cough", "shortness_of_breath",
             f"temp={t}°C", f"RR={rr}"],
        )

    @Rule(
        Symptom(name="rash"),
        Symptom(name="shortness_of_breath"),
        Symptom(onset=MATCH.o), TEST(lambda o: o == "sudden"),
        Vital(heart_rate=MATCH.hr), TEST(lambda hr: hr > 100),
    )
    def r26_anaphylaxis(self, o, hr):
        """R-26 — RED FLAG: Sudden rash + SOB + tachycardia → anaphylaxis."""
        self._flag(
            "Possible_Anaphylaxis",
            "Sudden rash + shortness of breath + tachycardia — possible anaphylaxis",
        )
        self._assert(
            "Anaphylaxis", 0.88, "IMMEDIATE", "R-26",
            "Sudden rash + SOB + tachycardia → anaphylaxis",
            ["rash", "shortness_of_breath", "onset=sudden", f"HR={hr}"],
        )

    @Rule(
        Symptom(name="chest_pain"),
        PainDetail(character=MATCH.ch), TEST(lambda ch: ch in ["burning", "sharp"]),
        PainDetail(radiation=MATCH.rad), TEST(lambda rad: rad == "none"),
        NOT(Symptom(name="diaphoresis")),
        PatientInfo(age=MATCH.age), TEST(lambda age: age < 55),
    )
    def r27_gerd(self, ch, rad, age):
        """R-27 — Burning/sharp chest pain, no radiation, younger patient → GERD."""
        self._assert(
            "GERD", 0.65, "NON_URGENT", "R-27",
            "Burning/sharp chest pain, no radiation, no diaphoresis, age<55 → GERD",
            [f"pain={ch}", "radiation=none", "no diaphoresis", f"age={age}"],
        )

    @Rule(
        PatientInfo(known_conditions=MATCH.conds),
        TEST(lambda conds: "diabetes_mellitus" in conds),
        Symptom(name="nausea"),
        Symptom(name="vomiting"),
        Vital(consciousness=MATCH.c),
        TEST(lambda c: c in ["confused", "unresponsive"]),
    )
    def r28_dka(self, conds, c):
        """R-28 — Diabetic + nausea/vomiting + altered consciousness → DKA."""
        self._assert(
            "Diabetic_Ketoacidosis", 0.85, "IMMEDIATE", "R-28",
            "Known diabetes + nausea/vomiting + altered consciousness → DKA",
            ["diabetes_mellitus", "nausea", "vomiting", f"consciousness={c}"],
        )

    @Rule(
        Vital(systolic_bp=MATCH.sbp), TEST(lambda sbp: sbp >= 180),
        Vital(diastolic_bp=MATCH.dbp), TEST(lambda dbp: dbp >= 120),
    )
    def r29_hypertensive_crisis(self, sbp, dbp):
        """R-29 — RED FLAG: Systolic ≥180 + diastolic ≥120 → hypertensive crisis."""
        self._flag(
            "Hypertensive_Crisis",
            f"BP {sbp}/{dbp} mmHg — severely elevated, hypertensive crisis",
        )
        self._assert(
            "Hypertensive_Crisis", 0.92, "IMMEDIATE", "R-29",
            "Systolic≥180 + diastolic≥120 → hypertensive crisis",
            [f"SBP={sbp}", f"DBP={dbp}"],
        )

    @Rule(
        Symptom(name="headache", severity=MATCH.sev), TEST(lambda sev: sev >= 8),
        Symptom(name="neck_stiffness"),
        Vital(temperature=MATCH.t), TEST(lambda t: t >= 38.5),
    )
    def r30_meningitis(self, sev, t):
        """R-30 — RED FLAG: Severe headache + neck stiffness + fever → meningitis."""
        self._flag(
            "Possible_Meningitis",
            "Severe headache + neck stiffness + high fever — possible meningitis",
        )
        self._assert(
            "Meningitis", 0.86, "IMMEDIATE", "R-30",
            "Severe headache (≥8/10) + neck stiffness + fever≥38.5°C → suspected meningitis",
            [f"headache severity={sev}", "neck_stiffness", f"temp={t}°C"],
        )

    # ══════════════════════════════════════════════════════════════════════
    # RISK-FACTOR MODIFIER RULES — CF boosters (no new hypothesis created)
    # ══════════════════════════════════════════════════════════════════════

    @Rule(
        PatientInfo(known_conditions=MATCH.conds),
        TEST(lambda conds: "hypertension" in conds),
    )
    def rf01_hypertension_boost(self, conds):
        """RF-01 — Hypertension boosts cardiac and stroke hypotheses by +0.10 CF."""
        for diag in ["Acute_Myocardial_Infarction", "Ischemic_Stroke",
                     "Hypertensive_Crisis", "Heart_Failure"]:
            self._boost(
                diag, 0.10, "RF-01",
                "Hypertension amplifier: cardiac/stroke CF +0.10",
                "known_condition=hypertension",
            )

    @Rule(
        PatientInfo(known_conditions=MATCH.conds),
        TEST(lambda conds: "diabetes_mellitus" in conds),
    )
    def rf02_diabetes_boost(self, conds):
        """RF-02 — Diabetes mellitus boosts cardiac, sepsis, and DKA by +0.08 CF."""
        for diag in ["Acute_Myocardial_Infarction", "Sepsis",
                     "Diabetic_Ketoacidosis"]:
            self._boost(
                diag, 0.08, "RF-02",
                "Diabetes amplifier: cardiac/DKA/sepsis CF +0.08",
                "known_condition=diabetes_mellitus",
            )
