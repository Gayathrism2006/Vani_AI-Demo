import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LoginPage from './components/LoginPage';
import SetupPage from './components/SetupPage';
import AssessmentPage from './components/AssessmentPage';
import SuccessPage from './components/SuccessPage';
import ReviewPage from './components/ReviewPage';

export default function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('vani_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('vani_token') || '');
  const [view, setView] = useState(() => {
    return localStorage.getItem('vani_user') ? 'SETUP' : 'LOGIN';
  });
  
  const [systemStatus, setSystemStatus] = useState(null);
  const [currentAssessment, setCurrentAssessment] = useState(null);
  const [reviewAssessmentId, setReviewAssessmentId] = useState(null);

  // Fetch system status (OpenVoice, ElevenLabs, OpenAI)
  useEffect(() => {
    fetch('/api/system/status')
      .then((res) => res.json())
      .then((data) => setSystemStatus(data))
      .catch((err) => console.error('Failed to fetch system status:', err));
  }, []);

  const handleLoginSuccess = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
    localStorage.setItem('vani_user', JSON.stringify(userData));
    localStorage.setItem('vani_token', userToken);
    setView('SETUP');
  };

  const handleLogout = () => {
    setUser(null);
    setToken('');
    setCurrentAssessment(null);
    localStorage.removeItem('vani_user');
    localStorage.removeItem('vani_token');
    setView('LOGIN');
  };

  const handleAssessmentStarted = (assessmentData) => {
    setCurrentAssessment(assessmentData);
    setView('ASSESSMENT');
  };

  const handleSubmitted = (assessmentId) => {
    setReviewAssessmentId(assessmentId);
    setView('SUCCESS');
  };

  const handleGoToReview = (assessmentId) => {
    setReviewAssessmentId(assessmentId);
    setView('REVIEW');
  };

  const handleBackToSetup = () => {
    setCurrentAssessment(null);
    setView('SETUP');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header
        user={user}
        onLogout={handleLogout}
        systemStatus={systemStatus}
      />

      <main style={{ flex: 1 }}>
        {view === 'LOGIN' && (
          <LoginPage onLoginSuccess={handleLoginSuccess} />
        )}

        {view === 'SETUP' && (
          <SetupPage
            user={user}
            onAssessmentStarted={handleAssessmentStarted}
            systemStatus={systemStatus}
          />
        )}

        {view === 'ASSESSMENT' && currentAssessment && (
          <AssessmentPage
            assessment={currentAssessment}
            onSubmitted={handleSubmitted}
          />
        )}

        {view === 'SUCCESS' && (
          <SuccessPage
            assessmentId={reviewAssessmentId || currentAssessment?.assessment_id}
            onGoToReview={handleGoToReview}
          />
        )}

        {view === 'REVIEW' && (
          <ReviewPage
            assessmentId={reviewAssessmentId || currentAssessment?.assessment_id}
            onBackToSetup={handleBackToSetup}
          />
        )}
      </main>
    </div>
  );
}
