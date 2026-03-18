import { useState, useEffect } from 'react';
import './App.css';

const SYMPTOM_DEFINITIONS = [
  { name: 'fever', label: 'Fever', danger: false },
  { name: 'persistent_cough', label: 'Persistent Cough', danger: false },
  { name: 'shortness_of_breath', label: 'Shortness of Breath', danger: false },
  { name: 'coughing_blood', label: 'Coughing Blood', danger: true },
  { name: 'fast_breathing', label: 'Fast Breathing', danger: false },
  { name: 'chest_indrawing', label: 'Chest Indrawing', danger: true },
  { name: 'bluish_lips', label: 'Bluish Lips or Face', danger: true },
  { name: 'unexplained_weight_loss', label: 'Unexplained Weight Loss', danger: true },
  { name: 'fatigue', label: 'Extreme Fatigue', danger: false },
  { name: 'night_sweats', label: 'Night Sweats', danger: false },
  { name: 'persistent_pain', label: 'Persistent Pain', danger: false },
  { name: 'lumps_swelling', label: 'Lumps or Swelling', danger: true },
  { name: 'chills_shivering', label: 'Chills or Shivering', danger: false },
  { name: 'severe_headache', label: 'Severe Headache', danger: false },
  { name: 'nausea_vomiting', label: 'Nausea or Vomiting', danger: false },
  { name: 'loss_of_appetite', label: 'Loss of Appetite', danger: false },
  { name: 'difficulty_swallowing', label: 'Difficulty Swallowing', danger: true },
  { name: 'hoarseness', label: 'Hoarseness of Voice', danger: false },
  { name: 'unexplained_bleeding', label: 'Unexplained Bleeding/Bruising', danger: true },
  { name: 'bowel_changes', label: 'Changes in Bowel Habits', danger: true },
  { name: 'chronic_indigestion', label: 'Chronic Indigestion', danger: false },
  { name: 'joint_muscle_pain', label: 'Joint or Muscle Pain', danger: false }
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

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [recording, setRecording] = useState(false);

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

  // Proof of concept voice recording
  const startRecording = () => {
    setRecording(true);
    // Simulate recording delay, then "transcribe" what they might say.
    setTimeout(() => {
      setFormData({
        ...formData,
        voice_transcript: "I have been coughing for weeks, feels like my chest hurts, I lost a lot of weight and I noticed some strange bleeding."
      });
      setRecording(false);
    }, 3000);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch('http://localhost:8000/api/assess', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      setResult(data);
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
        <h1>DALILI</h1>
        <p>Comprehensive Early Risk Assessment for Pneumonia, Malaria & Cancer</p>
      </div>

      <div className="glass-card">
        <h2>Describe How You Feel</h2>
        <p style={{marginBottom: '1rem', color: '#6b7280'}}>Use the microphone to describe your symptoms naturally, or type them below.</p>
        
        <div className="voice-input-container">
          <button 
            type="button" 
            className={`mic-btn ${recording ? 'recording' : ''}`}
            onClick={startRecording}
          >
            {recording ? '🔴 Listening...' : '🎤 Tap to Speak'}
          </button>
          
          <textarea
            className="transcript-box"
            name="voice_transcript"
            value={formData.voice_transcript}
            onChange={handleInputChange}
            placeholder="Your voice input will appear here..."
            rows="3"
          />
        </div>
      </div>

      <div className="glass-card">
        <h2>Comprehensive Tracker</h2>
        <p style={{marginBottom: '1.5rem', color: '#6b7280'}}>Select any and all symptoms that apply to your current condition.</p>
        <form onSubmit={handleSubmit}>
          
          <div className="form-grid">
            {SYMPTOM_DEFINITIONS.map(symp => (
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
          <div className={`risk-badge risk-level-${result.risk_level}`}>
            {result.risk_level} Risk
          </div>
          <p><strong>Action Required:</strong> {result.recommended_action}</p>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '1rem' }}>
            Detected Risk Factors: {result.symptoms.length > 0 ? result.symptoms.join(', ') : 'None'}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="glass-card">
          <h2>Recent Anonymous Assessments</h2>
          <ul className="history-list">
            {history.map((item) => (
              <li key={item.id} className="history-item">
                <span style={{color: '#6b7280', fontSize: '0.875rem'}}>
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
