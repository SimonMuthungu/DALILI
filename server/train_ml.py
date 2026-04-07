import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# 22 symptom features
features = [
    'fever', 'persistent_cough', 'coughing_blood', 'fast_breathing', 'chest_indrawing',
    'unexplained_weight_loss', 'fatigue', 'night_sweats', 'persistent_pain',
    'lumps_swelling', 'chills_shivering', 'severe_headache', 'nausea_vomiting',
    'loss_of_appetite', 'difficulty_swallowing', 'hoarseness', 'unexplained_bleeding',
    'bowel_changes', 'chronic_indigestion', 'shortness_of_breath', 'bluish_lips',
    'joint_muscle_pain'
]

X = []
y = []

# Generate synthetic dataset to bootstrap the ML model from the existing heuristics
for i in range(5000):
    row = np.random.randint(0, 2, size=len(features))
    req = dict(zip(features, row))
    
    risk = "Low"
    if req['chest_indrawing'] or req['bluish_lips'] or req['coughing_blood'] or req['unexplained_bleeding']:
        risk = "Emergency"
    elif req['unexplained_weight_loss'] or req['lumps_swelling'] or req['persistent_pain'] or req['difficulty_swallowing'] or req['bowel_changes'] or (req['fever'] and req['severe_headache'] and req['nausea_vomiting']):
        risk = "High"
    elif req['persistent_cough'] or req['night_sweats'] or req['shortness_of_breath'] or req['hoarseness'] or req['chronic_indigestion'] or req['fever'] or req['fatigue'] or req['chills_shivering'] or req['loss_of_appetite'] or req['joint_muscle_pain']:
        risk = "Moderate"

    # Add noise
    if np.random.rand() < 0.10:
        risk = np.random.choice(["Low", "Moderate", "High", "Emergency"])

    X.append(row)
    y.append(risk)

# Train the model
clf = RandomForestClassifier(n_estimators=50, random_state=42)
clf.fit(X, y)

# Save the model and features
joblib.dump(clf, "symptom_model.pkl")
joblib.dump(features, "model_features.pkl")
print("Model created and saved successfully.")
