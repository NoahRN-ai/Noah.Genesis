# AI Report - Section V: Core Systems Assessment (UI Blueprint)

This document outlines the conceptual UI structure for Section V of the AI-generated shift report.
It shows where data generated by `populate_section_v_systems_assessment(patient_id)` would be displayed.
For an MVP, many fields will be for display (from mock/manual data), while some will be simple input fields.

```html
<!-- Conceptual HTML-like structure for a single patient -->
<div class="section-v-systems-assessment">
  <div class="header">
    <h4>Section V: Core Systems Assessment</h4>
    <!-- Patient context (name, room) would typically be inherited from a parent component -->
  </div>

  <!-- Neurological Assessment -->
  <div class="system-assessment-group" id="neuro-assessment">
    <h5>1. Neurological</h5>
    <div class="assessment-grid">
      <div class="item"><strong>LOC:</strong> <span class="data-display">{{ neurological.loc }}</span> <input type="text" value="{{ neurological.loc }}" placeholder="LOC (e.g., A&Ox3)"></div>
      <div class="item"><strong>GCS:</strong> <span class="data-display">{{ neurological.gcs }}</span> <input type="text" value="{{ neurological.gcs }}" placeholder="GCS (e.g., E4V5M6)"></div>
      <div class="item"><strong>Pupils:</strong> <span class="data-display">{{ neurological.pupils }}</span> <input type="text" value="{{ neurological.pupils }}" placeholder="Pupils (e.g., PERRLA)"></div>
      <div class="item"><strong>Sedation Goal/RASS:</strong> <span class="data-display">{{ neurological.sedation_goal_rass }}</span> <input type="text" value="{{ neurological.sedation_goal_rass }}" placeholder="Sedation/RASS"></div>
      <div class="item"><strong>CAM-ICU:</strong> <span class="data-display">{{ neurological.cam_icu }}</span> <select><option>{{ neurological.cam_icu }}</option><option>Positive</option><option>Negative</option><option>Unable to Assess</option></select></div>
      <div class="item"><strong>Restraints:</strong> <span class="data-display">{{ neurological.restraints }}</span> <input type="text" value="{{ neurological.restraints }}" placeholder="Restraints type/reason"></div>
      <div class="item wide"><strong>Motor Strength:</strong> <span class="data-display">{{ neurological.motor_strength }}</span> <textarea placeholder="Motor strength details">{{ neurological.motor_strength }}</textarea></div>
      <div class="item wide"><strong>Neuro Notes:</strong> <span class="data-display">{{ neurological.notes }}</span> <textarea placeholder="Additional neuro observations">{{ neurological.notes }}</textarea></div>
    </div>
  </div>

  <!-- Pulmonary Assessment -->
  <div class="system-assessment-group" id="pulmonary-assessment">
    <h5>2. Pulmonary</h5>
    <div class="assessment-grid">
      <div class="item"><strong>Airway:</strong> <span class="data-display">{{ pulmonary.airway }}</span> <input type="text" value="{{ pulmonary.airway }}" placeholder="Airway (e.g., ETT, Trach, Nasal)"></div>
      <div class="item"><strong>O2 Delivery:</strong> <span class="data-display">{{ pulmonary.oxygen_delivery }}</span> <input type="text" value="{{ pulmonary.oxygen_delivery }}" placeholder="O2 Device (e.g., NC, FM, Vent)"></div>
      <div class="item"><strong>Flow/FiO2:</strong> <span class="data-display">{{ pulmonary.oxygen_flow_rate_fio2 }}</span> <input type="text" value="{{ pulmonary.oxygen_flow_rate_fio2 }}" placeholder="Flow or FiO2"></div>
      <div class="item"><strong>Resp. Rate:</strong> <span class="data-display">{{ pulmonary.respiratory_rate }}</span> <input type="text" value="{{ pulmonary.respiratory_rate }}" placeholder="RR"></div>
      <div class="item"><strong>SpO2:</strong> <span class="data-display">{{ pulmonary.spo2 }}</span> <input type="text" value="{{ pulmonary.spo2 }}" placeholder="SpO2 %"></div>
      <div class="item wide"><strong>Breath Sounds:</strong> <span class="data-display">{{ pulmonary.breath_sounds }}</span> <textarea placeholder="Auscultation findings">{{ pulmonary.breath_sounds }}</textarea></div>
      <div class="item"><strong>Cough/Sputum:</strong> <span class="data-display">{{ pulmonary.cough_sputum }}</span> <input type="text" value="{{ pulmonary.cough_sputum }}" placeholder="Cough/Sputum details"></div>
      <div class="item wide"><strong>ABG/VBG Highlights:</strong> <span class="data-display">{{ pulmonary.abg_vbg_highlights }}</span> <!-- Display Only from EMR/Labs --></div>
      <div class="item wide"><strong>Vent Settings:</strong> <span class="data-display">{{ pulmonary.ventilator_settings }}</span> <!-- Display Only or Link to Vent Flowsheet --></div>
      <div class="item"><strong>SAT/SBT Status:</strong> <span class="data-display">{{ pulmonary.sat_sbt_status }}</span> <input type="text" value="{{ pulmonary.sat_sbt_status }}" placeholder="SAT/SBT"></div>
    </div>
  </div>

  <!-- Cardiovascular Assessment -->
  <div class="system-assessment-group" id="cardio-assessment">
    <h5>3. Cardiovascular</h5>
    <div class="assessment-grid">
      <div class="item"><strong>Heart Rhythm/Rate:</strong> <span class="data-display">{{ cardiovascular.heart_rhythm_rate }}</span> <!-- Display from Monitor --></div>
      <div class="item"><strong>BP/MAP:</strong> <span class="data-display">{{ cardiovascular.bp_map }}</span> <!-- Display from Monitor --></div>
      <div class="item"><strong>Hemodynamics (PAC):</strong> <span class="data-display">{{ cardiovascular.hemodynamics_pac }}</span> <!-- Display if available --></div>
      <div class="item"><strong>Peripheral Pulses:</strong> <span class="data-display">{{ cardiovascular.peripheral_pulses }}</span> <input type="text" value="{{ cardiovascular.peripheral_pulses }}" placeholder="Peripheral pulses assessment"></div>
      <div class="item"><strong>Capillary Refill:</strong> <span class="data-display">{{ cardiovascular.capillary_refill }}</span> <input type="text" value="{{ cardiovascular.capillary_refill }}" placeholder="Cap refill"></div>
      <div class="item"><strong>Edema:</strong> <span class="data-display">{{ cardiovascular.edema }}</span> <input type="text" value="{{ cardiovascular.edema }}" placeholder="Edema location/severity"></div>
      <div class="item wide"><strong>Active Vasoactive Drips:</strong> <span class="data-display">{{ cardiovascular.active_vasoactive_drips }}</span> <!-- Display from EMAR/Infusion pumps --></div>
      <div class="item wide"><strong>Telemetry:</strong> <span class="data-display">{{ cardiovascular.telemetry }}</span> <textarea placeholder="Telemetry observations">{{ cardiovascular.telemetry }}</textarea></div>
    </div>
  </div>

  <!-- GI Assessment -->
  <div class="system-assessment-group" id="gi-assessment">
    <h5>4. GI - Gastrointestinal</h5>
    <div class="assessment-grid">
      <div class="item wide"><strong>Diet/Tube Feedings:</strong> <span class="data-display">{{ gi_gastrointestinal.diet_tube_feedings }}</span> <input type="text" value="{{ gi_gastrointestinal.diet_tube_feedings }}" placeholder="Diet order, TF type/rate"></div>
      <div class="item"><strong>Bowel Sounds:</strong> <span class="data-display">{{ gi_gastrointestinal.bowel_sounds }}</span> <input type="text" value="{{ gi_gastrointestinal.bowel_sounds }}" placeholder="Bowel sounds"></div>
      <div class="item wide"><strong>Abdomen Assessment:</strong> <span class="data-display">{{ gi_gastrointestinal.abdomen_assessment }}</span> <textarea placeholder="Abdominal assessment findings">{{ gi_gastrointestinal.abdomen_assessment }}</textarea></div>
      <div class="item"><strong>Last BM:</strong> <span class="data-display">{{ gi_gastrointestinal.last_bm }}</span> <input type="text" value="{{ gi_gastrointestinal.last_bm }}" placeholder="Date/Time/Consistency"></div>
      <div class="item"><strong>Nausea/Vomiting:</strong> <span class="data-display">{{ gi_gastrointestinal.nausea_vomiting }}</span> <select><option>{{ gi_gastrointestinal.nausea_vomiting }}</option><option>Yes</option><option>No</option></select></div>
      <div class="item"><strong>GI Output:</strong> <span class="data-display">{{ gi_gastrointestinal.gi_output }}</span> <input type="text" value="{{ gi_gastrointestinal.gi_output }}" placeholder="NG/OG/Ostomy output"></div>
      <div class="item wide"><strong>Blood Sugar Monitoring:</strong> <span class="data-display">{{ gi_gastrointestinal.blood_sugar_monitoring }}</span> <!-- Display from Labs/EMR --></div>
      <div class="item wide"><strong>Misc GI Notes:</strong> <span class="data-display">{{ gi_gastrointestinal.misc_gi_notes }}</span> <textarea placeholder="Other GI notes">{{ gi_gastrointestinal.misc_gi_notes }}</textarea></div>
    </div>
  </div>

  <!-- GU Assessment -->
  <div class="system-assessment-group" id="gu-assessment">
    <h5>5. GU - Genitourinary</h5>
    <div class="assessment-grid">
      <div class="item"><strong>Urine Output Method:</strong> <span class="data-display">{{ gu_genitourinary.urine_output_method }}</span> <input type="text" value="{{ gu_genitourinary.urine_output_method }}" placeholder="Voiding, Foley, etc."></div>
      <div class="item"><strong>Urine Output (24hr / Last Shift):</strong> <span class="data-display">{{ gu_genitourinary.urine_output_amount_24hr }}</span> <!-- Display from I/O chart --></div>
      <div class="item"><strong>Urine Characteristics:</strong> <span class="data-display">{{ gu_genitourinary.urine_characteristics }}</span> <input type="text" value="{{ gu_genitourinary.urine_characteristics }}" placeholder="Color, clarity, odor"></div>
      <div class="item wide"><strong>Renal Labs Summary (BUN/Cr):</strong> <span class="data-display">{{ gu_genitourinary.renal_labs_summary }}</span> <!-- Display from Labs --></div>
      <div class="item"><strong>Dialysis Access:</strong> <span class="data-display">{{ gu_genitourinary.dialysis_access }}</span> <input type="text" value="{{ gu_genitourinary.dialysis_access }}" placeholder="Type/Site if present"></div>
    </div>
  </div>

  <!-- Skin & Mobility Assessment -->
  <div class="system-assessment-group" id="skin-mobility-assessment">
    <h5>6. Skin & Mobility</h5>
    <div class="assessment-grid">
      <div class="item"><strong>Braden Score:</strong> <span class="data-display">{{ skin_mobility.braden_score }}</span> <!-- Display from EMR --></div>
      <div class="item wide"><strong>Skin Assessment Findings:</strong> <span class="data-display">{{ skin_mobility.skin_assessment_findings }}</span> <textarea placeholder="Detailed skin findings. Future: Link to digital body map.">{{ skin_mobility.skin_assessment_findings }}</textarea> <!-- Conceptual: Interactive Digital Body Map --></div>
      <div class="item wide"><strong>Wound Care Orders:</strong> <span class="data-display">{{ skin_mobility.wound_care_orders }}</span> <!-- Display from EMR Orders --></div>
      <div class="item wide"><strong>Pressure Injury Prevention:</strong> <span class="data-display">{{ skin_mobility.pressure_injury_prevention }}</span> <textarea placeholder="Interventions in place">{{ skin_mobility.pressure_injury_prevention }}</textarea></div>
      <div class="item"><strong>Mobility Status:</strong> <span class="data-display">{{ skin_mobility.mobility_status }}</span> <input type="text" value="{{ skin_mobility.mobility_status }}" placeholder="e.g., Bedrest, SBA x1"></div>
      <div class="item"><strong>Fall Interventions:</strong> <span class="data-display">{{ skin_mobility.fall_interventions }}</span> <input type="text" value="{{ skin_mobility.fall_interventions }}" placeholder="e.g., Bed alarm, low bed"></div>
      <div class="item"><strong>Spinal Precautions:</strong> <span class="data-display">{{ skin_mobility.spinal_precautions }}</span> <select><option>{{ skin_mobility.spinal_precautions }}</option><option>Yes</option><option>No</option></select></div>
      <div class="item"><strong>Bath:</strong> <span class="data-display">{{ skin_mobility.bath_type_schedule }}</span> <input type="text" value="{{ skin_mobility.bath_type_schedule }}" placeholder="Type/Schedule"></div>
      <div class="item"><strong>Weight:</strong> <span class="data-display">{{ skin_mobility.weight_monitoring }}</span> <!-- Display from EMR --></div>
    </div>
  </div>

  <!-- IV Access Assessment -->
  <div class="system-assessment-group" id="iv-access-assessment">
    <h5>7. IV Access / Lines</h5>
    <div class="assessment-grid">
      <!-- Loop through iv_sites_and_types -->
      {{#each iv_access_lines.iv_sites_and_types}}
      <div class="item iv-site-item wide">
        <strong>Site: {{this.site}} ({{this.type}})</strong><br>
        Patency: <span class="data-display">{{this.patency}}</span> <input type="text" value="{{this.patency}}" placeholder="Patency"><br>
        S/S Infection: <span class="data-display">{{this.s_s_infection}}</span> <input type="text" value="{{this.s_s_infection}}" placeholder="Signs of infection"><br>
        Dressing Due: <span class="data-display">{{this.dressing_change_due}}</span> <!-- Display Only -->
      </div>
      {{/each}}
      <div class="item wide"><strong>Central Line Necessity:</strong> <span class="data-display">{{ iv_access_lines.central_line_necessity }}</span> <!-- Display/Input based on policy --></div>
      <div class="item wide"><strong>IV Notes:</strong> <span class="data-display">{{ iv_access_lines.notes }}</span> <textarea placeholder="Additional IV access notes">{{ iv_access_lines.notes }}</textarea></div>
    </div>
  </div>

  <!-- Fluids & Infusions Assessment -->
  <div class="system-assessment-group" id="fluids-infusions-assessment">
    <h5>8. Fluids / Infusions / Intake</h5>
    <div class="assessment-grid">
      <div class="item wide"><strong>Continuous Infusions:</strong> <span class="data-display">{{ fluids_infusions_intake.continuous_infusions }}</span> <!-- Display from EMAR/Pumps. Could be a list. --></div>
      <div class="item wide"><strong>IVF (Maintenance/Bolus):</strong> <span class="data-display">{{ fluids_infusions_intake.ivf_maintenance_bolus }}</span> <!-- Display from EMAR/Pumps --></div>
      <div class="item wide"><strong>Blood Products:</strong> <span class="data-display">{{ fluids_infusions_intake.blood_products_overview }}</span> <!-- Display from EMAR --></div>
      <div class="item"><strong>PO Intake (Estimate):</strong> <span class="data-display">{{ fluids_infusions_intake.po_intake_estimate }}</span> <input type="text" value="{{ fluids_infusions_intake.po_intake_estimate }}" placeholder="PO Intake"></div>
      <div class="item"><strong>Fluid Balance (24hr):</strong> <span class="data-display">{{ fluids_infusions_intake.fluid_balance_24hr }}</span> <!-- Display from I/O chart --></div>
    </div>
  </div>

  <!-- Pain Assessment -->
  <div class="system-assessment-group" id="pain-assessment">
    <h5>9. Pain / Comfort</h5>
    <div class="assessment-grid">
      <div class="item"><strong>Pain Score (Current):</strong> <span class="data-display">{{ pain_comfort.pain_score_current }}</span> <input type="text" value="{{ pain_comfort.pain_score_current }}" placeholder="Score/Scale"></div>
      <div class="item"><strong>Location/Character:</strong> <span class="data-display">{{ pain_comfort.pain_location_character }}</span> <input type="text" value="{{ pain_comfort.pain_location_character }}" placeholder="Location/Type"></div>
      <div class="item"><strong>Pain Goal:</strong> <span class="data-display">{{ pain_comfort.pain_goal }}</span> <input type="text" value="{{ pain_comfort.pain_goal }}" placeholder="Patient's goal"></div>
      <div class="item wide"><strong>Non-Pharmacological Interventions:</strong> <span class="data-display">{{ pain_comfort.non_pharmacological_interventions }}</span> <textarea placeholder="Non-pharm methods used">{{ pain_comfort.non_pharmacological_interventions }}</textarea></div>
      <div class="item wide"><strong>Pharmacological Interventions:</strong> <span class="data-display">{{ pain_comfort.pharmacological_interventions }}</span> <!-- Display from EMAR, with option to add PRN admin --></div>
      <div class="item wide"><strong>Effectiveness:</strong> <span class="data-display">{{ pain_comfort.effectiveness_of_interventions }}</span> <textarea placeholder="How effective were interventions?">{{ pain_comfort.effectiveness_of_interventions }}</textarea></div>
    </div>
  </div>

  <!-- Laboratory & Diagnostics Assessment -->
  <div class="system-assessment-group" id="labs-diagnostics-assessment">
    <h5>10. Laboratory / Diagnostics</h5>
    <div class="assessment-grid">
      <div class="item wide"><strong>Abnormal Lab/Test Results (Recent):</strong>
        <ul class="data-display">
          {{#each laboratory_diagnostics.abnormal_lab_test_results}}
          <li>{{this}}</li>
          {{/each}}
        </ul>
        <!-- Display from LIS -->
      </div>
      <div class="item wide"><strong>Pending Labs/Tests:</strong>
        <ul class="data-display">
          {{#each laboratory_diagnostics.pending_labs_tests}}
          <li>{{this}}</li>
          {{/each}}
        </ul>
        <!-- Display from LIS/Orders -->
      </div>
      <div class="item wide"><strong>Recent Imaging Highlights:</strong> <span class="data-display">{{ laboratory_diagnostics.recent_imaging_highlights }}</span> <!-- Display from RIS --></div>
      <div class="item wide"><strong>Other Diagnostics Notes:</strong> <span class="data-display">{{ laboratory_diagnostics.other_diagnostics_notes }}</span> <textarea placeholder="Notes on ECG, other diagnostics">{{ laboratory_diagnostics.other_diagnostics_notes }}</textarea></div>
    </div>
  </div>

</div> <!-- End of Section V -->

<!--
Key:
- `<span class="data-display">{{ ... }}</span>`: Data primarily displayed from backend/EMR mock data.
- `<input type="text" value="{{ ... }}"> / <textarea>{{ ... }}</textarea> / <select>`: Conceptual simple input fields for MVP.
  In a real UI, these would have proper data binding and save mechanisms.
- `<!-- Display Only ... -->`: Indicates data that is almost exclusively from other systems.
- `<!-- Conceptual: ... -->`: Ideas for richer UI components beyond MVP.
- `{{#each ...}} ... {{/each}}`: Loop for list data (Handlebars-like syntax).
-->
```
