"""
AIE212 — Medical Diagnosis Expert System
Phase 4: Implementation

Package Structure
─────────────────────────────────────────────────────────
  core/
    certainty_factor.py   — CertaintyFactor  (MYCIN CF calculus)
    facts.py              — PatientInfo, Symptom, PainDetail, Vital (Fact atoms)
    diagnosis_result.py   — DiagnosisResult  (result data-class)
    working_memory.py     — WorkingMemory    (session-scoped hypothesis store)
    inference_engine.py   — InferenceEngine  (orchestrator)
    explanation_module.py — ExplanationModule (plain-language reasoning)

  knowledge/
    knowledge_base.py     — KnowledgeBase    (all IF-THEN production rules)

  interface/
    console_style.py      — ConsoleStyle     (ANSI colour helpers)
    action_library.py     — ActionLibrary    (diagnosis → action lookup)
    intake_form.py        — IntakeForm       (CLI patient intake)
    result_renderer.py    — ResultRenderer   (console output)

  utils/
    data_persistence.py   — DataPersistence  (JSON save/load)

  tests/
    test_medical_system.py — Unit tests

  main.py                 — App (entry point controller)
─────────────────────────────────────────────────────────
"""
