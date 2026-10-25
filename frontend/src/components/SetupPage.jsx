import React, { useState, useRef, useEffect } from 'react';
import {
  Code2, Globe2, Sparkles, Volume2, ArrowRight, CheckCircle2,
  AlertTriangle, Loader2, ShieldCheck, FileText, Mic, Square,
  Play, Pause, RotateCcw, X, ShieldAlert
} from 'lucide-react';

const PROGRAMMING_LANGUAGES = [
  { value: 'Python', label: 'Python (Generators, AsyncIO, OOP, Memory)' },
  { value: 'Java', label: 'Java (JVM, Thread Pools, JPA, Virtual Threads)' },
  { value: 'JavaScript', label: 'JavaScript (Event Loop, Async, Closures, DOM)' },
  { value: 'TypeScript', label: 'TypeScript (Generics, Type Narrowing, Architecture)' },
  { value: 'C++', label: 'C++ (Memory Management, RAII, Concurrency, Pointers)' },
  { value: 'C#', label: 'C# (.NET Core, Async/Await, LINQ, Memory)' },
  { value: 'C', label: 'C (Systems Programming, Pointer Arithmetic, Structs)' },
  { value: 'SQL', label: 'SQL (Query Optimization, Indexing, Transactions, ACID)' },
  { value: 'Go', label: 'Go (Goroutines, Channels, Microservices)' },
  { value: 'Rust', label: 'Rust (Borrow Checker, Concurrency, Lifetimes)' }
];

const ASSESSMENT_LANGUAGES = [
  { value: 'English', label: 'English (Spoken in cloned Indian English accent)' },
  { value: 'Tamil', label: 'Tamil / தமிழ் (Spoken in cloned Tamil voice)' }
];

const TERMS_TEXT_EN = "I, the candidate, agree to the terms and conditions of Vani AI. I declare that I am undertaking this technical evaluation independently and will answer all questions in my own natural voice without any impersonation or unauthorized third-party assistance.";

const TERMS_TEXT_TA = "நான் வாணி ஏஐ நிறுவனத்தின் விதிமுறைகள் மற்றும் நிபந்தனைகளை முழுமையாக ஒப்புக்கொள்கிறேன். இந்தத் தேர்வை எவ்வித ஆள்மாறாட்டமும் இன்றி எனது சொந்தக் குரலில் நேர்மையாக சுயமாக முடிப்பேன் என்று உறுதி கூறுகிறேன்.";

const formatSeconds = (sec) => {
  const m = Math.floor((sec || 0) / 60);
  const s = (sec || 0) % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
};

export default function SetupPage({ user, onAssessmentStarted, systemStatus }) {
  const [selectedProgLang, setSelectedProgLang] = useState('');
  const [selectedAssessLang, setSelectedAssessLang] = useState('');
  const [validationError, setValidationError] = useState('');

  // Terms & Conditions Modal State
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [isRecordingTerms, setIsRecordingTerms] = useState(false);
  const [termsRecordingSeconds, setTermsRecordingSeconds] = useState(0);
  const [termsLiveTranscript, setTermsLiveTranscript] = useState('');
  const [termsAudioBlob, setTermsAudioBlob] = useState(null);
  const [termsAudioUrl, setTermsAudioUrl] = useState('');
  const [isPlayingTermsAudio, setIsPlayingTermsAudio] = useState(false);
  const [termsRecordingError, setTermsRecordingError] = useState('');

  // Generation & submission states
  const [isSubmittingTerms, setIsSubmittingTerms] = useState(false);
  const [submissionStep, setSubmissionStep] = useState('');

  // Audio refs
  const termsTimerRef = useRef(null);
  const termsStreamRef = useRef(null);
  const termsMediaRecorderRef = useRef(null);
  const termsSpeechRecognizerRef = useRef(null);
  const termsChunksRef = useRef([]);
  const termsAudioPlayerRef = useRef(null);

  // Clean up audio hardware on unmount
  useEffect(() => {
    return () => {
      if (termsTimerRef.current) clearInterval(termsTimerRef.current);
      if (termsSpeechRecognizerRef.current) {
        try { termsSpeechRecognizerRef.current.stop(); } catch (e) {}
      }
      if (termsMediaRecorderRef.current && termsMediaRecorderRef.current.state !== 'inactive') {
        try { termsMediaRecorderRef.current.stop(); } catch (e) {}
      }
      if (termsStreamRef.current) {
        termsStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      if (termsAudioUrl) {
        URL.revokeObjectURL(termsAudioUrl);
      }
    };
  }, [termsAudioUrl]);

  // Open modal after form validation
  const handleOpenTermsModal = () => {
    setValidationError('');
    if (!selectedProgLang) {
      setValidationError('Please select your preferred programming language from the dropdown.');
      return;
    }
    if (!selectedAssessLang) {
      setValidationError('Please select your assessment language (English or Tamil) from the dropdown.');
      return;
    }
    setShowTermsModal(true);
  };

  // Start recording candidate voice agreeing to terms & conditions
  const handleStartTermsRecording = async () => {
    setTermsRecordingError('');
    setTermsAudioBlob(null);
    if (termsAudioUrl) {
      URL.revokeObjectURL(termsAudioUrl);
      setTermsAudioUrl('');
    }
    setTermsLiveTranscript('');
    setTermsRecordingSeconds(0);
    termsChunksRef.current = [];

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Your browser does not support audio recording. Please use Google Chrome or Microsoft Edge.');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      termsStreamRef.current = stream;

      let mimeType = '';
      if (typeof MediaRecorder !== 'undefined') {
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        }
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      termsMediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          termsChunksRef.current.push(e.data);
        }
      };

      // Real-time speech recognition for Terms & Conditions declaration
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        try {
          const recognizer = new SpeechRecognition();
          recognizer.continuous = true;
          recognizer.interimResults = true;
          recognizer.lang = selectedAssessLang === 'Tamil' ? 'ta-IN' : 'en-US';

          recognizer.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            for (let i = 0; i < event.results.length; ++i) {
              if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript + ' ';
              } else {
                interimTranscript += event.results[i][0].transcript;
              }
            }
            setTermsLiveTranscript((finalTranscript + interimTranscript).trim());
          };

          recognizer.onerror = (e) => {
            console.warn('Terms speech recognizer warning:', e.error);
          };

          recognizer.start();
          termsSpeechRecognizerRef.current = recognizer;
        } catch (e) {
          console.warn('Speech recognition start failed:', e);
        }
      }

      recorder.onstop = () => {
        if (termsTimerRef.current) {
          clearInterval(termsTimerRef.current);
          termsTimerRef.current = null;
        }
        if (termsStreamRef.current) {
          termsStreamRef.current.getTracks().forEach((t) => t.stop());
          termsStreamRef.current = null;
        }

        const blobMime = mimeType ? mimeType.split(';')[0] : 'audio/webm';
        const blob = new Blob(termsChunksRef.current, { type: blobMime });
        setTermsAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setTermsAudioUrl(url);
      };

      recorder.start(250);
      setIsRecordingTerms(true);

      termsTimerRef.current = setInterval(() => {
        setTermsRecordingSeconds((s) => s + 1);
      }, 1000);

    } catch (err) {
      console.error('Microphone error in terms recording:', err);
      setTermsRecordingError(err.message || 'Microphone access denied. Please allow microphone permissions.');
      setIsRecordingTerms(false);
    }
  };

  // Stop terms recording
  const handleStopTermsRecording = () => {
    setIsRecordingTerms(false);
    if (termsTimerRef.current) {
      clearInterval(termsTimerRef.current);
      termsTimerRef.current = null;
    }
    if (termsSpeechRecognizerRef.current) {
      try { termsSpeechRecognizerRef.current.stop(); } catch (e) {}
    }
    if (termsMediaRecorderRef.current && termsMediaRecorderRef.current.state !== 'inactive') {
      try { termsMediaRecorderRef.current.stop(); } catch (e) {}
    }
  };

  // Re-record terms
  const handleResetTermsRecording = () => {
    handleStopTermsRecording();
    setTermsAudioBlob(null);
    if (termsAudioUrl) {
      URL.revokeObjectURL(termsAudioUrl);
      setTermsAudioUrl('');
    }
    setTermsLiveTranscript('');
    setTermsRecordingSeconds(0);
    setTermsRecordingError('');
  };

  // Play / Pause recorded terms audio
  const handleToggleTermsAudioPlayback = () => {
    if (!termsAudioPlayerRef.current) return;
    if (isPlayingTermsAudio) {
      termsAudioPlayerRef.current.pause();
      setIsPlayingTermsAudio(false);
    } else {
      termsAudioPlayerRef.current.currentTime = 0;
      termsAudioPlayerRef.current.play()
        .then(() => setIsPlayingTermsAudio(true))
        .catch((err) => console.warn('Audio playback error:', err));
    }
  };

  // Submit Terms & Conditions with recorded baseline voice and start assessment
  const handleAcceptTermsAndStart = async () => {
    if (!termsAudioBlob || termsAudioBlob.size < 500) {
      setTermsRecordingError('Please speak and record the Terms and Conditions declaration before starting.');
      return;
    }

    if (termsRecordingSeconds < 2) {
      setTermsRecordingError('Recording too short. Please speak the full declaration clearly (at least 3 seconds).');
      return;
    }

    setIsSubmittingTerms(true);
    setTermsRecordingError('');
    setSubmissionStep('Registering candidate baseline biometric voice embedding...');

    try {
      const formData = new FormData();
      formData.append('user_id', user?.id || 1);
      formData.append('user_email', user?.email || 'candidate@vani.ai');
      formData.append('programming_language', selectedProgLang);
      formData.append('assessment_language', selectedAssessLang);
      formData.append('terms_audio', termsAudioBlob, 'terms_declaration.webm');
      formData.append('terms_transcript', termsLiveTranscript || (selectedAssessLang === 'Tamil' ? TERMS_TEXT_TA : TERMS_TEXT_EN));

      setSubmissionStep('Synthesizing 5 technical scenario questions with OpenAI...');

      const res = await fetch('/api/assessment/start-with-terms', {
        method: 'POST',
        body: formData
      });

      setSubmissionStep('Generating question voice cloned in reference accent...');

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to initialize assessment session.');
      }

      setSubmissionStep('Baseline voice verified & locked. Entering assessment...');
      setTimeout(() => {
        setShowTermsModal(false);
        onAssessmentStarted(data);
      }, 700);

    } catch (err) {
      setTermsRecordingError(err.message || 'An error occurred while registering baseline voice.');
      setIsSubmittingTerms(false);
    }
  };

  // Selected language terms text
  const primaryTermsText = selectedAssessLang === 'Tamil' ? TERMS_TEXT_TA : TERMS_TEXT_EN;
  const secondaryTermsText = selectedAssessLang === 'Tamil' ? TERMS_TEXT_EN : TERMS_TEXT_TA;

  return (
    <div style={{ maxWidth: '880px', margin: '40px auto', padding: '0 24px' }}>
      {/* Main Setup Card */}
      <div className="glass-panel" style={{ padding: '40px' }}>
        <div style={{ marginBottom: '32px' }}>
          <div style={{ marginBottom: '8px' }}>
            <h2 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#fff' }}>
              Assessment Configuration
            </h2>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.92rem', lineHeight: '1.6' }}>
            Select your technical stack and spoken assessment language. You will then read and record the Terms & Conditions declaration to establish your biometric voice identity for this session.
          </p>
        </div>

        {/* Validation error notification */}
        {validationError && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.35)',
            color: '#fb7185',
            padding: '14px 18px',
            borderRadius: '12px',
            fontSize: '0.88rem',
            marginBottom: '26px'
          }}>
            <AlertTriangle size={20} style={{ flexShrink: 0 }} />
            <span>{validationError}</span>
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          {/* Programming language dropdown */}
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.92rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '10px' }}>
              <Code2 size={18} color="#818cf8" />
              <span>Select Programming Language</span>
              <span style={{ color: '#f43f5e' }}>*</span>
            </label>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '10px' }}>
              Questions will evaluate practical problem-solving, debugging, architecture, and coding concepts in this language.
            </p>
            <select
              value={selectedProgLang}
              onChange={(e) => setSelectedProgLang(e.target.value)}
              style={{
                width: '100%',
                padding: '14px 18px',
                background: '#0f172a',
                border: selectedProgLang ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '12px',
                color: selectedProgLang ? '#fff' : '#64748b',
                fontSize: '0.95rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="" disabled>-- Choose a programming language --</option>
              {PROGRAMMING_LANGUAGES.map((lang) => (
                <option key={lang.value} value={lang.value} style={{ background: '#0f172a', color: '#fff' }}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          {/* Assessment language dropdown */}
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.92rem', fontWeight: 700, color: '#f1f5f9', marginBottom: '10px' }}>
              <Globe2 size={18} color="#d946ef" />
              <span>Select Assessment & Question Spoken Language</span>
              <span style={{ color: '#f43f5e' }}>*</span>
            </label>
            <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '10px' }}>
              Questions will be displayed on screen and spoken aloud using your reference cloned voice in this language.
            </p>
            <select
              value={selectedAssessLang}
              onChange={(e) => setSelectedAssessLang(e.target.value)}
              style={{
                width: '100%',
                padding: '14px 18px',
                background: '#0f172a',
                border: selectedAssessLang ? '1px solid #d946ef' : '1px solid rgba(255, 255, 255, 0.15)',
                borderRadius: '12px',
                color: selectedAssessLang ? '#fff' : '#64748b',
                fontSize: '0.95rem',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="" disabled>-- Choose question & voice language --</option>
              {ASSESSMENT_LANGUAGES.map((lang) => (
                <option key={lang.value} value={lang.value} style={{ background: '#0f172a', color: '#fff' }}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          {/* Proceed to Terms & Conditions Button */}
          <div style={{ marginTop: '8px' }}>
            <button
              onClick={handleOpenTermsModal}
              disabled={!selectedProgLang || !selectedAssessLang}
              className="gradient-btn"
              style={{
                width: '100%',
                padding: '16px',
                borderRadius: '14px',
                fontSize: '1.05rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '10px',
                opacity: (!selectedProgLang || !selectedAssessLang) ? 0.6 : 1,
                cursor: (!selectedProgLang || !selectedAssessLang) ? 'not-allowed' : 'pointer'
              }}
            >
              <span>Review Terms & Record Voice Verification</span>
              <ArrowRight size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* ============================================================ */}
      {/* TERMS AND CONDITIONS VOICE VERIFICATION MODAL DIALOGUE       */}
      {/* ============================================================ */}
      {showTermsModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(3, 7, 18, 0.88)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '20px'
        }}>
          <div style={{
            background: '#0f172a',
            border: '1px solid rgba(99, 102, 241, 0.35)',
            borderRadius: '20px',
            maxWidth: '780px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '32px',
            boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(99, 102, 241, 0.15)',
            position: 'relative'
          }}>
            {/* Close button */}
            {!isSubmittingTerms && (
              <button
                onClick={() => {
                  handleResetTermsRecording();
                  setShowTermsModal(false);
                }}
                style={{
                  position: 'absolute',
                  top: '20px',
                  right: '20px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: 'none',
                  color: '#94a3b8',
                  borderRadius: '50%',
                  width: '36px',
                  height: '36px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
                title="Close"
              >
                <X size={18} />
              </button>
            )}

            {/* Modal Header */}
            <div style={{ marginBottom: '22px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
                <FileText size={22} color="#6366f1" />
                <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff' }}>
                  Terms & Conditions Voice Agreement
                </h3>
              </div>
              <p style={{ fontSize: '0.86rem', color: '#94a3b8', lineHeight: '1.5' }}>
                To prevent impersonation and guarantee academic integrity, please <strong>read aloud the declaration text below into your microphone</strong>. This establishes your authentic voice baseline.
              </p>
            </div>

            {/* Terms and Conditions Text Display Box */}
            <div style={{
              background: 'rgba(30, 41, 59, 0.7)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              borderRadius: '14px',
              padding: '20px',
              marginBottom: '22px'
            }}>
              <div style={{
                marginBottom: '10px'
              }}>
                <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Declaration Text to Read Aloud ({selectedAssessLang})
                </span>
              </div>

              {/* Primary Declaration Text in Selected Language */}
              <div style={{
                fontSize: '1.05rem',
                color: '#f8fafc',
                lineHeight: '1.7',
                fontWeight: 600,
                padding: '14px 18px',
                background: 'rgba(15, 23, 42, 0.7)',
                borderRadius: '10px',
                borderLeft: '4px solid #6366f1'
              }}>
                "{primaryTermsText}"
              </div>
            </div>

            {/* Error banner if microphone fails */}
            {termsRecordingError && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.35)',
                color: '#fb7185',
                padding: '12px 16px',
                borderRadius: '12px',
                fontSize: '0.85rem',
                marginBottom: '20px'
              }}>
                <ShieldAlert size={18} style={{ flexShrink: 0 }} />
                <span>{termsRecordingError}</span>
              </div>
            )}

            {/* Live speech transcription display while recording */}
            {isRecordingTerms && (
              <div style={{
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                borderRadius: '14px',
                padding: '16px 20px',
                marginBottom: '20px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: '#ef4444',
                      display: 'inline-block',
                      animation: 'pulse 1s infinite'
                    }} />
                    <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f43f5e' }}>
                      Transcribing your voice declaration live...
                    </span>
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: '#fca5a5', fontWeight: 700 }}>
                    {formatSeconds(termsRecordingSeconds)}
                  </span>
                </div>
                <div style={{
                  fontSize: '0.94rem',
                  color: '#f8fafc',
                  lineHeight: '1.6',
                  minHeight: '40px',
                  fontStyle: termsLiveTranscript ? 'normal' : 'italic'
                }}>
                  {termsLiveTranscript || 'Please read aloud the declaration above...'}
                </div>
              </div>
            )}

            {/* Voice Recording Controls */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
              background: 'rgba(15, 23, 42, 0.5)',
              borderRadius: '16px',
              border: '1px dashed rgba(255, 255, 255, 0.15)',
              marginBottom: '24px'
            }}>
              {!isRecordingTerms ? (
                <button
                  onClick={handleStartTermsRecording}
                  disabled={isSubmittingTerms}
                  style={{
                    width: '76px',
                    height: '76px',
                    borderRadius: '50%',
                    background: termsAudioBlob
                      ? 'linear-gradient(135deg, #10b981, #059669)'
                      : 'linear-gradient(135deg, #ef4444, #dc2626)',
                    border: 'none',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: isSubmittingTerms ? 'not-allowed' : 'pointer',
                    boxShadow: termsAudioBlob
                      ? '0 0 20px rgba(16, 185, 129, 0.4)'
                      : '0 0 25px rgba(239, 68, 68, 0.45)',
                    transition: 'all 0.25s ease'
                  }}
                  title={termsAudioBlob ? 'Click to re-record declaration' : 'Click to start speaking declaration'}
                >
                  <Mic size={32} />
                </button>
              ) : (
                <button
                  onClick={handleStopTermsRecording}
                  style={{
                    width: '76px',
                    height: '76px',
                    borderRadius: '50%',
                    background: '#ef4444',
                    border: 'none',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    boxShadow: '0 0 30px rgba(239, 68, 68, 0.6)',
                    animation: 'pulse 1.2s infinite'
                  }}
                  title="Click to Stop Recording"
                >
                  <Square size={28} />
                </button>
              )}

              <div style={{ textAlign: 'center', marginTop: '14px' }}>
                {isRecordingTerms ? (
                  <div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ef4444', fontFamily: 'var(--font-mono)' }}>
                      {formatSeconds(termsRecordingSeconds)}
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#f87171', fontWeight: 600, marginTop: '2px' }}>
                      Speaking Terms & Conditions • Click square to stop
                    </div>
                  </div>
                ) : termsAudioBlob ? (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', color: '#34d399', fontWeight: 700 }}>
                      <CheckCircle2 size={18} />
                      <span>Terms & Conditions Voice Recorded ({formatSeconds(termsRecordingSeconds)})</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '2px' }}>
                      Baseline voice sample captured. You can preview it below or click mic to re-record.
                    </div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#f1f5f9' }}>
                      Click Red Microphone to Speak the Declaration
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                      Read the box above aloud into your microphone clearly
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Audio Preview if recorded */}
            {termsAudioBlob && !isRecordingTerms && (
              <div style={{
                background: 'rgba(15, 23, 42, 0.75)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                borderRadius: '14px',
                padding: '16px 20px',
                marginBottom: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px'
              }}>
                <audio
                  ref={termsAudioPlayerRef}
                  src={termsAudioUrl}
                  onEnded={() => setIsPlayingTermsAudio(false)}
                />
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <button
                    onClick={handleToggleTermsAudioPlayback}
                    className="gradient-btn"
                    style={{
                      padding: '8px 16px',
                      fontSize: '0.82rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: isPlayingTermsAudio
                        ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                        : 'linear-gradient(135deg, #10b981, #059669)'
                    }}
                  >
                    {isPlayingTermsAudio ? <Pause size={14} /> : <Play size={14} />}
                    <span>{isPlayingTermsAudio ? 'Pause Voice' : 'Play My Recorded Voice'}</span>
                  </button>
                  <button
                    onClick={handleResetTermsRecording}
                    className="btn-secondary"
                    style={{ padding: '8px 14px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <RotateCcw size={13} />
                    <span>Re-record</span>
                  </button>
                </div>

                <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                  Status: <strong style={{ color: '#34d399' }}>Ready for Verification</strong>
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '14px' }}>
              <button
                onClick={() => {
                  handleResetTermsRecording();
                  setShowTermsModal(false);
                }}
                disabled={isSubmittingTerms}
                className="btn-secondary"
                style={{ padding: '12px 20px', fontSize: '0.9rem' }}
              >
                Cancel
              </button>

              <button
                onClick={handleAcceptTermsAndStart}
                disabled={isSubmittingTerms || !termsAudioBlob || isRecordingTerms}
                className="gradient-btn"
                style={{
                  padding: '14px 28px',
                  borderRadius: '12px',
                  fontSize: '0.98rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  opacity: (!termsAudioBlob || isSubmittingTerms || isRecordingTerms) ? 0.6 : 1,
                  cursor: (!termsAudioBlob || isSubmittingTerms || isRecordingTerms) ? 'not-allowed' : 'pointer'
                }}
              >
                {isSubmittingTerms ? (
                  <>
                    <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                    <span>{submissionStep}</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={18} />
                    <span>Accept Terms & Start Assessment</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
