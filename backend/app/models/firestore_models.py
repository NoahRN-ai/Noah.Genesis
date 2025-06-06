import uuid  # Added import
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Utility ---
def utcnow():
    return datetime.now(UTC)


# Utility function for default tool call ID
def generate_default_tool_call_id():
    return str(uuid.uuid4())


# --- UserProfile ---
class UserRole(str, Enum):
    NURSE = "nurse"
    PATIENT = "patient"


class UserProfileBase(BaseModel):
    role: UserRole
    display_name: Optional[str] = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    # created_at and updated_at will be managed by the service layer on write
    # to ensure they reflect actual DB transaction times more accurately,
    # or can be added here with default_factory=utcnow if preferred for model state.
    # For consistency, making them server-set upon write seems better.


class UserProfileCreate(UserProfileBase):
    pass  # All fields from Base are relevant for creation initially


class UserProfileUpdate(BaseModel):  # Allows partial updates
    role: Optional[UserRole] = None
    display_name: Optional[str] = None
    preferences: Optional[dict[str, Any]] = None


class UserProfile(UserProfileBase):  # Represents a UserProfile document read from DB
    user_id: str  # Document ID
    created_at: datetime
    updated_at: datetime


# --- PatientDataLog ---
class PatientDataLogDataType(str, Enum):
    OBSERVATION = "observation"
    SYMPTOM_REPORT = "symptom_report"
    LLM_SUMMARY = "llm_summary"
    NURSING_NOTE_DRAFT = "nursing_note_draft"
    SHIFT_HANDOFF_DRAFT = "shift_handoff_draft"
    USER_DOCUMENT = "user_document"  # E.g. patient uploaded document text


class PatientDataLogBase(BaseModel):
    user_id: str  # Patient who owns the data
    created_by_user_id: str  # User who entered the data (can be self or nurse)
    timestamp: datetime  # Timestamp the data pertains to (e.g., observation time)
    data_type: PatientDataLogDataType
    content: dict[str, Any] = Field(default_factory=dict)  # Flexible content structure
    source: str = "Noah.Genesis_MVP"


class PatientDataLogCreate(PatientDataLogBase):
    pass


class PatientDataLogUpdate(BaseModel):  # Allows partial updates
    # user_id and created_by_user_id are typically not updatable for a log entry
    timestamp: Optional[datetime] = None
    data_type: Optional[PatientDataLogDataType] = None
    content: Optional[dict[str, Any]] = None
    source: Optional[str] = None


class PatientDataLog(
    PatientDataLogBase
):  # Represents a PatientDataLog document read from DB
    log_id: str  # Document ID
    created_at: datetime  # Timestamp of record creation in DB
    updated_at: datetime  # Timestamp of last update in DB


# --- InteractionHistory ---
class InteractionActor(str, Enum):
    USER = "user"
    AGENT = "agent"


class ToolCall(BaseModel):
    name: str
    args: dict[str, Any]
    id: str = Field(default_factory=generate_default_tool_call_id)


class ToolResponse(BaseModel):
    tool_call_id: str  # Corresponds to the 'id' of the ToolCall it's responding to
    name: str  # The name of the tool that was called
    content: Any  # The output/content from the tool execution


class InteractionHistoryBase(BaseModel):
    session_id: str
    user_id: str
    actor: InteractionActor
    message_content: str
    tool_calls: Optional[list[ToolCall]] = None  # Verified: Uses updated ToolCall
    tool_responses: Optional[
        list[ToolResponse]
    ] = None  # Verified: Uses updated ToolResponse
    # timestamp will be managed by the service layer for accuracy on write


class InteractionHistoryCreate(InteractionHistoryBase):
    pass


class InteractionHistoryUpdate(
    BaseModel
):  # Interactions are typically immutable, but if edits were allowed:
    message_content: Optional[str] = None
    # tool_calls and tool_responses are usually part of the initial record


class InteractionHistory(
    InteractionHistoryBase
):  # Represents an InteractionHistory document read from DB
    interaction_id: str  # Document ID
    timestamp: datetime  # Timestamp of when the interaction occurred/was logged


# --- FHIR-inspired Enums and Sub-models ---


# Enums for Observation status
class FHIRStatusObservation(str, Enum):
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CANCELLED = "cancelled"  # Added based on common FHIR usage
    ENTERED_IN_ERROR = "entered-in-error"  # Added based on common FHIR usage


# Enums for MedicationStatement status
class FHIRStatusMedicationStatement(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"
    INTENDED = "intended"
    STOPPED = "stopped"
    ON_HOLD = "on-hold"


# Enums for ContactPoint
class ContactPointSystem(str, Enum):
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    PAGER = "pager"
    URL = "url"
    SMS = "sms"
    OTHER = "other"


class ContactPointUse(str, Enum):
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    MOBILE = "mobile"


# Enums for Address
class AddressUse(str, Enum):
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    BILLING = "billing"  # Common FHIR value


class AddressType(str, Enum):
    POSTAL = "postal"
    PHYSICAL = "physical"
    BOTH = "both"


# Enum for HumanName use
class HumanNameUse(str, Enum):
    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    NICKNAME = "nickname"
    ANONYMOUS = "anonymous"
    OLD = "old"
    MAIDEN = "maiden"


# Sub-model for Coding (part of CodeableConcept)
class Coding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


# Sub-model for CodeableConcept
class CodeableConcept(BaseModel):
    text: str
    coding: Optional[list[Coding]] = Field(default_factory=list)


# Sub-model for Quantity
class Quantity(BaseModel):
    value: float
    unit: str
    system: Optional[str] = None
    code: Optional[str] = None  # E.g. UCUM code for the unit


# Sub-model for Address
class Address(BaseModel):
    use: Optional[AddressUse] = None
    type: Optional[AddressType] = None
    text: Optional[str] = None  # Full address as text
    line: Optional[list[str]] = Field(default_factory=list)
    city: Optional[str] = None
    district: Optional[str] = None  # County, district, region
    state: Optional[str] = None  # State, province
    postalCode: Optional[str] = None
    country: Optional[str] = None
    # period: Optional[Period] # FHIR Period sub-model, can add if needed


# Sub-model for HumanName
class HumanName(BaseModel):
    use: Optional[HumanNameUse] = None
    text: Optional[str] = None  # Full name as text
    family: Optional[str] = None  # Surname
    given: Optional[list[str]] = Field(default_factory=list)  # Given names
    prefix: Optional[list[str]] = Field(default_factory=list)
    suffix: Optional[list[str]] = Field(default_factory=list)
    # period: Optional[Period] # FHIR Period sub-model, can add if needed


# Sub-model for ContactPoint (telecom)
class ContactPoint(BaseModel):
    system: Optional[ContactPointSystem] = None
    value: Optional[str] = None  # The actual contact detail
    use: Optional[ContactPointUse] = None
    # rank: Optional[int] # Priority of use
    # period: Optional[Period] # FHIR Period sub-model, can add if needed


# --- PatientProfile Model ---
# Inspired by FHIR Patient resource


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class PatientProfileBase(BaseModel):
    active: Optional[bool] = True
    name: Optional[list[HumanName]] = Field(default_factory=list)
    telecom: Optional[list[ContactPoint]] = Field(default_factory=list)
    gender: Optional[Gender] = Gender.UNKNOWN
    birthDate: Optional[
        datetime
    ] = None  # FHIR uses 'date' string, but datetime is more useful
    address: Optional[list[Address]] = Field(default_factory=list)
    # photo: Optional[Attachment] # Can add if needed, FHIR Attachment sub-model
    # managingOrganization: Optional[Reference] # FHIR Reference to Organization, if needed
    # maritalStatus: Optional[CodeableConcept] # If needed
    # multipleBirthBoolean: Optional[bool] # If needed
    # multipleBirthInteger: Optional[int] # If needed
    # deceasedBoolean: Optional[bool] # If needed
    # deceasedDateTime: Optional[datetime] # If needed

    # Custom fields specific to this application, not strictly FHIR
    # e.g. primary_care_provider_id: Optional[str] = None (links to a UserProfile of a nurse/doctor)

    model_config = {
        "use_enum_values": True  # Ensures enum values are used in serialization
    }


class PatientProfileCreate(PatientProfileBase):
    # patient_id will be assigned by Firestore, not part of creation model
    pass


class PatientProfileUpdate(BaseModel):  # For partial updates
    active: Optional[bool] = None
    name: Optional[list[HumanName]] = None
    telecom: Optional[list[ContactPoint]] = None
    gender: Optional[Gender] = None
    birthDate: Optional[datetime] = None
    address: Optional[list[Address]] = None
    # Any other fields from PatientProfileBase that should be updatable


class PatientProfile(
    PatientProfileBase
):  # Represents a PatientProfile document read from DB
    patient_id: str  # Document ID (Firestore document ID)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


# --- Observation Model ---
# Inspired by FHIR Observation resource


class ObservationBase(BaseModel):
    status: FHIRStatusObservation = FHIRStatusObservation.FINAL
    category: Optional[list[CodeableConcept]] = Field(default_factory=list)
    code: CodeableConcept  # What was observed (e.g., blood pressure, glucose)
    subject_patient_id: str  # Reference to PatientProfile.patient_id
    effectiveDateTime: Optional[datetime] = None  # When the result is valid
    # effectivePeriod: Optional[Period] # Can use instead of effectiveDateTime
    # effectiveTiming: Optional[Timing] # Can use instead of effectiveDateTime
    # effectiveInstant: Optional[datetime] # Can use instead of effectiveDateTime
    issued: Optional[datetime] = Field(
        default_factory=utcnow
    )  # Date this version was released
    performer_user_id: Optional[list[str]] = Field(
        default_factory=list
    )  # Who performed the observation (e.g., UserProfile.user_id)

    valueQuantity: Optional[Quantity] = None
    valueCodeableConcept: Optional[CodeableConcept] = None
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    # valueRange: Optional[Range] # FHIR Range sub-model
    # valueRatio: Optional[Ratio] # FHIR Ratio sub-model
    # valueSampledData: Optional[SampledData] # FHIR SampledData sub-model
    # valueTime: Optional[datetime.time] # FHIR time string
    # valueDateTime: Optional[datetime] # FHIR dateTime string
    # valuePeriod: Optional[Period] # FHIR Period sub-model

    # dataAbsentReason: Optional[CodeableConcept] # If status is preliminary/partial and value is missing
    interpretation: Optional[list[CodeableConcept]] = Field(
        default_factory=list
    )  # E.g., high, low, normal
    note: Optional[str] = None  # Additional comments
    bodySite: Optional[CodeableConcept] = None  # E.g., left arm
    # method: Optional[CodeableConcept] # How observation was performed
    # referenceRange: Optional[List[ObservationReferenceRange]] # Sub-model for reference ranges
    # hasMember: Optional[List[Reference]] # To other Observations
    # derivedFrom: Optional[List[Reference]] # To other resources like DocumentReference, ImagingStudy, etc.
    # component: Optional[List[ObservationComponent]] # For multi-part observations like BP (systolic, diastolic)

    model_config = {"use_enum_values": True}


class ObservationCreate(ObservationBase):
    # observation_id will be assigned by Firestore
    pass


class ObservationUpdate(BaseModel):  # For partial updates
    status: Optional[FHIRStatusObservation] = None
    category: Optional[list[CodeableConcept]] = None
    code: Optional[CodeableConcept] = None
    effectiveDateTime: Optional[datetime] = None
    issued: Optional[datetime] = None
    performer_user_id: Optional[list[str]] = None
    valueQuantity: Optional[Quantity] = None
    valueCodeableConcept: Optional[CodeableConcept] = None
    valueString: Optional[str] = None
    valueBoolean: Optional[bool] = None
    valueInteger: Optional[int] = None
    interpretation: Optional[list[CodeableConcept]] = None
    note: Optional[str] = None
    bodySite: Optional[CodeableConcept] = None
    # Add other fields from ObservationBase as needed


class Observation(ObservationBase):  # Represents an Observation document read from DB
    observation_id: str  # Document ID (Firestore document ID)
    # subject_patient_id is already in ObservationBase
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


# --- MedicationStatement Model ---
# Inspired by FHIR MedicationStatement resource


class MedicationStatementBase(BaseModel):
    status: FHIRStatusMedicationStatement = FHIRStatusMedicationStatement.ACTIVE
    # statusReason: Optional[List[CodeableConcept]] # Why is the status as it is (e.g. if stopped)
    # category: Optional[CodeableConcept] # E.g. inpatient, outpatient - not in MVP spec but common
    medicationCodeableConcept: CodeableConcept  # What medication
    # medicationReference: Optional[Reference] # Alternative to CodeableConcept, if medications are stored as separate FHIR resources
    subject_patient_id: str  # Reference to PatientProfile.patient_id
    # context: Optional[Reference] # Encounter or EpisodeOfCare associated
    effectiveDateTime: Optional[datetime] = None  # Start of medication administration
    effectivePeriod_start: Optional[
        datetime
    ] = None  # More explicit than effectiveDateTime
    effectivePeriod_end: Optional[datetime] = None
    # effectiveTiming: Optional[Timing] # FHIR Timing sub-model if more complex schedule needed
    dateAsserted: Optional[datetime] = Field(
        default_factory=utcnow
    )  # When this statement was recorded
    informationSource_user_id: Optional[
        str
    ] = None  # Who provided the information (e.g., patient, practitioner, UserProfile.user_id)
    # informationSource_patient_id: Optional[str] = None # If patient themselves is the source
    # derivedFrom: Optional[List[Reference]] # Link to other resources
    # reasonCode: Optional[List[CodeableConcept]] # Why medication is taken
    # reasonReference: Optional[List[Reference]] # Link to Condition or Observation
    note: Optional[str] = None  # Additional comments

    # Dosage moved to a separate sub-model for better structure, as per FHIR
    # For MVP, simplified dosage fields directly in the model as per spec:
    dosage_text: Optional[str] = None  # E.g., "One tablet by mouth daily"
    dosage_timing_code_text: Optional[str] = None  # E.g., "BID", "Q4H"
    # FHIR has a Dosage sub-model which is more structured:
    # dosage: Optional[List[Dosage]] # FHIR Dosage sub-model

    model_config = {"use_enum_values": True}


class MedicationStatementCreate(MedicationStatementBase):
    # medication_statement_id will be assigned by Firestore
    pass


class MedicationStatementUpdate(BaseModel):  # For partial updates
    status: Optional[FHIRStatusMedicationStatement] = None
    medicationCodeableConcept: Optional[CodeableConcept] = None
    effectiveDateTime: Optional[datetime] = None
    effectivePeriod_start: Optional[datetime] = None
    effectivePeriod_end: Optional[datetime] = None
    dateAsserted: Optional[datetime] = None
    informationSource_user_id: Optional[str] = None
    dosage_text: Optional[str] = None
    dosage_timing_code_text: Optional[str] = None
    note: Optional[str] = None
    # Add other fields from MedicationStatementBase as needed


class MedicationStatement(
    MedicationStatementBase
):  # Represents a MedicationStatement document read from DB
    medication_statement_id: str  # Document ID (Firestore document ID)
    # subject_patient_id is already in MedicationStatementBase
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


# --- AIContextualStore Model ---
# Stores AI-generated summaries, insights, and user preferences for context.


class AIContextualStoreBase(BaseModel):
    patient_id: str  # Document ID, links to PatientProfile.patient_id
    last_summary: Optional[str] = None
    key_insights: list[str] = Field(default_factory=list)
    interaction_highlights: list[str] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(
        default_factory=dict
    )  # E.g. communication style, summary length
    custom_alerts: list[str] = Field(
        default_factory=list
    )  # Or List[Dict[str, Any]] for structured alerts
    # Reminder: created_at and updated_at are set by the service layer.


class AIContextualStoreCreate(AIContextualStoreBase):
    # patient_id is mandatory and comes from AIContextualStoreBase.
    # All other fields from Base are relevant for creation, often starting empty or with defaults.
    pass


class AIContextualStoreUpdate(BaseModel):  # For partial updates
    last_summary: Optional[str] = None
    key_insights: Optional[list[str]] = None
    interaction_highlights: Optional[list[str]] = None
    preferences: Optional[dict[str, Any]] = None
    custom_alerts: Optional[list[str]] = None
    # patient_id is the document ID and should not be updatable via this model.


class AIContextualStore(
    AIContextualStoreBase
):  # Represents an AIContextualStore document read from DB
    # patient_id is inherited from AIContextualStoreBase and serves as the document ID.
    created_at: datetime  # Set by service layer
    updated_at: datetime  # Set by service layer
