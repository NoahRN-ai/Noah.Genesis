import pytest
from pydantic import ValidationError
from datetime import datetime, date # Import date specifically if used
from typing import List

from backend.app.models.firestore_models import (
    PatientProfile, PatientProfileCreate, Gender, HumanName, HumanNameUse, ContactPoint, ContactPointSystem, ContactPointUse, Address, AddressUse, AddressType,
    Observation, ObservationCreate, FHIRStatusObservation, CodeableConcept, Coding, Quantity,
    MedicationStatement, MedicationStatementCreate, FHIRStatusMedicationStatement,
    AIContextualStore, AIContextualStoreCreate,
    utcnow # Assuming utcnow is accessible here for default comparisons or test data generation
)

# --- Test Data Samples ---

def get_sample_human_name_data(use: HumanNameUse = HumanNameUse.OFFICIAL, family: str = "Doe", given: List[str] = ["John"]) -> dict:
    return {
        "use": use.value,
        "family": family,
        "given": given,
        "text": f"{' '.join(given)} {family}"
    }

def get_sample_contact_point_data(system: ContactPointSystem = ContactPointSystem.EMAIL, value: str = "john.doe@example.com", use: ContactPointUse = ContactPointUse.HOME) -> dict:
    return {"system": system.value, "value": value, "use": use.value}

def get_sample_address_data(use: AddressUse = AddressUse.HOME, city: str = "Pleasantville", postal_code: str = "12345") -> dict:
    return {
        "use": use.value,
        "line": ["123 Main St"],
        "city": city,
        "state": "CA",
        "postalCode": postal_code,
        "country": "USA"
    }

def get_sample_patient_profile_data(patient_id: str = "patient123") -> dict:
    # For PatientProfile, created_at/updated_at are not part of Create model but part of full model
    return {
        "patient_id": patient_id,
        "active": True,
        "name": [HumanName(**get_sample_human_name_data())],
        "telecom": [ContactPoint(**get_sample_contact_point_data())],
        "gender": Gender.MALE.value,
        "birthDate": datetime(1980, 1, 1, 0, 0, 0), # FHIR birthDate is often just 'date' string, but model uses datetime
        "address": [Address(**get_sample_address_data())],
        "created_at": utcnow(),
        "updated_at": utcnow()
    }

def get_sample_codeable_concept_data(text: str = "Vital Signs", system: str = "http://loinc.org", code: str = "85353-1") -> dict:
    return {
        "text": text,
        "coding": [{"system": system, "code": code, "display": text}]
    }

def get_sample_quantity_data(value: float = 120.0, unit: str = "mmHg") -> dict:
    return {"value": value, "unit": unit, "system": "http://unitsofmeasure.org", "code": "mm[Hg]"}


def get_sample_observation_data(observation_id: str = "obs123", patient_id: str = "patient123") -> dict:
    return {
        "observation_id": observation_id,
        "subject_patient_id": patient_id,
        "status": FHIRStatusObservation.FINAL.value,
        "code": CodeableConcept(**get_sample_codeable_concept_data(text="Blood Pressure")),
        "effectiveDateTime": utcnow(),
        "issued": utcnow(),
        "valueQuantity": Quantity(**get_sample_quantity_data()),
        "created_at": utcnow(),
        "updated_at": utcnow()
    }

def get_sample_medication_statement_data(statement_id: str = "medstmt123", patient_id: str = "patient123") -> dict:
    return {
        "medication_statement_id": statement_id,
        "subject_patient_id": patient_id,
        "status": FHIRStatusMedicationStatement.ACTIVE.value,
        "medicationCodeableConcept": CodeableConcept(**get_sample_codeable_concept_data(text="Lisinopril 10mg tablet")),
        "effectiveDateTime": utcnow(),
        "dateAsserted": utcnow(),
        "dosage_text": "One tablet by mouth daily",
        "created_at": utcnow(),
        "updated_at": utcnow()
    }

def get_sample_ai_contextual_store_data(patient_id: str = "patient123") -> dict:
    return {
        "patient_id": patient_id,
        "last_summary": "Patient is doing well.",
        "key_insights": ["Regular exercise"],
        "interaction_highlights": ["Discussed diet plan"],
        "preferences": {"communication": "email"},
        "custom_alerts": ["Check blood sugar levels"],
        "created_at": utcnow(),
        "updated_at": utcnow()
    }

# --- Sub-model Tests ---

class TestHumanName:
    def test_human_name_creation(self):
        data = get_sample_human_name_data()
        name = HumanName(**data)
        assert name.family == "Doe"
        assert name.use == HumanNameUse.OFFICIAL

    def test_human_name_invalid_use(self):
        data = get_sample_human_name_data()
        data["use"] = "invalid_use_enum"
        with pytest.raises(ValidationError):
            HumanName(**data)

class TestCodeableConcept:
    def test_codeable_concept_creation(self):
        data = get_sample_codeable_concept_data()
        cc = CodeableConcept(**data)
        assert cc.text == "Vital Signs"
        assert len(cc.coding) == 1
        assert cc.coding[0].code == "85353-1"

    def test_codeable_concept_missing_text(self):
        data = get_sample_codeable_concept_data()
        del data["text"]
        with pytest.raises(ValidationError):
            CodeableConcept(**data)

# --- Main Model Tests ---

class TestPatientProfile:
    def test_patient_profile_creation(self):
        data = get_sample_patient_profile_data()
        # PatientProfileCreate does not have created_at/updated_at/patient_id set by client
        create_data = {k: v for k, v in data.items() if k not in ["patient_id", "created_at", "updated_at"]}
        profile_create = PatientProfileCreate(**create_data)
        assert profile_create.name[0].family == "Doe"

        profile_full = PatientProfile(**data)
        assert profile_full.patient_id == "patient123"
        assert profile_full.gender == Gender.MALE

    def test_patient_profile_minimal(self):
        # Assuming 'active', 'name', 'telecom', 'address' are optional with defaults
        # And gender has a default. birthDate is optional.
        # PatientProfileCreate only needs what's not defaulted or optional in PatientProfileBase
        # For this test, let's assume an empty create model is not valid if some fields are truly required by base.
        # The current PatientProfileBase has no strictly required fields beyond what defaults provide.
        # Let's make 'gender' a required field in Create for a better test.
        # (This would require model change, so for now, test with existing model structure)

        # If PatientProfileBase had required fields, this would fail:
        # with pytest.raises(ValidationError):
        #     PatientProfileCreate()

        # Test with what makes sense for the current model
        minimal_create_data = {} # Assuming PatientProfileBase has defaults for all or they are optional
        profile_create = PatientProfileCreate(**minimal_create_data)
        assert profile_create.active is True # Default from PatientProfileBase
        assert profile_create.gender == Gender.UNKNOWN # Default from PatientProfileBase

        # For the full model, patient_id, created_at, updated_at are required
        minimal_full_data = {
            "patient_id": "min_patient",
            "created_at": utcnow(),
            "updated_at": utcnow()
        }
        profile_full = PatientProfile(**minimal_full_data)
        assert profile_full.patient_id == "min_patient"
        assert profile_full.active is True # Default from base

    def test_patient_profile_invalid_gender(self):
        data = get_sample_patient_profile_data()
        create_data = {k: v for k, v in data.items() if k not in ["patient_id", "created_at", "updated_at"]}
        create_data["gender"] = "invalid_gender"
        with pytest.raises(ValidationError):
            PatientProfileCreate(**create_data)

    def test_patient_profile_missing_required_for_full_model(self):
        data = get_sample_patient_profile_data()
        del data["patient_id"] # patient_id is required for PatientProfile
        with pytest.raises(ValidationError):
            PatientProfile(**data)


class TestObservation:
    def test_observation_creation(self):
        data = get_sample_observation_data()
        create_data = {k: v for k, v in data.items() if k not in ["observation_id", "created_at", "updated_at"]}
        # subject_patient_id and code are required for ObservationCreate (inherited from ObservationBase)
        obs_create = ObservationCreate(**create_data)
        assert obs_create.subject_patient_id == "patient123"
        assert obs_create.code.text == "Blood Pressure"

        obs_full = Observation(**data)
        assert obs_full.observation_id == "obs123"
        assert obs_full.status == FHIRStatusObservation.FINAL

    def test_observation_missing_required(self):
        data = get_sample_observation_data()
        create_data = {k: v for k, v in data.items() if k not in ["observation_id", "created_at", "updated_at"]}
        del create_data["code"] # code is required
        with pytest.raises(ValidationError):
            ObservationCreate(**create_data)

    def test_observation_invalid_status(self):
        data = get_sample_observation_data()
        create_data = {k: v for k, v in data.items() if k not in ["observation_id", "created_at", "updated_at"]}
        create_data["status"] = "invalid_status_enum"
        with pytest.raises(ValidationError):
            ObservationCreate(**create_data)


class TestMedicationStatement:
    def test_medication_statement_creation(self):
        data = get_sample_medication_statement_data()
        create_data = {k: v for k, v in data.items() if k not in ["medication_statement_id", "created_at", "updated_at"]}
        med_stmt_create = MedicationStatementCreate(**create_data)
        assert med_stmt_create.subject_patient_id == "patient123"
        assert med_stmt_create.medicationCodeableConcept.text == "Lisinopril 10mg tablet"

        med_stmt_full = MedicationStatement(**data)
        assert med_stmt_full.medication_statement_id == "medstmt123"
        assert med_stmt_full.status == FHIRStatusMedicationStatement.ACTIVE

    def test_medication_statement_missing_required(self):
        data = get_sample_medication_statement_data()
        create_data = {k: v for k, v in data.items() if k not in ["medication_statement_id", "created_at", "updated_at"]}
        del create_data["medicationCodeableConcept"] # medicationCodeableConcept is required
        with pytest.raises(ValidationError):
            MedicationStatementCreate(**create_data)

    def test_medication_statement_invalid_status(self):
        data = get_sample_medication_statement_data()
        create_data = {k: v for k, v in data.items() if k not in ["medication_statement_id", "created_at", "updated_at"]}
        create_data["status"] = "invalid_status_enum"
        with pytest.raises(ValidationError):
            MedicationStatementCreate(**create_data)


class TestAIContextualStore:
    def test_ai_contextual_store_creation(self):
        data = get_sample_ai_contextual_store_data()
        # AIContextualStoreCreate requires patient_id
        create_data = {k: v for k, v in data.items() if k not in ["created_at", "updated_at"]}
        # patient_id is part of base, so it's in create_data
        store_create = AIContextualStoreCreate(**create_data)
        assert store_create.patient_id == "patient123"
        assert store_create.last_summary == "Patient is doing well."

        store_full = AIContextualStore(**data)
        assert store_full.patient_id == "patient123"
        assert len(store_full.key_insights) == 1

    def test_ai_contextual_store_minimal_create(self):
        # patient_id is the only strictly required field for AIContextualStoreCreate
        # as other fields have defaults (Optional or default_factory)
        create_data = {"patient_id": "patient_min_123"}
        store_create = AIContextualStoreCreate(**create_data)
        assert store_create.patient_id == "patient_min_123"
        assert store_create.last_summary is None
        assert store_create.key_insights == []

    def test_ai_contextual_store_missing_patient_id_create(self):
        with pytest.raises(ValidationError) as excinfo:
            AIContextualStoreCreate() # Missing patient_id
        assert "patient_id" in str(excinfo.value)

    def test_ai_contextual_store_missing_required_for_full_model(self):
        data = get_sample_ai_contextual_store_data()
        del data["created_at"] # created_at is required for AIContextualStore full model
        with pytest.raises(ValidationError):
            AIContextualStore(**data)

# TODO: Add more tests for edge cases, specific field validations, and other sub-models as complexity grows.
# For example, testing specific validation on ContactPoint.value based on ContactPoint.system (e.g. email format).
# Test Address fields, Quantity fields for type errors.
# Test lists to ensure they accept list of sub-models correctly.
# Test FHIR enums directly if they have complex logic beyond string matching.
# Test datetime fields with invalid date/time formats if not using datetime objects directly.
# The current tests cover basic instantiation, required fields, and some enum validation.
# For birthDate in PatientProfile, if it were a `date` string from FHIR, validation would be different.
# Since it's `datetime`, Pydantic handles type checking.
# If `utcnow` is not available in this scope, it needs to be imported or mocked.
# For now, assuming it's imported from firestore_models where it's defined.
# If `Field(default_factory=utcnow)` was used for created_at/updated_at in main models,
# then the create models would not need them, and full models would have them defaulted.
# Current structure in firestore_models.py:
# - PatientProfile, Observation, MedicationStatement have created_at/updated_at with default_factory=utcnow.
# - AIContextualStore has created_at/updated_at without default_factory (service sets them).
# This means AIContextualStore sample data and tests for full model *must* provide created_at/updated_at.
# For the others, they *could* be omitted from sample data for full model if relying on default_factory.
# However, providing them in sample data is fine for explicitness.
# The Create models (e.g. PatientProfileCreate) inherit from Base models.
# If Base model has default_factory for a field, then Create model also has it.
# This makes the distinction between Create and Full model (for DB representation) primarily about the ID and server-set timestamps.
# The provided sample data for full models (PatientProfile, Observation, MedStmt) includes these, which is good.
# My tests reflect this: create_data strips out ID and server timestamps, full_data includes them.
# For AIContextualStore, created_at/updated_at are NOT default_factory, so they MUST be in the full model data, and service layer sets them.
# The AIContextualStoreCreate model still inherits patient_id from AIContextualStoreBase.
# My test for AIContextualStoreCreate missing patient_id is correct.
# My test for AIContextualStore full model missing created_at is correct.
# The tests for PatientProfile/Observation/MedStatement for missing created_at/updated_at in the *full* model would pass if default_factory is used.
# Let's assume for full model tests, we always provide these timestamps for clarity, regardless of default_factory.
# The current tests for PatientProfile missing required fields for full model (e.g. patient_id) are correct.
# It would be good to test that fields meant to be set by server (like created_at in AIContextualStore) are not required in Create models.
# AIContextualStoreCreate does not require created_at/updated_at, which is correct.
# PatientProfileCreate does not require patient_id/created_at/updated_at, which is also correct.
# ObservationCreate does not require observation_id/created_at/updated_at.
# MedicationStatementCreate does not require medication_statement_id/created_at/updated_at.
# The tests align with this.
pytest # To make sure the linter/formatter sees this as a test file
