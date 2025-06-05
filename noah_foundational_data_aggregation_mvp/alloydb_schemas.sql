-- Schema for CoreRelationalRecords Table
CREATE TABLE CoreRelationalRecords (
    recordId SERIAL PRIMARY KEY,
    patientId VARCHAR(255) NOT NULL, -- Assuming this links to Firestore patientId
    recordType VARCHAR(100), -- E.g., 'PhysicianOrder', 'ConsultNote'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB -- Or TEXT if JSONB is not available/preferred
    -- FOREIGN KEY (patientId) REFERENCES Patients(firestorePatientId) -- If a separate Patients table with mapping exists
);

-- Schema for EventLogs Table
CREATE TABLE EventLogs (
    eventId SERIAL PRIMARY KEY,
    patientId VARCHAR(255) NOT NULL, -- Assuming this links to Firestore patientId
    eventType VARCHAR(100), -- E.g., 'VitalSignChange', 'MedicationAdministered', 'NurseInput'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    value JSONB, -- Or TEXT, flexible to store various event data structures
    source VARCHAR(100) -- E.g., 'ManualInput', 'SimulatedMonitor', 'EMRFeed'
    -- FOREIGN KEY (patientId) REFERENCES Patients(firestorePatientId) -- If a separate Patients table with mapping exists
);

-- Optional: A Patients table to map internal IDs to Firestore patientIds if needed
-- CREATE TABLE Patients (
-- internalPatientId SERIAL PRIMARY KEY,
-- firestorePatientId VARCHAR(255) UNIQUE NOT NULL,
-- createdAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- Indexes for faster querying
CREATE INDEX idx_corerelationalrecords_patientid ON CoreRelationalRecords(patientId);
CREATE INDEX idx_corerelationalrecords_timestamp ON CoreRelationalRecords(timestamp);
CREATE INDEX idx_eventlogs_patientid ON EventLogs(patientId);
CREATE INDEX idx_eventlogs_eventtype ON EventLogs(eventType);
CREATE INDEX idx_eventlogs_timestamp ON EventLogs(timestamp);
