import json
import datetime
from typing import Dict, Any, Optional, List # Added List

# Assuming services will be injectable, direct imports for now
# These will require the other service files to be created/updated first
from .firestore_service import get_patient_profile # Assuming PatientProfile and its fetching method
from .alloydb_data_service import AlloyDBDataService # For fetching events
from .rag_service import RAGService
from .llm_service import get_llm_response
from .tts_service import TTSService # New import

class PatientSummaryService:
    def __init__(self,
                 alloydb_service: AlloyDBDataService,
                 rag_service: RAGService,
                 llm_service_func: Any, # This is get_llm_response
                 tts_service: TTSService # Added TTSService
                ):
        # self.firestore_service = firestore_service # Not passed via init, get_patient_profile is imported directly
        self.alloydb_service = alloydb_service
        self.rag_service = rag_service
        self.get_llm_response = llm_service_func
        self.tts_service = tts_service # Store TTSService instance
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (PatientSummaryService): Initialized with TTS.")


    async def generate_patient_summary(self, patient_id: str, summary_type: str) -> str:
        """
        Generates a patient summary by fetching data, querying RAG, and calling an LLM.
        (Logic adapted from patient_summary_agent.py)
        """
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (PatientSummaryService): Generating summary for patient {patient_id}, type: {summary_type}")

        # 1. Fetch Patient Profile
        patient_profile_data = await get_patient_profile(patient_id)
        if not patient_profile_data:
            return f"Error: Patient with ID {patient_id} not found."

        patient_profile = patient_profile_data.model_dump()


        # 2. Fetch Event Logs (using AlloyDBDataService or mock)
        event_logs = await self.alloydb_service.list_events_for_patient(patient_id, limit=20)


        # 3. Query RAG
        rag_query = patient_profile.get("principal_problem", "general medical condition")
        rag_results = await self.rag_service.query_clinical_knowledge_base(
            query=rag_query,
            patient_context={"patient_id": patient_id, "profile": patient_profile}
        )

        # 4. Construct Prompt for LLM
        summary_parts = []
        summary_parts.append(f"--- AI-Generated Summary ({summary_type.replace('_', ' ').title()}) ---")

        # Safely access patient name
        patient_name_list = patient_profile.get('name', [])
        patient_name = "N/A"
        if patient_name_list and isinstance(patient_name_list, list) and len(patient_name_list) > 0:
            patient_name = patient_name_list[0].get('text', 'N/A')

        summary_parts.append(f"Patient: {patient_name} (ID: {patient_profile.get('patient_id', 'N/A')})")

        birth_date = patient_profile.get('birthDate', 'N/A')
        if isinstance(birth_date, datetime.datetime): # Format datetime if it's an object
            birth_date = birth_date.strftime('%Y-%m-%d')
        summary_parts.append(f"DOB: {birth_date}, MRN: {patient_profile.get('mrn', 'N/A')}")

        admission_date = patient_profile.get('admission_date', 'N/A')
        if isinstance(admission_date, datetime.datetime): # Format datetime
            admission_date = admission_date.strftime('%Y-%m-%d %H:%M:%S')
        summary_parts.append(f"Admission Date: {admission_date}")

        summary_parts.append(f"Principal Problem: {patient_profile.get('principal_problem', 'N/A')}")
        summary_parts.append(f"Allergies: {', '.join(patient_profile.get('allergies_text', ['N/A']))}")

        code_status_obj = patient_profile.get('code_status', {})
        code_status_text = "N/A"
        if code_status_obj and isinstance(code_status_obj, dict): # Check if it's a dict (from CodeableConcept)
            code_status_text = code_status_obj.get('text', 'N/A')
        summary_parts.append(f"Code Status: {code_status_text}")


        summary_parts.append("\nKey Recent Events:")
        if event_logs:
            for event in event_logs[:3]:
                event_ts = event.get('timestamp', 'N/A')
                if isinstance(event_ts, datetime.datetime): event_ts = event_ts.isoformat()
                summary_parts.append(f"  - {event_ts}: {event.get('eventType')} - {json.dumps(event.get('value'))}")
        else:
            summary_parts.append("  - No recent events found (or mock service returned empty).")

        summary_parts.append("\nRelevant Clinical Information (RAG):")
        if rag_results:
            for doc in rag_results[:2]:
                summary_parts.append(f"  - {doc.get('title')}: {doc.get('snippet')}")
        else:
            summary_parts.append("  - No specific clinical guidance retrieved by RAG.")

        if summary_type == 'nursing_note':
            summary_parts.append("\nNursing Focus:")
            summary_parts.append("  - Monitor vital signs closely, especially related to the principal problem.")
            summary_parts.append("  - Administer medications as prescribed and observe for effects/side effects.")
        elif summary_type == 'handoff_report':
            summary_parts.append("\nKey Points for Handoff:")
            summary_parts.append(f"  - Patient is {patient_name} admitted for {patient_profile.get('principal_problem', 'N/A')}.")
            summary_parts.append("  - Current status: [Simulated assessment - e.g., Stable but requires monitoring for changes related to principal problem].")

        llm_prompt = "\n".join(summary_parts)
        llm_prompt += "\n\n--- End of Context, Begin Summary ---"


        # 5. Call LLM Service
        summary_text = await self.get_llm_response(prompt=llm_prompt, conversation_history=None)

        return summary_text

# Example instantiation (would be handled by DI in FastAPI)
# rag_serv = RAGService()
# alloy_serv = MockAlloyDBDataService() # Or AlloyDBDataService() once method is available
# from backend.app.services.llm_service import get_llm_response_vertex # Specific LLM func
# patient_summary_serv = PatientSummaryService(alloydb_service=alloy_serv, rag_service=rag_serv, llm_service_func=get_llm_response_vertex)

    async def generate_handoff_report(self,
                                      patient_id: str,
                                      manual_priorities: List[str],
                                      manual_monitoring_params: List[str],
                                      shift_duration_hours: int = 12
                                     ) -> Dict[str, Any]:
        """
        Generates a handoff report including AI summary, manual inputs, and TTS audio ref.
        """
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (PatientSummaryService): Generating handoff report for {patient_id}")

        # 1. Fetch Patient Profile (using direct import for now)
        profile_model = await get_patient_profile(patient_id)
        if not profile_model:
            return {"error": f"Handoff Report Error: Patient ID {patient_id} not found."}
        profile_dict = profile_model.model_dump(exclude_none=True)

        # 2. Fetch Recent Events (using AlloyDBDataService)
        # TODO: The original script had specific time filtering for events.
        # list_events_for_patient in AlloyDBDataService has default limit/order, but not specific time window yet.
        # For now, using default list; this could be enhanced in AlloyDBDataService.
        recent_events = await self.alloydb_service.list_events_for_patient(patient_id, limit=15, descending=True)
        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (PatientSummaryService): Fetched {len(recent_events)} recent events for handoff.")


        # 3. Generate AI Summary part for handoff
        # Using existing method, maybe a specific summary_type like "handoff_narrative"
        ai_summary_text = await self.generate_patient_summary(patient_id, summary_type="handoff_narrative")
        if "Error:" in ai_summary_text: # Basic error check from summary generation
             print(f"[{datetime.datetime.utcnow().isoformat()}] WARN (PatientSummaryService): AI summary generation for handoff encountered an error: {ai_summary_text}")
             # Decide if to proceed without AI summary or return error
             # For now, continue and note missing AI summary

        # 4. Construct text for TTS
        tts_text_parts = [f"Handoff for patient {profile_dict.get('name', [{'text': ''}])[0].get('text', patient_id)}."]
        if "Error:" not in ai_summary_text and ai_summary_text:
            tts_text_parts.append(f"AI Summary: {ai_summary_text}")
        else:
            tts_text_parts.append("AI summary could not be generated for this handoff.")

        if manual_priorities:
            tts_text_parts.append("Key priorities are:")
            for priority in manual_priorities:
                tts_text_parts.append(priority) # Assuming priorities are full sentences
        if manual_monitoring_params:
            tts_text_parts.append("Parameters to monitor closely include:")
            for param in manual_monitoring_params:
                tts_text_parts.append(param)

        full_tts_text = " ".join(tts_text_parts)

        # 5. Call TTS Service
        tts_response = await self.tts_service.synthesize_speech(full_tts_text, patient_id=patient_id)
        voice_audio_ref = tts_response.get("audio_reference") if tts_response.get("status") == "success" else None

        # 6. Construct final handoff data
        handoff_data = {
            "patient_id": patient_id,
            "patient_name": profile_dict.get('name', [{'text': 'N/A'}])[0].get('text', 'N/A'),
            "room_no": profile_dict.get("room_no", "N/A"), # Assuming room_no might be added to profile or fetched elsewhere
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "ai_generated_shift_summary": ai_summary_text if "Error:" not in ai_summary_text else "N/A due to error.",
            "top_priorities_for_incoming_nurse": manual_priorities,
            "parameters_to_monitor_closely": manual_monitoring_params,
            "voice_handoff_available": bool(voice_audio_ref),
            "voice_handoff_audio_ref": voice_audio_ref
        }

        print(f"[{datetime.datetime.utcnow().isoformat()}] INFO (PatientSummaryService): Handoff data generation complete for {patient_id}.")
        return handoff_data
