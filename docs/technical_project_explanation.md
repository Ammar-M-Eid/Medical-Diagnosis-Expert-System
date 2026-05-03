# Medical Diagnosis Expert System - Technical Explanation

## Overview

This project is a Python knowledge-based medical triage and preliminary diagnosis system. It uses a rule-based expert system architecture with certainty factors, a graphical interface built with `customtkinter`, and JSON persistence for saved patient assessments.

The system has two runnable entry points:

- `gui_app.py` - graphical desktop application.
- `main.py` - console-based interactive application.

The main technical goal is transparency: the system does not only output a diagnosis, it records which rules fired, which patient facts matched, how certainty factors changed, which red flags were triggered, and why the final diagnosis was ranked first.

## Project Structure

```text
KBS/
+-- core/
|   +-- certainty_factor.py
|   +-- diagnosis_result.py
|   +-- explanation_module.py
|   +-- facts.py
|   +-- inference_engine.py
|   +-- working_memory.py
+-- knowledge/
|   +-- knowledge_base.py
+-- interface/
|   +-- action_library.py
|   +-- console_style.py
|   +-- intake_form.py
|   +-- result_renderer.py
+-- utils/
|   +-- data_persistence.py
+-- tests/
|   +-- test_medical_system.py
+-- gui_app.py
+-- main.py
+-- requirements.txt
+-- docs/
```

## Runtime Dependencies

The project dependencies are listed in `requirements.txt`:

```text
experta==1.9.4
customtkinter==5.2.2
pytest==9.0.3
```

Dependency roles:

- `experta`: rule engine used for facts, rules, and forward chaining.
- `customtkinter`: GUI framework.
- `pytest`: test runner.

## High-Level Architecture

The system follows a layered design:

```text
User Input
   |
   v
GUI or Console Interface
   |
   v
InferenceEngine
   |
   v
Fact Creation
   |
   v
KnowledgeBase rules
   |
   v
WorkingMemory
   |
   v
Ranked DiagnosisResult objects
   |
   v
ExplanationModule + ActionLibrary
   |
   v
Results UI / Console Output / JSON Save
```

The most important separation is between:

- the interface layer, which collects and displays data;
- the inference layer, which performs reasoning;
- the knowledge layer, which stores medical rules;
- the explanation layer, which translates raw rule traces into readable reasoning.

## Data Model

Patient input is represented as a dictionary. A typical assessment includes:

```python
{
    "age": 58,
    "sex": "male",
    "known_conditions": ["hypertension"],
    "smoking": True,
    "alcohol": False,
    "temperature": 37.0,
    "heart_rate": 102,
    "systolic_bp": 140,
    "diastolic_bp": 90,
    "spo2": 94,
    "resp_rate": 18,
    "consciousness": "alert",
    "symptoms": [
        {
            "name": "chest_pain",
            "severity": 9,
            "duration_days": 0.1,
            "onset": "sudden",
            "progression": "worsening"
        }
    ],
    "pain_detail": {
        "character": "crushing",
        "radiation": "left_arm"
    }
}
```

## Fact Classes

`core/facts.py` defines the `experta.Fact` subclasses used by the rule engine:

- `PatientInfo`: age, sex, chronic conditions, smoking, alcohol.
- `Symptom`: symptom name, severity, duration, onset, progression.
- `PainDetail`: pain character and radiation.
- `Vital`: temperature, HR, BP, SpO2, respiratory rate, consciousness.

These classes are intentionally simple because `experta` stores fact fields dynamically.

## Inference Engine

`core/inference_engine.py` is the orchestration layer.

Its main method is:

```python
InferenceEngine.run(patient_data: dict) -> dict
```

Execution steps:

1. Create a fresh `WorkingMemory`.
2. Create a `KnowledgeBase` and inject the working memory.
3. Reset the knowledge base.
4. Convert patient data into facts.
5. Declare all facts into the rule engine.
6. Run the forward-chaining engine.
7. Ask `WorkingMemory` for ranked results.
8. Return primary diagnosis, differentials, red flags, and trace.

The returned result dictionary has this shape:

```python
{
    "primary": DiagnosisResult | None,
    "differentials": list[DiagnosisResult],
    "red_flags": list[dict],
    "trace": list[dict]
}
```

## Knowledge Base

`knowledge/knowledge_base.py` contains the production rules. It inherits from `experta.KnowledgeEngine`.

The rules are grouped into:

- Simple rules: single vital/symptom to initial hypothesis.
- Complex rules: multiple facts to specific diagnoses.
- Risk-factor modifier rules: boost certainty factors for existing hypotheses.

Example rule behavior:

```text
IF age >= 40
AND chest pain
AND crushing/pressure pain
AND radiation to left arm or jaw
AND diaphoresis
AND SpO2 < 95 OR HR > 100
THEN Acute_Myocardial_Infarction
CF = 0.95
Urgency = IMMEDIATE
Red flag = Suspected_Acute_MI
```

Internally, rules call helper methods:

- `_assert(...)`: sends a diagnosis hypothesis to `WorkingMemory`.
- `_flag(...)`: registers a red flag.
- `_boost(...)`: applies a certainty-factor boost to an existing hypothesis.

## Working Memory

`core/working_memory.py` stores all conclusions during one assessment.

It tracks:

- diagnostic hypotheses;
- combined certainty factors;
- urgency levels;
- rule IDs that contributed to each hypothesis;
- red flags;
- raw inference trace entries.

Each trace entry contains:

```python
{
    "rule_id": "R-08",
    "description": "...",
    "facts_matched": ["age=58", "pain=crushing"],
    "conclusion": "Acute_Myocardial_Infarction [CF=0.95, urgency=IMMEDIATE]"
}
```

This is what enables the explanation module to show transparent reasoning.

## Certainty Factor Logic

`core/certainty_factor.py` implements MYCIN-style certainty factor utilities.

When two independent rules support the same diagnosis, the CF is combined using:

```text
CF_combined = CF1 + CF2 * (1 - CF1)
```

Example:

```text
Existing CF = 0.95
Risk boost = 0.10
Combined CF = 0.95 + 0.10 * (1 - 0.95)
Combined CF = 0.955
```

Confidence labels:

| CF Range | Label |
| --- | --- |
| >= 0.85 | Very High |
| >= 0.70 | High |
| >= 0.50 | Medium |
| < 0.50 | Low |

Urgency ranking:

| Urgency | Rank |
| --- | --- |
| IMMEDIATE | 4 |
| URGENT | 3 |
| SEMI_URGENT | 2 |
| NON_URGENT | 1 |

Ranking uses urgency first, then certainty factor.

## Diagnosis Result Object

`core/diagnosis_result.py` defines the immutable result object:

```python
DiagnosisResult(
    diagnosis="Acute_Myocardial_Infarction",
    cf=0.955,
    confidence="Very High",
    urgency="IMMEDIATE",
    rules_fired=["R-08"]
)
```

The `display_name` property replaces underscores with spaces for UI output.

## Explanation Module

`core/explanation_module.py` turns raw trace data into human-readable reasoning.

It provides:

- `summary(results)`: plain-language explanation.
- `detailed(results)`: structured reasoning audit trace.
- `explain_conflicts(results)`: notes about competing diagnoses.

The detailed audit trace includes:

- final ranking;
- matched diagnosis rules;
- evidence matched by each rule;
- certainty modifiers;
- red flags;
- chronological rule log.

This module is important because it satisfies the project requirement for explainability. The system can answer:

- Why this diagnosis?
- Which facts matched?
- Which rule fired?
- What was the CF?
- Why was it urgent?
- What alternatives were considered?

## Clinical Action Library

`interface/action_library.py` maps diagnosis IDs to recommended actions.

Example:

```python
ActionLibrary.get("Acute_Myocardial_Infarction")
```

Returns actions such as:

- call emergency services;
- aspirin if not contraindicated;
- keep patient calm and monitored.

Unknown diagnoses use a fallback:

```text
Further clinical assessment required
Consult a licensed clinician
```

## GUI Architecture

`gui_app.py` implements the graphical interface using `customtkinter`.

Important GUI classes:

- `GUIApp`: main application window and navigation controller.
- `Sidebar`: navigation between assessment and saved assessments.
- `AssessmentView`: full patient intake form.
- `DemographicsSection`: name, age, sex.
- `HistorySection`: chronic conditions and lifestyle factors.
- `VitalsSection`: vital signs with status indicators.
- `SymptomsSection`: symptom selection and per-symptom details.
- `PainDetailSection`: pain character and radiation.
- `ResultsView`: displays diagnosis, actions, red flags, explanations.
- `SavedPatientsView`: loads and deletes saved assessments.
- `_ExplanationCard`: shows reasoning summary and expandable audit trace.

GUI flow:

```text
AssessmentView
   |
   v Run Assessment
GUIApp._run_assessment()
   |
   v
InferenceEngine.run()
   |
   v
ResultsView
   |
   v
Primary diagnosis + differentials + actions + explanation
```

The `New Assessment` button rebuilds a fresh `AssessmentView`.

## Console Application

`main.py` provides a console version of the same workflow.

It uses:

- `interface/intake_form.py` to collect patient data;
- `core/inference_engine.py` to run diagnosis;
- `interface/result_renderer.py` to print results;
- `utils/data_persistence.py` to save/load assessments.

It also configures UTF-8 console output to avoid Windows encoding crashes when printing non-ASCII banner characters.

## Persistence

`utils/data_persistence.py` saves assessments as JSON files in the project root.

Saved file format:

```json
{
  "timestamp": "...",
  "patient_data": {},
  "results": {
    "primary": {},
    "differentials": [],
    "red_flags": [],
    "trace": []
  }
}
```

Filename behavior:

- patient names are sanitized;
- spaces and invalid characters become underscores;
- empty names become `unnamed_patient.json`.

The GUI can list, load, preview, and delete saved assessments.

## Testing

`tests/test_medical_system.py` contains regression tests for four important scenarios:

- acute myocardial infarction;
- lower UTI;
- sepsis;
- asthma exacerbation.

Run tests with:

```powershell
python -m pytest -q
```

Current result:

```text
4 passed
```

## Error Fixes Applied During Development

Several runtime issues were fixed:

1. Broken virtual environment

The existing `.venv` pointed to a missing Python path. It was rebuilt with the local Python installation.

2. Windows console encoding crash

`main.py` now configures stdout/stderr as UTF-8 before printing the banner.

3. `configure().pack()` GUI crash

Tkinter/customtkinter `configure()` returns `None`. Divider configuration was split into separate `configure()` and `pack()` calls.

4. Invalid `border_color="transparent"`

`customtkinter` does not accept transparent border colors. Non-urgent action rows now use the background color as border color.

5. Duplicate button `height` argument

The shared `_btn()` helper now allows callers to override height safely.

6. `New Assessment` navigation bug

The results page now rebuilds the form directly instead of relying on sidebar state.

7. Trace readability

The trace was upgraded from a raw chronological log into a structured audit.

## Current Technical Limitations

1. The rule base is fixed and manually authored.
2. Certainty factors are expert-assigned, not statistically calibrated.
3. There is no database; saved assessments are JSON files in the project root.
4. GUI validation is basic and can be expanded.
5. The system does not support pediatric-specific logic.
6. The system does not process lab tests, ECGs, imaging, or physical exam findings unless manually encoded as inputs.
7. The GUI and console share the same inference engine but use separate input/rendering code.
8. Generated patient JSON files can clutter the project root unless moved to a dedicated data folder in a future version.

## Suggested Future Technical Improvements

- Move saved assessments into a `data/assessments/` folder.
- Add stronger input validation for impossible vitals.
- Add test coverage for every rule R-01 through R-30.
- Add automated GUI smoke tests.
- Add a rule registry table to document all rule IDs and expected outputs.
- Add export-to-PDF for assessment results.
- Add search/filter features for saved patients.
- Add a configuration file for paths, color themes, and clinical thresholds.

## Summary

Technically, the project is a transparent rule-based expert system with a clear data pipeline:

```text
Input dictionary -> Experta facts -> Rule firing -> Working memory -> Ranked results -> Explanation and UI rendering
```

The design is suitable for an educational knowledge-based systems project because it demonstrates:

- symbolic medical rules;
- forward chaining;
- certainty factor reasoning;
- red-flag prioritization;
- differential diagnosis ranking;
- explainable decisions;
- GUI and console interaction;
- JSON persistence;
- automated regression testing.
