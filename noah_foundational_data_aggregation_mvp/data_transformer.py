import datetime
import json


def transform_data_for_ai(raw_data: dict) -> dict:
    """Placeholder function representing data transformation logic.
    In a real-world scenario, this function would contain complex ETL logic
    to prepare data for AI/ML models or other analytical purposes.
    This could involve:
    - Cleaning data (handling missing values, outliers)
    - Normalizing or standardizing data formats
    - Feature engineering (creating new relevant features from existing data)
    - Anonymizing or de-identifying sensitive information
    - Aggregating data from multiple sources
    - Reshaping data into a suitable structure for the target system

    For now, it performs a simple transformation: adds a timestamp
    and returns the data nested under a 'processed_data' key.
    """
    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Called transform_data_for_ai with raw_data:"
    )
    print(json.dumps(raw_data, indent=2))

    transformed_data = {
        "processing_timestamp": datetime.datetime.utcnow().isoformat(),
        "original_data": raw_data,
        "ai_optimized_features": {
            # Example: could be flattened, aggregated, or feature-engineered data
            "key_metric_1": raw_data.get("some_value", 0) * 2,  # Simplified example
            "description": f"Transformed data for {raw_data.get('patientId', 'unknown_patient')}",
        },
    }

    print(
        f"[{datetime.datetime.utcnow().isoformat()}] INFO: Transformation complete. Result:"
    )
    print(json.dumps(transformed_data, indent=2))

    return transformed_data


if __name__ == "__main__":
    print("Running example usage of data_transformer.py...")

    # Example 1: Transforming mock patient data
    mock_raw_patient_data = {
        "patientId": "PATIENT_002",
        "systolic_bp": 120,
        "diastolic_bp": 80,
        "notes": "Patient is stable.",
    }
    print("\n--- Transforming Patient Data ---")
    transformed_patient_data = transform_data_for_ai(mock_raw_patient_data)
    # print("Transformed Patient Data:", json.dumps(transformed_patient_data, indent=2))

    print("-" * 30)

    # Example 2: Transforming mock event data
    mock_raw_event_data = {
        "eventId": "EVENT_XYZ_789",
        "patientId": "PATIENT_003",
        "eventType": "MedicationAdministered",
        "details": {"medication": "Insulin", "dosage": "10 units"},
        "some_value": 25,
    }
    print("\n--- Transforming Event Data ---")
    transformed_event_data = transform_data_for_ai(mock_raw_event_data)
    # print("Transformed Event Data:", json.dumps(transformed_event_data, indent=2))
    print("-" * 30)

    print("Example usage completed.")
