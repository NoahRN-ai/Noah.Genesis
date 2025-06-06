import json
import datetime
from typing import Dict, Any, List

# Service dependencies (will be properly injected in a FastAPI app)
# from .firestore_service import FirestoreService, PatientProfile # Or specific functions
# from .alloydb_data_service import AlloyDBDataService
# from .patient_summary_service import PatientSummaryService
# from backend.app.models.firestore_models import PatientProfile # For direct type hint

class ReportDataService:
    # --- Mock Data (can be loaded from config or be class attributes) ---
    MOCK_LAB_RESULTS_STATIC = {
        "patientA123": {"abnormal_results": ["K+ 3.1 mmol/L (Low)", "BNP 1250 pg/mL (High)"], "pending_results": ["Troponin Q6H"]},
        "patientB456": {"abnormal_results": ["WBC 15.5 x10^9/L (High)"], "pending_results": ["Sputum Culture"]}
    }
    MOCK_IV_ACCESS_DETAILS_STATIC = {
        "patientA123": [{"site": "Left Forearm", "type": "PIV 20G", "patency": "Flushes well"}],
        "patientB456": [{"site": "Right Antecubital", "type": "PIV 22G", "patency": "Sluggish"}]
    }

    def __init__(self,
                 firestore_service: Any, # Placeholder for actual FirestoreService instance
                 alloydb_service: Any, # Placeholder for actual AlloyDBDataService instance
                 patient_summary_service: Any # Placeholder for actual PatientSummaryService instance
                ):
        self.firestore_service = firestore_service
        self.alloydb_service = alloydb_service
        self.patient_summary_service = patient_summary_service
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (ReportDataService): Initialized.")
        # You could also load MOCK_LAB_RESULTS etc. from a config file here if preferred

    async def get_section_i_system_overview(self) -> Dict[str, Any]:
        """Populates data for Section I: System Overview."""
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (ReportDataService): Populating Section I - System Overview")
        now = datetime.datetime.utcnow()
        current_shift_name = "Day Shift"
        current_shift_times = "07:00 - 19:00"
        if 19 <= now.hour or now.hour < 7:
            current_shift_name = "Night Shift"
            current_shift_times = "19:00 - 07:00"

        reporting_nurse_name = "AI Nurse Agent"
        receiving_nurses_list = ["Assigned Floor Nurse 1", "Assigned Floor Nurse 2"]
        unit_name = "Medical-Surgical Ward A"
        unit_capacity = 20
        current_census = 18
        admissions_expected = 2
        discharges_expected = 1

        unit_census_overview_str = (
            f"Unit: {unit_name} | Capacity: {unit_capacity} | "
            f"Current Census: {current_census} | Admissions Expected: {admissions_expected} | "
            f"Discharges Expected: {discharges_expected}"
        )
        urgent_unit_alerts_list = [
            "Room 305: Patient awaiting urgent lab results (Critical Potassium).",
            "Unit: Low stock of IV pumps, request submitted to central supply."
        ]
        return {
            "current_date_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "shift_info": f"{now.strftime('%A, %B %d, %Y')} - {current_shift_name} ({current_shift_times})",
            "reporting_nurse": reporting_nurse_name,
            "receiving_nurses": receiving_nurses_list,
            "unit_census_overview": unit_census_overview_str,
            "urgent_unit_alerts": urgent_unit_alerts_list
        }

    async def get_section_ii_patient_identification(self, patient_id: str) -> Dict[str, Any]:
        """Populates data for Section II: Patient Identification."""
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (ReportDataService): Populating Section II - Patient ID for {patient_id}")
        profile_model = await self.firestore_service.get_patient_profile(patient_id)
        if not profile_model:
            return {"error": f"Patient ID {patient_id} not found."}

        profile = profile_model.model_dump(exclude_none=True)
        mock_extended_details = {
            profile_model.patient_id: {
                "room_no": f"Room {profile_model.patient_id[-3:]}",
                "consulting_physicians": ["Dr. Alpha (Cardiology)", "Dr. Beta (General)"],
            }
        }
        final_profile_data = profile.copy()
        final_profile_data.update(mock_extended_details.get(profile_model.patient_id, {}))

        emergency_contact_str = "N/A"
        if final_profile_data.get("emergency_contacts"):
            first_contact = final_profile_data["emergency_contacts"][0]
            contact_name = first_contact.get("name", "N/A")
            contact_phone = first_contact.get("phone", "N/A")
            emergency_contact_str = f"{contact_name} ({contact_phone})"

        patient_name_str = "N/A"
        if final_profile_data.get("name"):
            primary_name_info = final_profile_data["name"][0]
            patient_name_str = primary_name_info.get("text") or \
                               f"{' '.join(primary_name_info.get('given', []))} {primary_name_info.get('family', '')}".strip()

        birth_date_val = final_profile_data.get('birthDate')
        birth_date_str = "N/A"
        if isinstance(birth_date_val, datetime.datetime):
            birth_date_str = birth_date_val.strftime('%Y-%m-%d')
        elif isinstance(birth_date_val, str):
            birth_date_str = birth_date_val

        admission_date_val = final_profile_data.get('admission_date')
        admission_date_str = "N/A"
        if isinstance(admission_date_val, datetime.datetime):
            admission_date_str = admission_date_val.strftime('%Y-%m-%d %H:%M:%S UTC')
        elif isinstance(admission_date_val, str):
            admission_date_str = admission_date_val

        code_status_text = "N/A"
        code_status_obj = final_profile_data.get("code_status")
        if code_status_obj and isinstance(code_status_obj, dict):
             code_status_text = code_status_obj.get("text", "N/A")
        elif isinstance(code_status_obj, str):
             code_status_text = code_status_obj

        return {
            "room_no": final_profile_data.get("room_no", "N/A"),
            "patient_name_dob_mrn": f"{patient_name_str} | DOB: {birth_date_str} | MRN: {final_profile_data.get('mrn', 'N/A')}",
            "isolation_precautions": final_profile_data.get("isolation_precautions", "None"),
            "code_status": code_status_text,
            "allergies": ", ".join(final_profile_data.get("allergies_text", ["None listed"])),
            "admitted_on_problem": f"Admitted on: {admission_date_str} for {final_profile_data.get('principal_problem', 'N/A')}",
            "consulting_physicians": ", ".join(final_profile_data.get("consulting_physicians", ["None listed"])),
            "emergency_contact": emergency_contact_str
        }

    async def _get_contextual_patient_data(self, patient_id: str, data_key: str, default_value: str = "N/A") -> str:
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (ReportDataService): Fetching contextual data for {patient_id}, key: {data_key} (Simulated)")
        mock_store_data = {
            "patientA123": {
                "about_me": "Retired librarian, enjoys reading and classical music. Values clear communication.",
                "our_goals": "Manage CHF symptoms, improve mobility, and return home with support.",
                "social_history_highlights": "Widowed, non-smoker, occasional wine. Strong family support."
            },
            "patientB456": {
                "about_me": "Software developer, avid cyclist. Eager to get back to work.",
                "our_goals": "Resolve pneumonia, improve respiratory function.",
                "social_history_highlights": "Married, non-smoker, exercises regularly."
            }
        }
        return mock_store_data.get(patient_id, {}).get(data_key, default_value)

    async def get_section_iii_patient_history(self, patient_id: str) -> Dict[str, Any]:
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (ReportDataService): Populating Section III - Patient History for {patient_id}")
        history_summary_text = await self.patient_summary_service.generate_patient_summary(patient_id, summary_type="historical_recap")
        relevant_past_medical_history = f"AI Generated Summary (aspects of PMH): {history_summary_text}"
        significant_surgical_history = f"AI Generated Summary (aspects of PSH): Refer to overall summary."
        about_me_data = await self._get_contextual_patient_data(patient_id, "about_me", "No 'About Me' information available.")
        our_goals_data = await self._get_contextual_patient_data(patient_id, "our_goals", "No specific goals defined.")
        social_history_data = await self._get_contextual_patient_data(patient_id, "social_history_highlights", "No social history highlights available.")
        return {
            "relevant_past_medical_history": relevant_past_medical_history,
            "significant_surgical_history": significant_surgical_history,
            "social_history_highlights": social_history_data,
            "about_me": about_me_data,
            "our_goals": our_goals_data
        }

    async def _get_mock_lab_results(self, patient_id: str) -> Dict[str, List[str]]:
        return self.MOCK_LAB_RESULTS_STATIC.get(patient_id, {"abnormal_results": [], "pending_results": []})

    async def _get_mock_iv_access_details(self, patient_id: str) -> List[Dict[str, str]]:
        return self.MOCK_IV_ACCESS_DETAILS_STATIC.get(patient_id, [])

    async def _get_neuro_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "loc": "Alert and Oriented x3", "gcs": "15", "pupils": "PERRLA",
            "sedation_goal_rass": "RASS 0", "cam_icu": "Negative", "restraints": "None",
            "motor_strength": "Moves all extremities equally", "notes": "No focal deficits."
        }
        if patient_id == "patientA123":
            assessment["notes"] = "Reports slight dizziness on standing."
        return assessment

    async def _get_pulmonary_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "airway": "Patent", "oxygen_delivery": "Nasal Cannula", "oxygen_flow_rate_fio2": "2 L/min",
            "respiratory_rate": "18", "spo2": "96%", "breath_sounds": "Clear bilaterally",
            "cough_sputum": "Non-productive", "abg_vbg_highlights": "pH 7.38, PaCO2 42",
            "ventilator_settings": "N/A", "sat_sbt_status": "N/A"
        }
        if patient_id == "patientB456":
            assessment["breath_sounds"] = "Coarse crackles in lower lobes."
            assessment["spo2"] = "93% on 2L NC"
        return assessment

    async def _get_cardiovascular_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "heart_rhythm_rate": "Sinus Rhythm, Rate 75", "bp_map": "120/80 mmHg (MAP 93)",
            "hemodynamics_pac": "N/A", "peripheral_pulses": "Radial +2, Pedal +1",
            "capillary_refill": "<3s", "edema": "Trace BLE", "active_vasoactive_drips": "None",
            "telemetry": "Monitored, no ectopy."
        }
        if patient_id == "patientA123":
            assessment["heart_rhythm_rate"] = "Atrial Fibrillation, Rate 88"
            assessment["edema"] = "+1 pitting edema ankles."
        return assessment

    async def _get_gi_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "diet_tube_feedings": "Regular Diet", "bowel_sounds": "Active x4",
            "abdomen_assessment": "Soft, non-tender", "last_bm": "Today AM",
            "nausea_vomiting": "Denies", "gi_output": "N/A",
            "blood_sugar_monitoring": "ACHS. Last: 110", "misc_gi_notes": "Tolerating diet."
        }
        if patient_id == "patientA123":
            assessment["diet_tube_feedings"] = "Cardiac Diet, 2L Fluid Restriction"
        return assessment

    async def _get_gu_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "urine_output_method": "Voiding independently", "urine_output_amount_24hr": "1800 mL",
            "urine_characteristics": "Clear, yellow", "renal_labs_summary": "BUN 18, Creat 1.0 (Stable)",
            "dialysis_access": "None"
        }
        if patient_id == "patientA123":
            assessment["renal_labs_summary"] = f"BUN 25, Creat 1.8 (Elevated, baseline {profile.get('principal_problem')})" # Example using profile
        return assessment

    async def _get_skin_mobility_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "braden_score": "19 (Low Risk)", "skin_assessment_findings": "Warm, dry, intact.",
            "wound_care_orders": "None", "pressure_injury_prevention": "Turn Q2H.",
            "mobility_status": "Ambulates independently.", "fall_interventions": "Bed low, call light in reach.",
            "spinal_precautions": "None", "bath_type_schedule": "Shower daily AM", "weight_monitoring": "Daily AM. Last: 70kg."
        }
        if patient_id == "patientA123":
            assessment["braden_score"] = "16 (Moderate Risk)"
            assessment["mobility_status"] = "Ambulates with walker, SBA."
        return assessment

    async def _get_iv_access_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        iv_sites = await self._get_mock_iv_access_details(patient_id)
        return {
            "iv_sites_and_types": iv_sites,
            "central_line_necessity": "N/A" if not any("CVC" in site.get("type","") for site in iv_sites) else "Daily review",
            "notes": "Monitor CVC site." if patient_id == "patientA123" else "Ensure PIVs dated."
        }

    async def _get_fluids_infusions_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "continuous_infusions": "None", "ivf_maintenance_bolus": "Saline lock PRN.",
            "blood_products_overview": "None", "po_intake_estimate": "Good, 1500mL/24hr.",
            "fluid_balance_24hr": "+300 mL"
        }
        if patient_id == "patientA123":
            assessment["ivf_maintenance_bolus"] = "NS @ 30 mL/hr KVO via CVC."
        return assessment

    async def _get_pain_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        assessment = {
            "pain_score_current": "0/10", "pain_location_character": "N/A", "pain_goal": "<= 3/10",
            "non_pharmacological_interventions": "Repositioning.", "pharmacological_interventions": "PRN Acetaminophen.",
            "effectiveness_of_interventions": "Well managed."
        }
        if patient_id == "patientB456":
            assessment["pain_score_current"] = "3/10 on deep inspiration"
            assessment["pain_location_character"] = "Right chest, sharp"
        return assessment

    async def _get_laboratory_diagnostics_assessment(self, patient_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        labs = await self._get_mock_lab_results(patient_id)
        return {
            "abnormal_lab_test_results": labs.get("abnormal_results", []),
            "pending_labs_tests": labs.get("pending_results", []),
            "recent_imaging_highlights": "CXR (yesterday): Bilateral lower lobe infiltrates." if patient_id == "patientB456" else "CXR (today): Mild pulmonary congestion.",
            "other_diagnostics_notes": "ECG: Afib, rate 88." if patient_id == "patientA123" else "Awaiting sputum culture."
        }

    async def get_section_v_systems_assessment(self, patient_id: str) -> Dict[str, Any]:
        """Populates data for Section V: Systems Assessment by calling sub-functions."""
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (ReportDataService): Populating Section V for {patient_id}")

        profile_model = await self.firestore_service.get_patient_profile(patient_id)
        if not profile_model:
            return {"error": f"Patient ID {patient_id} not found, cannot generate Section V."}

        profile_dict = profile_model.model_dump(exclude_none=True)

        return {
            "neurological": await self._get_neuro_assessment(patient_id, profile_dict),
            "pulmonary": await self._get_pulmonary_assessment(patient_id, profile_dict),
            "cardiovascular": await self._get_cardiovascular_assessment(patient_id, profile_dict),
            "gi_gastrointestinal": await self._get_gi_assessment(patient_id, profile_dict),
            "gu_genitourinary": await self._get_gu_assessment(patient_id, profile_dict),
            "skin_mobility": await self._get_skin_mobility_assessment(patient_id, profile_dict),
            "iv_access_lines": await self._get_iv_access_assessment(patient_id, profile_dict), # Corrected typo here
            "fluids_infusions_intake": await self._get_fluids_infusions_assessment(patient_id, profile_dict),
            "pain_comfort": await self._get_pain_assessment(patient_id, profile_dict),
            "laboratory_diagnostics": await self._get_laboratory_diagnostics_assessment(patient_id, profile_dict)
        }

    # Placeholder for saving user input related to reports
    async def save_report_input_data(self, patient_id: str, data_key: str, content: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (ReportDataService): Simulating save for patient {patient_id}, key {data_key}.")
        # This would call firestore_service or other relevant service.
        return {"status": "success", "message": "Data saved (simulated)."}

# Example usage (for testing, actual instantiation via DI)
# class MockService: pass
# mock_fs = MockService()
# mock_alloy = MockService()
# mock_summary = MockService()
# report_service = ReportDataService(firestore_service=mock_fs, alloydb_service=mock_alloy, patient_summary_service=mock_summary)
