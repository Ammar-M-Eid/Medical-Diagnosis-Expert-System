# Medical Diagnosis Expert System - Testing and Evaluation Report

## Purpose

This report documents realistic test scenarios for the Medical Diagnosis Expert System, evaluates output correctness and reasoning consistency, analyzes limitations, and demonstrates how the system explains its decisions.

The tests were run from:

```powershell
cd A:\MyGitHub\KBS
.\.venv\Scripts\activate
python -m pytest -q
```

Automated regression result:

```text
4 passed
```

A separate scenario sweep was also run directly through `InferenceEngine` and `ExplanationModule` to evaluate broader behavior.

## Comparison Against Project Phase Documents

After the first evaluation draft, the report was compared against the local project PDFs:

- `docs/ph 1.pdf` - problem analysis, realistic diagnostic scenarios, scope, and limitations.
- `docs/ph2.pdf` - solution approach using a Rule-Based Expert System and Certainty Factors.
- `docs/ph 3.pdf` - design requirements for transparent explanations, rule traces, CF tracking, differential justification, conflict resolution, and red-flag explanations.

The evaluation was then adjusted to align with those documents.

Document alignment:

| Project document requirement | Where it is addressed in this report |
| --- | --- |
| Phase 1 realistic scenarios: common cold/URTI, tension headache, lower UTI, appendicitis, acute MI, stroke | Covered in the scenario table and detailed scenario notes |
| Phase 1 scope: adult triage, symptoms/vitals, red flags, urgency classes, differentials, transparent reasoning | Covered in system workflow, scenario evaluation, and limitations |
| Phase 1 limitations: no definitive diagnosis, no physical exam, no labs/imaging, no pediatric coverage, no prescribing authority, no continuous monitoring | Covered in System Limitations |
| Phase 2 RBES approach | Covered in How The System Works and Reasoning Consistency Analysis |
| Phase 2 Certainty Factor mechanism | Covered in outputs, CF table values, modifier examples, and audit trace examples |
| Phase 3 explanation design: rule IDs, matched facts, conclusion, CF, summary explanation, detailed trace | Covered in Demonstration Of Decision Explanation |
| Phase 3 conflict handling: competing diagnoses prioritized by urgency, CF, specificity, and red flags | Covered in Correctness Analysis and Reasoning Consistency Analysis |

## How The System Works

The system uses a rule-based expert-system architecture.

1. The user enters demographics, medical history, vital signs, symptoms, and pain details.
2. `InferenceEngine` converts the patient dictionary into facts.
3. `KnowledgeBase` evaluates those facts using `experta` production rules.
4. Matching rules assert diagnoses with certainty factors.
5. Risk-factor modifier rules can boost certainty factors.
6. Red-flag rules add safety-critical alerts.
7. `WorkingMemory` combines repeated certainty factors and ranks results by urgency first, then certainty factor.
8. `ExplanationModule` produces a plain-language explanation and a detailed audit trace.

## Evaluation Criteria

Correctness was evaluated by comparing the primary diagnosis against the expected diagnosis for each clinical scenario.

Reasoning consistency was evaluated by checking that:

- the fired rules matched the supplied facts;
- certainty factors were applied consistently;
- red flags appeared when emergency rules fired;
- urgency outranked certainty where appropriate;
- explanation text matched the same rule trace used to produce the result.

## Scenario Results Summary

| ID | Scenario | Expected Primary | Actual Primary | CF | Urgency | Result |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | Common cold / URTI | URTI_Common_Cold | URTI_Common_Cold | 0.78 | NON_URGENT | PASS |
| D2 | Tension headache | Tension_Headache | Tension_Headache | 0.72 | NON_URGENT | PASS |
| S1 | Acute myocardial infarction | Acute_Myocardial_Infarction | Acute_Myocardial_Infarction | 0.955 | IMMEDIATE | PASS |
| S2 | Lower UTI | UTI_Lower | UTI_Lower | 0.82 | SEMI_URGENT | PASS |
| S3 | Sepsis | Sepsis | Sepsis | 0.88 | IMMEDIATE | PASS |
| S4 | Asthma exacerbation | Asthma_Exacerbation | Asthma_Exacerbation | 0.80 | URGENT | PASS |
| S5 | Ischemic stroke | Ischemic_Stroke | Ischemic_Stroke | 0.973 | IMMEDIATE | PASS |
| S6 | Pneumonia | Pneumonia | Pneumonia | 0.76 | URGENT | PASS |
| S7 | GERD-like chest pain | GERD | GERD | 0.65 | NON_URGENT | PASS |
| S8 | Meningitis | Meningitis | Meningitis | 0.86 | IMMEDIATE | PASS |
| S9 | Acute appendicitis | Acute_Appendicitis | Acute_Appendicitis | 0.78 | URGENT | PASS |
| S10 | Low-data normal vitals | None | None | N/A | N/A | PASS |

Overall scenario sweep result after comparing against the phase documents: 12/12 expected primary outcomes.

## Detailed Scenario Evaluation

### D1 - Common Cold / URTI

This scenario is based on the common cold / URTI example in Phase 1 Section 1.4.

Input highlights:

- Age 28
- Runny nose
- Sore throat
- Temperature 37.4 C
- Normal vital signs

Expected output from Phase 1: probable URTI / common cold, Non-Urgent, High confidence.

Actual output:

```text
Primary: URTI Common Cold
CF: 0.78
Confidence: High
Urgency: NON_URGENT
Rules fired: R-07
Differentials: None
Red flags: None
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-07 matched runny nose, sore throat, and afebrile temperature.
- The output matched the Phase 1 expected response: common cold / URTI with non-urgent urgency.

### D2 - Tension Headache

This scenario is based on the tension headache example in Phase 1 Section 1.4.

Input highlights:

- Age 35
- Headache severity 4/10
- No fever
- No neurological symptoms
- No neck stiffness

Expected output from Phase 1: tension-type headache, Non-Urgent.

Actual output:

```text
Primary: Tension Headache
CF: 0.72
Confidence: High
Urgency: NON_URGENT
Rules fired: R-06
Differentials: None
Red flags: None
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-06 matched mild/moderate headache and the absence of fever, neck stiffness, and neurological warning signs.
- The output matched the Phase 1 expected response: non-urgent tension headache.

### S1 - Acute Myocardial Infarction

Input highlights:

- Age 58 male
- Known hypertension
- Crushing chest pain
- Left-arm radiation
- Diaphoresis
- Shortness of breath
- HR 102 bpm
- SpO2 94%

Expected output: `Acute_Myocardial_Infarction`

Actual output:

```text
Primary: Acute Myocardial Infarction
CF: 0.955
Confidence: Very High
Urgency: IMMEDIATE
Rules fired: R-08
Differential: Pulmonary Embolism, CF=0.65, URGENT
Red flag: Suspected_Acute_MI
```

Correctness evaluation: PASS. The system correctly selected acute MI because the input matched the acute MI rule pattern.

Reasoning consistency:

- R-08 matched age >= 40, crushing chest pain, left-arm radiation, diaphoresis, and abnormal vitals.
- RF-01 boosted cardiac certainty because hypertension was present.
- A red flag was triggered because suspected acute MI is emergency-level.
- Pulmonary embolism appeared as a differential because sudden chest pain, shortness of breath, and tachycardia also matched R-18.

Audit trace excerpt:

```text
FINAL RANKING
1. PRIMARY: Acute Myocardial Infarction | CF=0.955 | confidence=Very High | urgency=IMMEDIATE | rules=R-08
2. DIFFERENTIAL #1: Pulmonary Embolism | CF=0.65 | confidence=Medium | urgency=URGENT | rules=R-18

MATCHED DIAGNOSIS RULES
Acute Myocardial Infarction
  [R-08] Age>=40 + crushing/pressure chest pain + left-arm/jaw radiation + diaphoresis + abnormal vitals
      evidence: age=58
      evidence: pain=crushing
      evidence: radiation=left_arm
      evidence: diaphoresis
      evidence: spo2=94
      evidence: HR=102

CERTAINTY MODIFIERS
[RF-01] Hypertension amplifier: cardiac/stroke CF +0.10
    effect: Acute_Myocardial_Infarction CF boosted 0.950 -> 0.9550
```

### S2 - Lower UTI

Input highlights:

- 24-year-old female
- Dysuria
- Urinary frequency
- Duration 2 days
- Temperature 37.8 C
- No flank pain

Expected output: `UTI_Lower`

Actual output:

```text
Primary: UTI Lower
CF: 0.82
Confidence: High
Urgency: SEMI_URGENT
Rules fired: R-22
Differentials: None
Red flags: None
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-22 requires female sex, dysuria, urinary frequency, duration >= 1 day, temperature below 38.5 C, and no flank pain.
- No red flag was expected because the scenario does not suggest upper UTI or sepsis.
- No differential was produced because no other rule pattern matched the facts.

### S3 - Sepsis

Input highlights:

- Fever
- Chills
- Temperature 39.0 C
- HR 110 bpm
- SBP 90 mmHg

Expected output: `Sepsis`

Actual output:

```text
Primary: Sepsis
CF: 0.88
Confidence: Very High
Urgency: IMMEDIATE
Rules fired: R-13
Differential: Infection Present, CF=0.55, SEMI_URGENT
Red flag: Suspected_Sepsis
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-13 matched fever, chills, tachycardia, and hypotension.
- R-01 also matched elevated temperature and produced a lower-priority infection hypothesis.
- The primary diagnosis was sepsis because IMMEDIATE urgency and higher specificity outranked generic infection.

### S4 - Asthma Exacerbation

Input highlights:

- Known asthma
- Shortness of breath
- Wheezing
- Respiratory rate 25/min
- SpO2 94%

Expected output: `Asthma_Exacerbation`

Actual output:

```text
Primary: Asthma Exacerbation
CF: 0.80
Confidence: High
Urgency: URGENT
Rules fired: R-12
Differentials: None
Red flags: None
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-12 matched shortness of breath, wheezing, known asthma, and elevated respiratory rate.
- No critical SpO2 red flag was expected because SpO2 was 94%, not below 90%.

### S5 - Ischemic Stroke

Input highlights:

- Age 67 male
- Known hypertension
- Sudden facial drooping
- Sudden arm weakness
- Sudden slurred speech

Expected output: `Ischemic_Stroke`

Actual output:

```text
Primary: Ischemic Stroke
CF: 0.973
Confidence: Very High
Urgency: IMMEDIATE
Rules fired: R-14
Differentials: None
Red flag: Suspected_Ischemic_Stroke
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-14 matched FAST-positive stroke symptoms with sudden onset.
- RF-01 boosted stroke certainty because hypertension was present.
- The red flag is consistent with stroke triage safety.

### S6 - Pneumonia

Input highlights:

- Elderly patient
- Fever
- Cough
- Shortness of breath
- Temperature 38.8 C
- Respiratory rate 24/min

Expected output: `Pneumonia`

Actual output:

```text
Primary: Pneumonia
CF: 0.76
Confidence: High
Urgency: URGENT
Rules fired: R-25
Differentials:
- Infection Present, CF=0.55, SEMI_URGENT
- Possible Influenza, CF=0.50, NON_URGENT
Red flags: None
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-25 matched fever, cough, shortness of breath, high temperature, and elevated respiratory rate.
- R-01 and R-03 also matched because fever and cough can support generic infection and possible influenza.
- Pneumonia outranked both because it was more specific and had higher urgency.

### S7 - GERD-Like Chest Pain

Input highlights:

- Age 35 male
- Burning chest pain
- No radiation
- No diaphoresis
- Normal vitals

Expected output: `GERD`

Actual output:

```text
Primary: GERD
CF: 0.65
Confidence: Medium
Urgency: NON_URGENT
Rules fired: R-27
Differentials: None
Red flags: None
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-27 matched burning chest pain, no radiation, no diaphoresis, and age under 55.
- No cardiac red flag fired because the pain pattern did not match MI or aortic dissection rules.

### S8 - Meningitis

Input highlights:

- Severe headache
- Neck stiffness
- Fever 39.1 C

Expected output: `Meningitis`

Actual output:

```text
Primary: Meningitis
CF: 0.86
Confidence: Very High
Urgency: IMMEDIATE
Rules fired: R-30
Differential: Infection Present, CF=0.55, SEMI_URGENT
Red flag: Possible_Meningitis
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-30 matched severe headache, neck stiffness, and high fever.
- R-01 also matched elevated temperature.
- Meningitis outranked generic infection due to IMMEDIATE urgency and stronger CF.

### S9 - Acute Appendicitis

Input highlights:

- Right lower quadrant pain severity 8/10
- Nausea
- Low-grade fever 38.0 C

Expected output: `Acute_Appendicitis`

Actual output:

```text
Primary: Acute Appendicitis
CF: 0.78
Confidence: High
Urgency: URGENT
Rules fired: R-24
Differentials: None
Red flags: None
```

Correctness evaluation: PASS.

Reasoning consistency:

- R-24 matched RLQ pain severity >= 5, nausea, and low-grade fever.
- No red flag was configured for appendicitis in the current knowledge base, so urgency remained URGENT rather than IMMEDIATE.

### S10 - Low-Data Normal Vitals

Input highlights:

- Normal vitals
- No symptoms
- No abnormal history

Expected output: no diagnosis

Actual output:

```text
Primary: None
Differentials: None
Red flags: None
Trace: No rules fired - insufficient input data provided.
```

Correctness evaluation: PASS.

Reasoning consistency:

- No facts matched diagnosis-producing rules.
- The system correctly avoided inventing a diagnosis.
- The explanation recommends adding symptoms, abnormal vitals, or pain details.

## Correctness Analysis

The system produced the expected primary diagnosis for all 12 scenario-sweep cases after comparison with the phase documents. The outputs were clinically plausible within the limited rule base. Emergency presentations such as acute MI, sepsis, ischemic stroke, and meningitis were assigned IMMEDIATE urgency and red flags. Non-emergency or lower-acuity cases such as common cold, tension headache, GERD, and lower UTI were not over-escalated.

The system also handled competing diagnoses appropriately. For example:

- Acute MI and pulmonary embolism both matched parts of the chest-pain scenario, but acute MI ranked first because it had IMMEDIATE urgency and higher CF.
- Pneumonia, generic infection, and possible influenza all matched respiratory infection facts, but pneumonia ranked first because it was more specific and urgent.
- Sepsis and infection-present both matched fever-related facts, but sepsis ranked first because hypotension and tachycardia indicated an emergency.

## Reasoning Consistency Analysis

The reasoning was consistent across scenarios:

- The same input facts produced the same fired rules on repeated runs.
- Each explanation referenced the same rule IDs that appeared in the audit trace.
- Red flags appeared only when red-flag rules fired.
- Risk-factor modifiers only adjusted existing hypotheses; they did not create diagnoses by themselves.
- Ranking followed the system design: urgency first, certainty factor second.

Example consistency check:

In S1, hypertension did not create acute MI. R-08 created acute MI, then RF-01 boosted the CF from 0.950 to 0.955. This is consistent with the modifier-rule design.

## Demonstration Of Decision Explanation

After running an assessment in the GUI:

1. The results page shows the primary diagnosis, confidence, urgency, and differentials.
2. The section "HOW THE SYSTEM DETERMINED THE ILLNESS" explains the process in plain language.
3. The "Show Full Trace" button expands the detailed audit trace.

The audit trace now contains:

- `FINAL RANKING`
- `MATCHED DIAGNOSIS RULES`
- `CERTAINTY MODIFIERS`
- `RED FLAGS`
- `CHRONOLOGICAL RULE LOG`

Example from S1:

```text
FINAL RANKING
1. PRIMARY: Acute Myocardial Infarction | CF=0.955 | confidence=Very High | urgency=IMMEDIATE | rules=R-08
2. DIFFERENTIAL #1: Pulmonary Embolism | CF=0.65 | confidence=Medium | urgency=URGENT | rules=R-18

MATCHED DIAGNOSIS RULES
Acute Myocardial Infarction
  [R-08] Age>=40 + crushing/pressure chest pain + left-arm/jaw radiation + diaphoresis + abnormal vitals
      evidence: age=58
      evidence: pain=crushing
      evidence: radiation=left_arm
      evidence: diaphoresis
      evidence: spo2=94
      evidence: HR=102

CERTAINTY MODIFIERS
[RF-01] Hypertension amplifier: cardiac/stroke CF +0.10
    matched: known_condition=hypertension
    effect: Acute_Myocardial_Infarction CF boosted 0.950 -> 0.9550

RED FLAGS
- Suspected Acute MI
    reason: Age 58, crushing chest pain -> left_arm, diaphoresis, SpO2=94%, HR=102bpm
```

This demonstrates that the system does not only output a diagnosis; it shows the evidence, rule IDs, certainty changes, red flags, and ranking logic behind that diagnosis.

## System Limitations

1. Limited clinical scope

The knowledge base contains a fixed set of rules. It cannot diagnose conditions outside those rules.

2. No laboratory or imaging data

The system does not use ECG, troponin, CBC, urinalysis, cultures, imaging, or other diagnostic tests. For example, acute MI and pneumonia can only be inferred from symptoms and vitals.

3. Rule thresholds are simplified

Cutoffs such as HR > 100, SpO2 < 90, or temperature >= 38.5 are simplified educational thresholds. Real triage protocols may be more nuanced.

4. No probabilistic population modeling

Certainty factors are manually assigned. They are not learned from clinical datasets and should not be interpreted as calibrated probabilities.

5. Limited conflict resolution

The system ranks by urgency and CF, but it does not perform deep differential diagnosis reasoning or exclusion based on negative findings beyond explicit `NOT(...)` rule conditions.

6. Input quality sensitivity

Incorrect or incomplete user input can prevent rules from firing or cause the wrong rule to fire.

7. No medication, allergy, pregnancy, or immunosuppression logic

Important clinical factors such as pregnancy, anticoagulant use, allergies, immune status, and medication history are not currently represented.

8. Not a clinical authority

The system is a decision-support demonstration and must not replace professional clinical judgment.

## Recommendations For Future Improvement

- Add more structured clinical inputs: allergies, pregnancy status, medications, immunosuppression, recent surgery, and exposure history.
- Add test/lab result facts such as ECG, troponin, WBC, urinalysis, and chest X-ray findings.
- Add more differential diagnosis rules for overlapping presentations.
- Add validation rules for physiologically impossible vitals.
- Add a formal confusion matrix once a labeled clinical dataset is available.
- Add automated scenario tests for every rule R-01 through R-30 and RF-01 through RF-02.
- Add user-facing warnings when insufficient data leads to no diagnosis.

## Conclusion

The system performed correctly on the selected diverse scenarios and produced consistent explanations aligned with the fired rules. Its strongest feature is transparent reasoning: every diagnosis can be traced back to matched facts, rule IDs, certainty factors, risk modifiers, and red flags. Its main limitation is that it remains a fixed educational rule base, not a comprehensive or validated medical diagnostic system.
