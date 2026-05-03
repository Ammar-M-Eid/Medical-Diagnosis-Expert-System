"""
AIE212 — Medical Diagnosis Expert System
utils/data_persistence.py

Responsibility: Save and load patient assessment sessions to/from JSON files.
"""

import json
import re
import os
from datetime import datetime


class DataPersistence:
    """
    Saves and loads patient assessment sessions as JSON files.

    Each saved file is named after the patient (e.g., 'mark.json').
    Searching for a patient by name automatically finds their file.

    Usage
    -----
        filename = DataPersistence.save_assessment(patient_data, results)
        data     = DataPersistence.load_assessment(patient_name)
    """

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Convert a patient name into a safe filesystem filename.
        Strips invalid characters, collapses spaces to underscores.
        Returns lowercase for consistency.
        """
        if not name:
            return "unnamed_patient"
        safe = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip())
        safe = re.sub(r'_+', '_', safe).strip('_').lower()
        return safe if safe else "unnamed_patient"

    @staticmethod
    def save_assessment(patient_data: dict, results: dict, filename: str = None) -> str:
        """
        Serialise a patient assessment to a JSON file named after the patient.

        Parameters
        ----------
        patient_data : dict  — original intake form data (must contain 'name')
        results      : dict  — output from InferenceEngine.run()
        filename     : str | None — override target filename; auto-generated from patient name if None

        Returns
        -------
        str — path to the saved file
        """
        if filename is None:
            patient_name = patient_data.get("name", "").strip()
            safe_name = DataPersistence._sanitize_filename(patient_name)
            filename = f"{safe_name}.json"

        def safe_dict(obj):
            """Safely convert an object to a serializable dict."""
            if obj is None:
                return None
            try:
                return obj.__dict__
            except AttributeError:
                return obj

        def safe_list(objects):
            """Safely convert a list of objects."""
            return [safe_dict(item) for item in objects]

        payload = {
            "timestamp"    : datetime.now().isoformat(),
            "patient_data": patient_data,
            "results": {
                "primary"      : safe_dict(results.get("primary")),
                "differentials": safe_list(results.get("differentials", [])),
                "red_flags"    : results.get("red_flags", []),
                "trace"        : results.get("trace", []),
            },
        }

        try:
            with open(filename, "w") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save assessment: {e}")
            raise

        return filename

    @staticmethod
    def load_assessment(patient_name: str) -> dict:
        """
        Load a patient assessment by name (without .json extension).

        Searches for '<sanitized_name>.json' in the current directory.

        Parameters
        ----------
        patient_name : str — patient name (e.g., 'mark'); '.json' is added automatically

        Returns
        -------
        dict — the full saved assessment payload

        Raises
        ------
        FileNotFoundError — if the patient's file does not exist
        json.JSONDecodeError — if the file is malformed
        """
        safe_name = DataPersistence._sanitize_filename(patient_name)
        filename = f"{safe_name}.json"

        if not os.path.exists(filename):
            raise FileNotFoundError(f"No assessment found for patient '{patient_name}'")

        with open(filename, "r") as f:
            return json.load(f)

    @staticmethod
    def list_saved_patients() -> list:
        """
        Return a list of all saved patient names (without extensions).
        """
        patients = []
        if os.path.exists("."):
            for fname in os.listdir("."):
                if fname.endswith(".json"):
                    patients.append(fname[:-5])  # strip .json
        return sorted(patients)

    @staticmethod
    def delete_assessment(patient_name: str) -> None:
        """
        Delete a saved patient assessment by name.

        Parameters
        ----------
        patient_name : str — patient name used when the file was saved

        Raises
        ------
        FileNotFoundError — if no matching assessment file exists
        OSError           — if the file cannot be removed
        """
        safe_name = DataPersistence._sanitize_filename(patient_name)
        filename = f"{safe_name}.json"
        if not os.path.exists(filename):
            raise FileNotFoundError(
                f"No assessment found for patient '{patient_name}'"
            )
        os.remove(filename)
