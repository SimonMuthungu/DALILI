import { useState, useEffect, useRef } from 'react';
import './App.css';

const SYMPTOM_DEFINITIONS = [
    // General / Malaria
    { name: 'fever', label: 'Fever', danger: false, category: 'General' },
    { name: 'chills_shivering', label: 'Chills or Shivering', danger: false, category: 'General' },
    { name: 'severe_headache', label: 'Severe Headache', danger: false, category: 'General' },
    { name: 'nausea_vomiting', label: 'Nausea or Vomiting', danger: false, category: 'General' },
    { name: 'joint_muscle_pain', label: 'Joint or Muscle Pain', danger: false, category: 'General' },
    { name: 'fatigue', label: 'Extreme Fatigue', danger: false, category: 'General' },

    // Respiratory / Pneumonia
    { name: 'persistent_cough', label: 'Persistent Cough', danger: false, category: 'Respiratory' },
    { name: 'shortness_of_breath', label: 'Shortness of Breath', danger: false, category: 'Respiratory' },
    { name: 'fast_breathing', label: 'Fast Breathing', danger: false, category: 'Respiratory' },
    { name: 'chest_indrawing', label: 'Chest Indrawing', danger: true, category: 'Respiratory' },
    { name: 'bluish_lips', label: 'Bluish Lips or Face', danger: true, category: 'Respiratory' },

    // Cancer Red Flags
    { name: 'coughing_blood', label: 'Coughing Blood', danger: true, category: 'Advanced' },
    { name: 'unexplained_weight_loss', label: 'Unexplained Weight Loss', danger: true, category: 'Advanced' },
    { name: 'lumps_swelling', label: 'Lumps or Swelling', danger: true, category: 'Advanced' },
    { name: 'difficulty_swallowing', label: 'Difficulty Swallowing', danger: true, category: 'Advanced' },
    { name: 'hoarseness', label: 'Hoarseness of Voice', danger: true, category: 'Advanced' },
    { name: 'unexplained_bleeding', label: 'Unexplained Bleeding/Bruising', danger: true, category: 'Advanced' },
    { name: 'bowel_changes', label: 'Changes in Bowel Habits', danger: true, category: 'Advanced' },

    // Other
    { name: 'night_sweats', label: 'Night Sweats', danger: false, category: 'Other' },
    { name: 'persistent_pain', label: 'Persistent Pain', danger: false, category: 'Other' },
    { name: 'loss_of_appetite', label: 'Loss of Appetite', danger: false, category: 'Other' },
    { name: 'chronic_indigestion', label: 'Chronic Indigestion', danger: false, category: 'Other' }
];

function App() {
    const [formData, setFormData] = useState({
        fever: false,
        persistent_cough: false,
        shortness_of_breath: false,
        coughing_blood: false,
        fast_breathing: false,
        chest_indrawing: false,
        bluish_lips: false,
        unexplained_weight_loss: false,
        fatigue: false,
        night_sweats: false,
        persistent_pain: false,
        lumps_swelling: false,
        chills_shivering: false,
        severe_headache: false,
        nausea_vomiting: false,
        loss_of_appetite: false,
        difficulty_swallowing: false,
        hoarseness: false,
        unexplained_bleeding: false,
        bowel_changes: false,
        chronic_indigestion: false,
        joint_muscle_pain: false,
        location: '',
        voice_transcript: ''
    });

    const [language, setLanguage] = useState('English');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [history, setHistory] = useState([]);
    const [recording, setRecording] = useState(false);

    const speakText = (text, lang) => {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            if (lang === "Swahili") {
                utterance.lang = "sw-KE";
            } else if (lang === "English") {
                utterance.lang = "en-KE";
            }
            // For Luo and Kikuyu, use default system voice as best effort
            window.speechSynthesis.speak(utterance);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const fetchHistory = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/assessments');
            const data = await res.json();
            setHistory(data);
        } catch (error) {
            console.error('Error fetching history:', error);
        }
    };

    const handleCheckboxChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.checked
        });
    };

    const handleInputChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    // Fall back to backend Python STT to bypass the browser 'network' error.
    const toggleRecording = async () => {
        if (recording) {
            return; // Backend is already listening
        }

        setRecording(true);
        // Fixed 6s length from backend

        try {
            const res = await fetch('http://localhost:8000/api/transcribe-backend');
            const data = await res.json();

            if (data.transcript) {
                setFormData(prev => ({
                    ...prev,
                    voice_transcript: prev.voice_transcript ? prev.voice_transcript + " " + data.transcript : data.transcript
                }));
            } else if (data.error) {
                alert("Transcription Error: " + data.error);
            }
        } catch (error) {
            console.error("Backend STT error:", error);
            alert("Failed to connect to backend STT server.");
        } finally {
            setRecording(false);
        }
    };

    const handleSubmit = async (e, forceVoiceOnly = false) => {
        if (e) e.preventDefault();
        setLoading(true);
        setResult(null);

        let payload = { ...formData, language };

        if (forceVoiceOnly) {
            // Clear all manual symptoms
            const emptySymptoms = {};
            SYMPTOM_DEFINITIONS.forEach(symp => {
                emptySymptoms[symp.name] = false;
            });
            payload = { ...emptySymptoms, location: formData.location || 'Unknown', voice_transcript: formData.voice_transcript, language };
        }

        try {
            const res = await fetch('http://localhost:8000/api/assess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            setResult(data);
            speakText(data.recommended_action, language);
            fetchHistory(); // Refresh history
        } catch (error) {
            console.error('Error submitting form:', error);
            alert('Failed to connect to the backend server. Make sure it is running on port 8000.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-container">
            <div className="hero">
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
                    <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        style={{ padding: '0.5rem', borderRadius: '8px', border: 'none', backgroundColor: 'rgba(255,255,255,0.2)', color: 'white', fontWeight: 'bold' }}
                    >
                        <option value="English" style={{ color: 'black' }}>English</option>
                        <option value="Swahili" style={{ color: 'black' }}>Swahili</option>
                        <option value="Kikuyu" style={{ color: 'black' }}>Kikuyu</option>
                        <option value="Luo" style={{ color: 'black' }}>Luo</option>
                    </select>
                </div>
                <h1>DALILI</h1>
                <p>Comprehensive Early Risk Assessment for Pneumonia, Malaria & Cancer</p>
            </div>

            <div className="glass-card">
                <h2>Describe How You Feel</h2>
                <p style={{ marginBottom: '1rem', color: '#6b7280' }}>Use the microphone to describe your symptoms naturally.</p>

                <div className="voice-input-container">
                    <button
                        type="button"
                        className={`mic-btn ${recording ? 'recording' : ''}`}
                        onClick={toggleRecording}
                        disabled={recording}
                    >
                        {recording ? '🔴 Listening (Auto-stops in 6s)...' : '🎤 Tap to Speak'}
                    </button>

                    <textarea
                        className="transcript-box"
                        name="voice_transcript"
                        value={formData.voice_transcript}
                        readOnly
                        placeholder="Your voice input will appear here..."
                        rows="3"
                        style={{ marginBottom: '1rem' }}
                    />
                    <button
                        type="button"
                        className="btn-submit"
                        style={{ backgroundColor: '#10b981' }}
                        onClick={() => handleSubmit(null, true)}
                        disabled={loading || !formData.voice_transcript}
                    >
                        {loading ? 'Analyzing Voice...' : 'Assess Comprehensive Risk (Voice Only)'}
                    </button>
                </div>
            </div>

            <div className="glass-card">
                <h2>Comprehensive Tracker</h2>
                <p style={{ marginBottom: '1.5rem', color: '#6b7280' }}>Select any and all symptoms that apply to your current condition.</p>
                <form onSubmit={handleSubmit}>

                    <div className="form-grid">
                        {['General', 'Respiratory', 'Advanced', 'Other'].map(cat => (
                            <div key={cat} style={{ gridColumn: '1 / -1', marginBottom: '1rem' }}>
                                <h3 style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: '0.5rem', marginBottom: '1rem', fontSize: '1rem' }}>{cat}</h3>
                                <div className="form-grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))' }}>
                                    {SYMPTOM_DEFINITIONS.filter(s => s.category === cat).map(symp => (
                                        <label key={symp.name} className={`checkbox-group ${symp.danger ? 'danger-checkbox' : ''}`}>
                                            <input
                                                type="checkbox"
                                                name={symp.name}
                                                checked={formData[symp.name]}
                                                onChange={handleCheckboxChange}
                                            />
                                            {symp.label}
                                        </label>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="input-group" style={{ marginBottom: '2rem', marginTop: '1rem' }}>
                        <label htmlFor="location">Your Location (County/Town)</label>
                        <input
                            type="text"
                            id="location"
                            name="location"
                            placeholder="e.g., Kisumu, Maseno..."
                            value={formData.location}
                            onChange={handleInputChange}
                            required
                        />
                    </div>

                    <button type="submit" className="btn-submit" disabled={loading}>
                        {loading ? 'Analyzing Profile...' : 'Assess Comprehensive Risk'}
                    </button>
                </form>
            </div>

            {result && (
                <div className="glass-card result-card">
                    <h2>Assessment Result</h2>
                    {result.detected_condition !== 'None' && result.detected_condition && (
                        <h3 style={{ color: '#ec4899', fontSize: '1.25rem', marginBottom: '1rem' }}>Condition Match: {result.detected_condition}</h3>
                    )}
                    <div className={`risk-badge risk-level-${result.risk_level}`}>
                        {result.risk_level} Risk
                    </div>
                    <p><strong>Action Required:</strong> {result.recommended_action}</p>
                    <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '1rem' }}>
                        Detected Risk Factors: {result.symptoms.length > 0 ? result.symptoms.join(', ') : 'None'}
                    </div>
                    <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '1rem' }}>
                        Disclaimer: This is not to be replaced with medical advice. Seek medical attention where necessary.
                    </div>
                </div>
            )}

            {history.length > 0 && (
                <div className="glass-card">
                    <h2>Recent Anonymous Assessments</h2>
                    <ul className="history-list">
                        {history.map((item) => (
                            <li key={item.id} className="history-item">
                                <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                                    {new Date(item.timestamp).toLocaleString()}
                                </span>
                                <span style={{
                                    fontWeight: '600',
                                    color: item.risk_level === 'Emergency' ? '#ef4444' : item.risk_level === 'High' ? '#f59e0b' : '#10b981'
                                }}>
                                    {item.risk_level}
                                </span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default App;
