from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import random
import os
import joblib
import numpy as np
import speech_recognition as sr

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
model_features = []
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "symptom_model.pkl")
features_path = os.path.join(BASE_DIR, "model_features.pkl")

try:
    if os.path.exists(model_path) and os.path.exists(features_path):
        model = joblib.load(model_path)
        model_features = joblib.load(features_path)
        print("ML model loaded successfully.")
    else:
        print("ML model not found. Will use heuristic fallback only.")
except Exception as e:
    print(f"Error loading ML model: {e}")

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
    language: str = "English"

@app.post("/api/assess")
def assess_risk(req: SymptomRequest):
    req_dict = req.dict()
    transcript = req.voice_transcript.lower()
    
    # Simple NLP from voice transcript to check missing symptoms
    voice_keywords = {
        'fever': ['fever', 'hot', 'temperature', 'joto', 'homa', 'mwili moto', 'theri'],
        'persistent_cough': ['cough', 'coughing', 'kukohoa', 'kikohozi', 'gukorora', 'gukorera', 'ahonda'],
        'coughing_blood': ['blood in cough', 'coughing blood', 'kohoa damu', 'korora thakame', 'ngokorora thakame', 'ahonda remo'],
        'shortness_of_breath': ['breath', 'breathing', 'kupumua', 'hewa', 'kuhema', 'kuhuka'],
        'fast_breathing': ['fast breathing', 'panting', 'kuhema haraka'],
        'chest_indrawing': ['chest pain', 'chest hurt', 'kifua', 'kifua inauma', 'githuri', 'kithuri inuma', 'koro kor'],
        'bluish_lips': ['blue lips', 'lips blue', 'midomo buluu'],
        'unexplained_weight_loss': ['weight loss', 'losing weight', 'kukonda', 'kupunguza uzito', 'kuhinju'],
        'fatigue': ['tired', 'fatigue', 'weak', 'kuchoka', 'nginya', 'dhilu'],
        'night_sweats': ['sweat', 'sweating at night', 'kutoka jasho', 'jasho ya usiku', 'kuira jasho', 'luya'],
        'persistent_pain': ['pain', 'hurts', 'uchungu', 'maumivu', 'kuuma', 'remo'],
        'lumps_swelling': ['lump', 'swelling', 'uvimbe', 'kuvimba', 'gutu', 'kudunda'],
        'chills_shivering': ['cold', 'shivering', 'chills', 'kutetemeka', 'baridi', 'heho', 'kigutha'],
        'severe_headache': ['headache', 'head hurts', 'kichwa', 'kichwa kinauma', 'mutwe inuma', 'wich'],
        'nausea_vomiting': ['vomit', 'nausea', 'throw up', 'kutapika', 'kuhaka', 'gukunga', 'ngokwa'],
        'loss_of_appetite': ['appetite', 'not eating', 'sitaki kula', 'kosa hamu ya kula', 'gukua mukanwa', 'kwonda'],
        'difficulty_swallowing': ['swallow', 'kumeza', 'kumeria'],
        'hoarseness': ['voice', 'hoarse', 'sauti', 'mugu', 'dwol'],
        'unexplained_bleeding': ['bleeding', 'blood', 'damu', 'thakame', 'remo'],
        'bowel_changes': ['bowel', 'stool', 'diarrhea', 'kuhara', 'kuhara damu', 'gutu'],
        'chronic_indigestion': ['indigestion', 'stomach', 'tumbo', 'tumau', 'yath'],
        'joint_muscle_pain': ['joint', 'muscle', 'ache', 'maumivu', 'machungu', 'mahinda', 'liteng']
    }

    # Automatically flag symptoms identified in the transcript
    for key, keywords in voice_keywords.items():
        if not req_dict.get(key):
            for kw in keywords:
                if kw in transcript:
                    req_dict[key] = True
                    break

    # Advanced Scoring Logic
    scores = {
        "Malaria": 0,
        "Pneumonia": 0,
        "Lung Cancer": 0,
        "Throat Cancer": 0,
        "Gastrointestinal Cancer": 0,
        "Leukemia/Blood Cancer": 0
    }

    # Malaria Weights
    if req_dict.get('fever'): scores["Malaria"] += 3
    if req_dict.get('chills_shivering'): scores["Malaria"] += 2
    if req_dict.get('severe_headache'): scores["Malaria"] += 2
    if req_dict.get('nausea_vomiting'): scores["Malaria"] += 1
    if req_dict.get('fatigue'): scores["Malaria"] += 1
    if req_dict.get('joint_muscle_pain'): scores["Malaria"] += 2

    # Pneumonia Weights
    if req_dict.get('fever'): scores["Pneumonia"] += 2
    if req_dict.get('persistent_cough'): scores["Pneumonia"] += 3
    if req_dict.get('shortness_of_breath'): scores["Pneumonia"] += 2
    if req_dict.get('fast_breathing'): scores["Pneumonia"] += 2
    if req_dict.get('chest_indrawing'): scores["Pneumonia"] += 3
    if req_dict.get('bluish_lips'): scores["Pneumonia"] += 3

    # Lung Cancer Weights
    if req_dict.get('persistent_cough'): scores["Lung Cancer"] += 2
    if req_dict.get('coughing_blood'): scores["Lung Cancer"] += 4
    if req_dict.get('shortness_of_breath'): scores["Lung Cancer"] += 2
    if req_dict.get('unexplained_weight_loss'): scores["Lung Cancer"] += 3
    if req_dict.get('persistent_pain'): scores["Lung Cancer"] += 2

    # Throat Cancer Weights
    if req_dict.get('hoarseness'): scores["Throat Cancer"] += 4
    if req_dict.get('difficulty_swallowing'): scores["Throat Cancer"] += 4
    if req_dict.get('lumps_swelling'): scores["Throat Cancer"] += 2
    
    # Gastrointestinal Cancer
    if req_dict.get('bowel_changes'): scores["Gastrointestinal Cancer"] += 3
    if req_dict.get('chronic_indigestion'): scores["Gastrointestinal Cancer"] += 2
    if req_dict.get('nausea_vomiting'): scores["Gastrointestinal Cancer"] += 1
    if req_dict.get('unexplained_weight_loss'): scores["Gastrointestinal Cancer"] += 2
    if req_dict.get('unexplained_bleeding'): scores["Gastrointestinal Cancer"] += 3

    # Leukemia/Blood Cancer
    if req_dict.get('fatigue'): scores["Leukemia/Blood Cancer"] += 1
    if req_dict.get('unexplained_bleeding'): scores["Leukemia/Blood Cancer"] += 4
    if req_dict.get('night_sweats'): scores["Leukemia/Blood Cancer"] += 2
    if req_dict.get('lumps_swelling'): scores["Leukemia/Blood Cancer"] += 3
    
    max_condition = max(scores, key=scores.get)
    max_score = scores[max_condition]

    # Assign base risk and general action depending on the top score
    risk_level = "Low"
    condition_detected = "None"
    
    if max_score == 0:
        risk_level = "Low"
        base_action_key = "low_risk"
    elif max_score <= 3:
        risk_level = "Moderate"
        base_action_key = "moderate"
    elif max_score <= 6:
        risk_level = "High"
        base_action_key = "high"
        condition_detected = max_condition
    else:
        risk_level = "Emergency"
        base_action_key = "emergency"
        condition_detected = max_condition

    # Emergency overrides
    if req_dict.get('bluish_lips') or req_dict.get('chest_indrawing') or req_dict.get('coughing_blood'):
        risk_level = "Emergency"

    loc_val = req.location.strip()
    loc_text_en = f" in {loc_val}" if loc_val and loc_val.lower() != "unknown" else ""
    loc_text_sw = f" eneo la {loc_val}" if loc_val and loc_val.lower() != "unknown" else ""
    loc_text_ki = f" kũu {loc_val}" if loc_val and loc_val.lower() != "unknown" else ""
    loc_text_lu = f" machiegni gi {loc_val}" if loc_val and loc_val.lower() != "unknown" else ""

    # Multi-lingual dictionary
    advice_db = {
        "English": {
            "low_risk": f"Rest, hydrate, and maintain a healthy diet. You seem fine{loc_text_en}.",
            "moderate": f"You have some symptoms. Consider seeing a doctor{loc_text_en} if they persist.",
            "Malaria": f"Visit the nearest doctor{loc_text_en} since it looks like you have Malaria. Find a treated net and get tested.",
            "Pneumonia": f"Visit a clinic{loc_text_en} immediately as it looks like you have Pneumonia. Keep warm and avoid the cold.",
            "Lung Cancer": f"Warning: Your symptoms suggest severe respiratory risk. See an oncologist{loc_text_en} for a scan immediately.",
            "Throat Cancer": f"Warning: Severe throat symptoms detected. Please consult an ENT specialist{loc_text_en}.",
            "Gastrointestinal Cancer": f"Warning: Persistent stomach/bowel issues detected. Visit a specialist{loc_text_en} for screening.",
            "Leukemia/Blood Cancer": f"Warning: Unexplained bleeding and fatigue are dangerous. Visit a hospital{loc_text_en} soon."
        },
        "Swahili": {
            "low_risk": f"Pumzika, kunywa maji mengi na ule vizuri{loc_text_sw}. Unaonekana mzima.",
            "moderate": f"Una baadhi ya dalili. Fikiria kuona daktari{loc_text_sw} ikiwa zitaendelea.",
            "Malaria": f"Tembelea daktari aliye karibu{loc_text_sw} kwani inaonekana una Malaria. Tafuta chandarua kilichotibiwa.",
            "Pneumonia": f"Nenda zahanati{loc_text_sw} mara moja kwani inaonekana una Nimonia. Vaa nguo za joto na epuka baridi.",
            "Lung Cancer": f"Onyo: Dalili zinaashiria hatari ya kupumua. Muone daktari bingwa{loc_text_sw}.",
            "Throat Cancer": f"Onyo: Dalili za koo zimegunduliwa. Tafadhali muone daktari wa koo{loc_text_sw}.",
            "Gastrointestinal Cancer": f"Onyo: Matatizo ya tumbo yamegunduliwa. Tembelea mtaalamu{loc_text_sw} kwa uchunguzi.",
            "Leukemia/Blood Cancer": f"Onyo: Kutokwa na damu ni hatari. Tembelea hospitali{loc_text_sw} kwa kipimo cha damu haraka."
        },
        "Kikuyu": {
            "low_risk": "Huruka, nyua mai maingi na urie wega. Uraonekana uri mwega.",
            "moderate": f"Wina tumenyerero. Thiĩ kũrĩ ndagĩtarĩ{loc_text_ki} kũngĩkorwo niituremwo.",
            "Malaria": f"Thiĩ kũrĩ ndagĩtarĩ akorwo nĩ hakuhĩ{loc_text_ki} tondũ wonekana ũrĩ na Malaria. Caria neti.",
            "Pneumonia": f"Thiĩ thibitarĩ{loc_text_ki} na ihenya tondũ wonekana ũrĩ na homa ya mapafu. Wĩhumbĩre wega.",
            "Lung Cancer": f"Utaaro mwororo: Onana na ndagĩtarĩ{loc_text_ki} na ihenya kaba kansa.",
            "Throat Cancer": f"Utaaro mwororo: Tumenyerero twa mumero. Onana na thibitari{loc_text_ki}.",
            "Gastrointestinal Cancer": f"Utaaro mwororo: Tumenyerero twa nda. Thiĩ thibitari{loc_text_ki} ucaririe ukui.",
            "Leukemia/Blood Cancer": f"Utaaro mwororo: Kuuma thakame gwi ugwati. Thiĩ guthima thakame{loc_text_ki}."
        },
        "Luo": {
            "low_risk": "Yweyo, madh pi kendo cham maber. Inenore maber.",
            "moderate": f"In gi ranyisi moko. Dhi ir laktar{loc_text_lu} ka gidhiero.",
            "Malaria": f"Dhi ir laktar{loc_text_lu} nikech inenore ni in gi Malaria. Many net mosekethi kendo ipimi.",
            "Pneumonia": f"Dhi ir klinik{loc_text_lu} mapiyo nikech inenore ni in gi Pneumonia. Rwak nanga malit.",
            "Lung Cancer": f"Tango: Ranyisi magi nyiso kethruok e ote. Dhi ir laktar{loc_text_lu} mapiyo.",
            "Throat Cancer": f"Tango: Ranyisi mar dhood ote moneno. Kwayi iyiud laktar{loc_text_lu} mar duol.",
            "Gastrointestinal Cancer": f"Tango: Ranyisi mar ich. Dhi ir laktar{loc_text_lu} mag ng'enyo ich.",
            "Leukemia/Blood Cancer": f"Tango: Chwer remo maonge gima kelo ok ber. Dhi pimi remo thoth{loc_text_lu}."
        }
    }

    req_lang = req.language
    if req_lang not in advice_db:
        req_lang = "English"

    if condition_detected in advice_db[req_lang] and risk_level in ["High", "Emergency"]:
        action = advice_db[req_lang][condition_detected]
    elif base_action_key in advice_db[req_lang]:
        action = advice_db[req_lang][base_action_key]
    else:
        action = advice_db[req_lang]["moderate"]

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
        "symptoms": symptoms_list,
        "detected_condition": condition_detected
    }

@app.get("/api/transcribe-backend")
def transcribe_backend():
    r = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("Listening for 6 seconds...")
            # Use record instead of listen to completely bypass the Windows PyAudio 
            # silence-detection deadlock. It records for EXACTLY 6 seconds.
            audio = r.record(source, duration=5)
            print("Processing speech...")
            # Send to Google Speech Recognition 
            text = r.recognize_google(audio)
            print("Transcript: ", text)
            return {"transcript": text}
    except sr.UnknownValueError:
        return {"error": "Could not understand the audio. Please try again."}
    except sr.RequestError as e:
        return {"error": f"Speech API error: {e}"}
    except Exception as e:
        return {"error": f"Audio source error: {e}"}

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
