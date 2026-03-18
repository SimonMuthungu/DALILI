from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect("dalili.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT,
            risk_level TEXT,
            recommended_action TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class SymptomRequest(BaseModel):
    fever: bool
    persistent_cough: bool
    coughing_blood: bool
    fast_breathing: bool
    chest_indrawing: bool
    unexplained_weight_loss: bool
    fatigue: bool
    night_sweats: bool
    persistent_pain: bool
    lumps_swelling: bool
    chills_shivering: bool
    severe_headache: bool
    nausea_vomiting: bool
    loss_of_appetite: bool
    difficulty_swallowing: bool
    hoarseness: bool
    unexplained_bleeding: bool
    bowel_changes: bool
    chronic_indigestion: bool
    shortness_of_breath: bool
    bluish_lips: bool
    joint_muscle_pain: bool
    location: str
    voice_transcript: str = ""

@app.post("/api/assess")
def assess_risk(req: SymptomRequest):
    risk_level = "Low"
    action = "Rest, hydrate, and maintain a healthy diet. Monitor any changes in your body. Please note: This is not a formal diagnosis."
    
    # Analyze structured symptoms for Emergencies
    if req.chest_indrawing or req.bluish_lips or req.coughing_blood or req.unexplained_bleeding:
        risk_level = "Emergency"
        action = "Urgent: Visit the nearest emergency facility immediately. These are critical signs of severe respiratory distress or advanced complications. Please note: This is not a diagnosis."
    # Analyze for High Risk (Cancer / Severe Malaria)
    elif req.unexplained_weight_loss or req.lumps_swelling or req.persistent_pain or req.difficulty_swallowing or req.bowel_changes or (req.fever and req.severe_headache and req.nausea_vomiting):
        risk_level = "High"
        action = "Warning: These symptoms require immediate medical screening to rule out severe conditions like Cancer or Complicated Malaria. Please consult a specialist. This is not a diagnosis."
    # Analyze for Moderate Risk
    elif req.persistent_cough or req.night_sweats or req.shortness_of_breath or req.hoarseness or req.chronic_indigestion:
        risk_level = "Moderate"
        action = "Visit a clinic for imaging and tests. Persistent or unusal symptoms need medical evaluation. Please note: This is not a diagnosis."
    elif req.fever or req.fatigue or req.chills_shivering or req.loss_of_appetite or req.joint_muscle_pain:
        risk_level = "Moderate"
        action = "Consider seeing a doctor for a checkup, especially if symptoms persist or worsen. Monitor closely. Please note: This is not a diagnosis."

    # Parse voice transcript for keywords (simulating AI NLP)
    transcript = req.voice_transcript.lower()
    if "blood" in transcript or "lump" in transcript or "lost weight" in transcript or "bleeding" in transcript:
        risk_level = "High"
        action = "Warning: Described symptoms require immediate medical screening to rule out severe conditions. Please consult a specialist. This is not a diagnosis."
    elif "can't breathe" in transcript or "chest hurts" in transcript or "blue" in transcript:
        risk_level = "Emergency"
        action = "Urgent: Based on your description, visit an emergency facility immediately. Please note: This is not a formal diagnosis."

    # compile selected symptoms
    symptoms_map = {
        'fever': 'Fever', 'persistent_cough': 'Persistent Cough', 'coughing_blood': 'Coughing Blood',
        'fast_breathing': 'Fast Breathing', 'chest_indrawing': 'Chest Indrawing', 
        'unexplained_weight_loss': 'Unexplained Weight Loss', 'fatigue': 'Extreme Fatigue', 
        'night_sweats': 'Night Sweats', 'persistent_pain': 'Persistent Pain', 
        'lumps_swelling': 'Lumps or Swelling', 'chills_shivering': 'Chills/Shivering',
        'severe_headache': 'Severe Headache', 'nausea_vomiting': 'Nausea/Vomiting',
        'loss_of_appetite': 'Loss of Appetite', 'difficulty_swallowing': 'Difficulty Swallowing',
        'hoarseness': 'Hoarseness of Voice', 'unexplained_bleeding': 'Unexplained Bleeding',
        'bowel_changes': 'Changes in Bowel Habits', 'chronic_indigestion': 'Chronic Indigestion',
        'shortness_of_breath': 'Shortness of Breath', 'bluish_lips': 'Bluish Lips/Face',
        'joint_muscle_pain': 'Joint/Muscle Pain'
    }
    
    symptoms_list = []
    # Using python getattr or dictionary
    req_dict = req.dict()
    for key, human_readable in symptoms_map.items():
        if req_dict.get(key):
            symptoms_list.append(human_readable)
            
    if req.voice_transcript: 
        symptoms_list.append("Voice Entry Analyzed")
    
    symptoms_str = ", ".join(symptoms_list)
    
    conn = sqlite3.connect("dalili.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO assessments (symptoms, risk_level, recommended_action) VALUES (?, ?, ?)",
        (symptoms_str, risk_level, action)
    )
    conn.commit()
    conn.close()
    
    return {
        "risk_level": risk_level,
        "recommended_action": action,
        "symptoms": symptoms_list
    }

@app.get("/api/assessments")
def get_assessments():
    conn = sqlite3.connect("dalili.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assessments ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "symptoms": row[1],
            "risk_level": row[2],
            "recommended_action": row[3],
            "timestamp": row[4]
        })
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
