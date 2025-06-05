import os
import json
from flask import Flask, jsonify, abort

app = Flask(__name__)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/Patient/<string:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """
    Retrieves a Patient FHIR resource by its ID.
    """
    file_path = os.path.join(DATA_DIR, f"{patient_id}.json")

    if not os.path.exists(file_path):
        abort(404, description=f"Patient with ID '{patient_id}' not found.")

    try:
        with open(file_path, 'r') as f:
            patient_data = json.load(f)
        return jsonify(patient_data)
    except Exception as e:
        abort(500, description=f"Error reading patient data: {str(e)}")

if __name__ == '__main__':
    # Note: This is a basic development server.
    # For production, use a proper WSGI server like Gunicorn.
    app.run(debug=True, host='0.0.0.0', port=5000)
