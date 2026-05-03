"""
AIE212 — Medical Diagnosis Expert System
interface/action_library.py

Responsibility: Static lookup mapping each diagnosis name to a list of
recommended clinical actions. Returns a generic fallback for unknown diagnoses.
"""


class ActionLibrary:
    """
    Static lookup that maps a diagnosis name to a list of recommended
    clinical actions.

    Usage
    -----
        actions = ActionLibrary.get("Acute_Myocardial_Infarction")
    """

    _ACTIONS: dict = {
        "Acute_Myocardial_Infarction": [
            "CALL EMERGENCY SERVICES IMMEDIATELY (ambulance)",
            "Administer Aspirin 300 mg if not contraindicated",
            "Keep patient calm, seated or lying — do NOT leave unattended",
            "Prepare for CPR if patient loses consciousness",
        ],
        "Ischemic_Stroke": [
            "CALL EMERGENCY SERVICES IMMEDIATELY",
            "Do NOT give food or water (aspiration risk)",
            "Note exact time of symptom onset — thrombolysis window is time-critical",
            "Keep patient still; monitor consciousness continuously",
        ],
        "Respiratory_Emergency": [
            "CALL EMERGENCY SERVICES",
            "Administer supplemental oxygen immediately",
            "Sit patient upright to aid breathing",
        ],
        "Hypertensive_Crisis": [
            "Immediate medical attention required",
            "Do NOT administer antihypertensives without medical supervision",
            "Transfer to Emergency Department now",
        ],
        "Anaphylaxis": [
            "ADMINISTER EPINEPHRINE (EpiPen) if available",
            "Call emergency services immediately",
            "Lay patient flat with legs raised (unless breathing difficulty)",
            "Monitor airway continuously",
        ],
        "Meningitis": [
            "Emergency hospital admission required",
            "Immediate IV antibiotics will be required",
            "Isolate patient pending confirmed diagnosis",
        ],
        "Diabetic_Ketoacidosis": [
            "Emergency admission for IV fluids and insulin",
            "Check blood glucose immediately",
            "Call emergency services",
        ],
        "Undifferentiated_Emergency": [
            "CALL EMERGENCY SERVICES IMMEDIATELY",
            "Maintain airway, breathing, circulation (ABC)",
        ],
        "Acute_Appendicitis": [
            "Refer to Emergency Department for surgical evaluation",
            "Nil by mouth — do NOT give food or water",
            "Do NOT administer analgesia before surgical assessment",
            "Imaging (ultrasound / CT) required",
        ],
        "Pulmonary_Embolism": [
            "Refer to Emergency Department urgently",
            "Supplemental oxygen",
            "Anticoagulation therapy to be initiated by a physician",
        ],
        "Pneumonia": [
            "Refer to GP or ED depending on severity (use CURB-65 score)",
            "Chest X-ray and blood tests required",
            "Antibiotics after cultures if bacterial origin confirmed",
        ],
        "UTI_Lower": [
            "Urine dipstick / mid-stream urine (MSU) for culture",
            "Initiate empirical antibiotic therapy",
            "Advise increased fluid intake",
            "GP visit within 24 hours",
        ],
        "Pyelonephritis": [
            "Refer to GP or ED within hours",
            "Urine culture and blood tests required",
            "IV antibiotics may be required",
        ],
        "Influenza": [
            "Rest and increase fluid intake",
            "OTC analgesics / antipyretics (paracetamol or ibuprofen)",
            "Antiviral (oseltamivir) if within 48 hours of onset and high-risk",
            "GP follow-up if symptoms worsen",
        ],
        "Possible_Influenza": [
            "Rest and fluids",
            "Monitor temperature",
            "GP visit if symptoms persist more than 5 days or worsen",
        ],
        "Tension_Headache": [
            "OTC analgesia (paracetamol or ibuprofen)",
            "Posture and ergonomic advice",
            "Stress management",
            "GP follow-up if recurrent or worsening",
        ],
        "URTI_Common_Cold": [
            "Rest and increase fluid intake",
            "OTC antihistamines / decongestants as needed",
            "No antibiotics required (viral illness)",
        ],
        "GERD": [
            "Antacids / proton pump inhibitor (PPI)",
            "Avoid trigger foods (spicy, fatty, acidic)",
            "Advise small meals; avoid lying down after eating",
            "GP follow-up if symptoms persist",
        ],
        "Unstable_Angina": [
            "Transfer to Emergency Department — urgent cardiology review",
            "Aspirin if not contraindicated",
            "Do NOT allow patient to exert themselves",
            "ECG required",
        ],
        "Infection_Present": [
            "Identify source of infection — further history required",
            "GP review recommended",
            "Blood tests may be needed",
        ],
        "Gastroenteritis": [
            "Oral rehydration solution or increased fluid intake",
            "Bland diet (BRAT: bananas, rice, applesauce, toast)",
            "Avoid dairy and fatty foods",
            "GP follow-up if symptoms persist beyond 48 hours",
        ],
        "Aortic_Dissection": [
            "CALL EMERGENCY SERVICES IMMEDIATELY",
            "Do NOT administer anticoagulants",
            "Keep systolic BP < 120 mmHg with medical supervision",
            "Prepare for emergency surgical consultation",
        ],
        "Asthma_Exacerbation": [
            "Administer bronchodilator (salbutamol) if available",
            "Consider oral corticosteroids",
            "Refer to emergency department if severe or not responding",
            "Monitor respiratory status closely",
        ],
        "Sepsis": [
            "CALL EMERGENCY SERVICES IMMEDIATELY",
            "Administer broad-spectrum antibiotics as soon as possible",
            "IV fluid resuscitation",
            "Monitor for signs of septic shock",
        ],
        "Hypertensive_Encephalopathy": [
            "Emergency blood pressure control required",
            "Neurological consultation",
            "Monitor for seizures or altered mental status",
            "Avoid rapid BP reduction to prevent cerebral hypoperfusion",
        ],
        "Viral_Arthropathy": [
            "Rest affected joints",
            "OTC analgesics / anti-inflammatories",
            "GP follow-up for persistent symptoms",
            "Consider viral serology testing if symptoms persist",
        ],
        "Labyrinthitis": [
            "Vestibular suppressants (e.g., meclizine)",
            "Rest and avoid sudden head movements",
            "ENT referral if symptoms persist beyond 1 week",
            "Consider corticosteroids in severe cases",
        ],
        "Gastritis": [
            "Proton pump inhibitors or H2 blockers",
            "Avoid NSAIDs, alcohol, and spicy foods",
            "Test for H. pylori if symptoms persist",
            "GP follow-up in 2 weeks",
        ],
        "Acute_Bronchitis": [
            "Symptomatic treatment: cough suppressants, analgesics",
            "Increase fluid intake",
            "Consider chest X-ray if symptoms persist >3 weeks",
            "Antibiotics only if bacterial infection confirmed",
        ],
    }

    _FALLBACK: list = [
        "Further clinical assessment required",
        "Consult a licensed clinician",
    ]

    @classmethod
    def get(cls, diagnosis: str) -> list:
        """
        Return the recommended action list for a given diagnosis name.

        Parameters
        ----------
        diagnosis : str — internal diagnosis identifier

        Returns
        -------
        list[str] — list of recommended action strings
        """
        return cls._ACTIONS.get(diagnosis, cls._FALLBACK)
