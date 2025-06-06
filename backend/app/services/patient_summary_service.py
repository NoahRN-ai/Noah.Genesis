import json
import datetime
from typing import Dict, Any, Optional, List # Added List

# Assuming services will be injectable, direct imports for now
# These will require the other service files to be created/updated first
from .firestore_service import get_patient_profile # Assuming PatientProfile and its fetching method
from .alloydb_data_service import AlloyDBDataService # For fetching events
from .rag_service import RAGService
from .llm_service import get_llm_response

class PatientSummaryService:
    def __init__(self,
                 # firestore_service: Any, # Will be properly injected
                 alloydb_service: AlloyDBDataService, # Will be AlloyDBDataService instance or mock
                 rag_service: RAGService,
                 llm_service_func: Any # Will be get_llm_response
                ):
        # self.firestore_service = firestore_service
        self.alloydb_service = alloydb_service
        self.rag_service = rag_service
        self.get_llm_response = llm_service_func

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
