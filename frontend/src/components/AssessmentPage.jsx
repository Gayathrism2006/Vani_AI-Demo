import React, { useState, useEffect, useRef } from 'react';
import {
  Volume2, Play, Pause, RotateCcw, Mic, Square, ArrowLeft, ArrowRight,
  CheckCircle2, Clock, Sparkles, AlertCircle, ShieldAlert, Check, RefreshCw, Send,
  Cpu, Activity, Radio, Waves, Loader2, ShieldCheck, AlertTriangle
} from 'lucide-react';

// Format recording duration mm:ss
const formatTime = (seconds) => {
  const mins = Math.floor((seconds || 0) / 60);
  const secs = (seconds || 0) % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export default function AssessmentPage({ assessment, onSubmitted }) {
  const assessmentId = assessment?.id || assessment?.assessment_id;
  const [currentIndex, setCurrentIndex] = useState(0); // 0 to 4
  const [questions, setQuestions] = useState(assessment.questions || []);
  const [answers, setAnswers] = useState(assessment.answers || {});

  // Question audio player state
  const [isQuestionAudioLoading, setIsQuestionAudioLoading] = useState(false);
  const [isPlayingQuestionAudio, setIsPlayingQuestionAudio] = useState(false);
  const [pendingPlay, setPendingPlay] = useState(false);
  const [autoPlayQuestions, setAutoPlayQuestions] = useState(true);
  const questionAudioRef = useRef(null);

  // Candidate recording & real-time live transcript state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [isProcessingAnswer, setIsProcessingAnswer] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [recordingError, setRecordingError] = useState('');

  // Refs for audio streams, recorder, timer, and recognizer
  const timerRef = useRef(null);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const speechRecognizerRef = useRef(null);
  const chunksRef = useRef([]);
  const currentIndexRef = useRef(currentIndex);

  useEffect(() => {
    currentIndexRef.current = currentIndex;
  }, [currentIndex]);

  // Candidate answer playback
  const [isPlayingCandidateAudio, setIsPlayingCandidateAudio] = useState(false);
  const candidateAudioRef = useRef(null);

  // Submission modal state
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');

  const currentQuestion = questions[currentIndex] || {};
  const currentAnswer = answers[String(currentIndex + 1)] || {};

  // Clean up all hardware & timers on component unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      if (speechRecognizerRef.current) {
        try { speechRecognizerRef.current.stop(); } catch (e) {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop(); } catch (e) {}
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Fetch or load question audio whenever current question changes
  useEffect(() => {
    // Stop any active candidate recording if question changed
    if (isRecording) {
      handleStopRecording();
    }

    // Stop active audio playback
    if (questionAudioRef.current) {
      questionAudioRef.current.pause();
      setIsPlayingQuestionAudio(false);
    }
    if (candidateAudioRef.current) {
      candidateAudioRef.current.pause();
      setIsPlayingCandidateAudio(false);
    }

    // Reset live transcript and error when changing questions
    setLiveTranscript('');
    setRecordingError('');

    // Ensure pending play is armed if auto-play is enabled so question voice starts automatically
    if (autoPlayQuestions) {
      setPendingPlay(true);
    }

    // If current question already has an audio_url, skip fetching
    if (questions[currentIndex]?.audio_url) {
      setIsQuestionAudioLoading(false);
      return;
    }

    const loadQuestionAudio = async () => {
      if (!assessmentId) return;
      const qNum = currentIndex + 1;
      setIsQuestionAudioLoading(true);
      try {
        const res = await fetch(`/api/assessment/${assessmentId}/question/${qNum}/audio`);
        const data = await res.json();
        if (res.ok && data.audio_url) {
          setQuestions((prev) => {
            const next = [...prev];
            next[currentIndex] = { ...next[currentIndex], audio_url: data.audio_url, is_cloned: data.is_cloned };
            return next;
          });
        }
      } catch (err) {
        console.error('Failed to load question audio:', err);
      } finally {
        setIsQuestionAudioLoading(false);
      }
    };

    loadQuestionAudio();
  }, [currentIndex, assessmentId]);

  // Automatically play question voice when audio becomes available or pendingPlay is active
  useEffect(() => {
    if (currentQuestion?.audio_url && (pendingPlay || autoPlayQuestions)) {
      setPendingPlay(false);
      const timer = setTimeout(() => {
        if (questionAudioRef.current) {
          questionAudioRef.current.currentTime = 0;
          questionAudioRef.current.play()
            .then(() => setIsPlayingQuestionAudio(true))
            .catch((e) => {
              console.log('Autoplay deferred until user click:', e);
              setIsPlayingQuestionAudio(false);
            });
        }
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [currentQuestion?.audio_url, currentIndex]);

  // Toggle question audio playback
  const togglePlayQuestionAudio = () => {
    if (isQuestionAudioLoading) {
      setPendingPlay((prev) => !prev);
      return;
    }
    if (!questionAudioRef.current) return;
    if (isPlayingQuestionAudio) {
      questionAudioRef.current.pause();
      setIsPlayingQuestionAudio(false);
    } else {
      questionAudioRef.current.play()
        .then(() => setIsPlayingQuestionAudio(true))
        .catch((err) => {
          console.warn('Playback error:', err);
          setIsPlayingQuestionAudio(false);
        });
    }
  };

  // Replay question audio
  const replayQuestionAudio = () => {
    if (isQuestionAudioLoading) {
      setPendingPlay(true);
      return;
    }
    if (!questionAudioRef.current) return;
    questionAudioRef.current.currentTime = 0;
    questionAudioRef.current.play()
      .then(() => setIsPlayingQuestionAudio(true))
      .catch((err) => {
        console.warn('Replay error:', err);
        setIsPlayingQuestionAudio(false);
      });
  };

  // Start candidate recording with real-time live transcription
  const handleStartRecording = async () => {
    setRecordingError('');
    setRecordingSeconds(0);
    setLiveTranscript('');
    chunksRef.current = [];

    // Stop any question audio if it's currently speaking
    if (questionAudioRef.current && isPlayingQuestionAudio) {
      questionAudioRef.current.pause();
      setIsPlayingQuestionAudio(false);
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Your browser does not support audio recording. Please use Google Chrome or Microsoft Edge.');
      }

      // 1. Start browser microphone recording with noise suppression
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      streamRef.current = stream;

      // Select supported MIME type
      let mimeType = '';
      if (typeof MediaRecorder !== 'undefined') {
        if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          mimeType = 'audio/webm;codecs=opus';
        } else if (MediaRecorder.isTypeSupported('audio/webm')) {
          mimeType = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
          mimeType = 'audio/mp4';
        } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
          mimeType = 'audio/ogg';
        }
      }

      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      // 2. Start Web Speech API for real-time live transcription display while speaking
      let liveTextBuffer = '';
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const recognizer = new SpeechRecognition();
          recognizer.continuous = true;
          recognizer.interimResults = true;
          recognizer.lang = assessment.assessment_language === 'Tamil' ? 'ta-IN' : 'en-US';

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
            const currentText = (finalTranscript + interimTranscript).trim();
            liveTextBuffer = currentText;
            setLiveTranscript(currentText);
          };

          recognizer.onerror = (e) => {
            console.warn('Speech recognition notice:', e.error);
          };

          recognizer.onend = () => {
            // Keep speech recognizer alive if recording is still active
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
              try { recognizer.start(); } catch (e) {}
            }
          };

          recognizer.start();
          speechRecognizerRef.current = recognizer;
        } catch (e) {
          console.warn('Could not start live speech recognizer:', e);
        }
      }

      recorder.onstop = async () => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }

        // Stop all audio tracks to turn off browser microphone indicator
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        const blobMime = mimeType ? mimeType.split(';')[0] : 'audio/webm';
        const audioBlob = new Blob(chunksRef.current, { type: blobMime });

        // Process audio via ElevenLabs Audio Isolation + Speech-to-Text
        await uploadAndProcessAnswer(audioBlob, liveTextBuffer, currentIndexRef.current);
      };

      recorder.start(250);
      setIsRecording(true);

      // Start elapsed recording seconds timer
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);

    } catch (err) {
      console.error('Microphone error:', err);
      setRecordingError(err.message || 'Microphone permission denied or device unavailable. Please allow microphone access in your browser.');
      setIsRecording(false);
    }
  };

  // Stop candidate recording
  const handleStopRecording = () => {
    setIsRecording(false);

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    if (speechRecognizerRef.current) {
      try {
        speechRecognizerRef.current.stop();
        speechRecognizerRef.current = null;
      } catch (e) {}
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {
        console.warn('Error stopping mediaRecorder:', e);
      }
    }
  };

  // Upload and process recording with ElevenLabs
  const uploadAndProcessAnswer = async (audioBlob, capturedLiveText, targetIndex) => {
    if (!audioBlob || audioBlob.size < 200) {
      setRecordingError('Recording was empty or too short. Please speak clearly into your microphone and record again.');
      return;
    }

    setIsProcessingAnswer(true);
    setProcessingStatus('Removing background noise with ElevenLabs Audio Isolation...');

    const questionNumber = (targetIndex ?? currentIndex) + 1;
    const formData = new FormData();
    formData.append('audio', audioBlob, `q${questionNumber}_answer.webm`);
    if (capturedLiveText && capturedLiveText.trim()) {
      formData.append('live_transcript', capturedLiveText.trim());
    }

    try {
      setTimeout(() => {
        setProcessingStatus('Transcribing speech & applying context correction with ElevenLabs...');
      }, 1000);

      setTimeout(() => {
        setProcessingStatus('Verifying speaker voice against Terms & Conditions baseline...');
      }, 2200);

      const res = await fetch(`/api/assessment/${assessmentId}/question/${questionNumber}/answer`, {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to process answer with ElevenLabs.');
      }

      // Update answer state
      setAnswers((prev) => ({
        ...prev,
        [String(questionNumber)]: data.answer
      }));

    } catch (err) {
      console.error('Upload error:', err);
      setRecordingError(err.message || 'Error processing your recording with ElevenLabs.');
    } finally {
      setIsProcessingAnswer(false);
      setProcessingStatus('');
    }
  };

  // Check how many questions are answered
  const answeredCount = Object.values(answers).filter((a) => a.recorded).length;
  const isAllAnswered = answeredCount === 5;

  // Handle final submission
  const handleFinalSubmit = async () => {
    setSubmitError('');
    setIsSubmitting(true);

    try {
      const res = await fetch(`/api/assessment/${assessmentId}/submit`, {
        method: 'POST'
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Submission failed.');
      }

      setShowSubmitModal(false);
      onSubmitted(assessmentId);
    } catch (err) {
      setSubmitError(err.message || 'Failed to submit assessment.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '960px', margin: '24px auto 80px', padding: '0 24px' }}>
      {/* Top assessment status header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            fontSize: '0.85rem',
            fontWeight: 700,
            background: 'rgba(99, 102, 241, 0.15)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: '#a5b4fc',
            padding: '4px 12px',
            borderRadius: '20px'
          }}>
            {assessment.programming_language}
          </span>
          <span style={{
            fontSize: '0.85rem',
            fontWeight: 700,
            background: 'rgba(217, 70, 239, 0.15)',
            border: '1px solid rgba(217, 70, 239, 0.3)',
            color: '#f0abfc',
            padding: '4px 12px',
            borderRadius: '20px'
          }}>
            {assessment.assessment_language}
          </span>
        </div>

        {/* Progress pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: '6px 14px',
          borderRadius: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <Clock size={15} color="#94a3b8" />
          <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#e2e8f0' }}>
            Question {currentIndex + 1} of 5
          </span>
          <span style={{ fontSize: '0.78rem', color: '#34d399', fontWeight: 600 }}>
            ({answeredCount}/5 Answered)
          </span>
        </div>
      </div>

      {/* Progress line */}
      <div style={{
        width: '100%',
        height: '6px',
        background: 'rgba(255, 255, 255, 0.08)',
        borderRadius: '3px',
        marginBottom: '28px',
        overflow: 'hidden'
      }}>
        <div style={{
          height: '100%',
          width: `${((currentIndex + 1) / 5) * 100}%`,
          background: 'var(--primary-gradient)',
          borderRadius: '3px',
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* Question quick jump tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        flexWrap: 'wrap'
      }}>
        {questions.map((q, idx) => {
          const isAnswered = answers[String(idx + 1)]?.recorded;
          const isCurrent = idx === currentIndex;
          const hasAudio = !!q.audio_url;
          return (
            <button
              key={idx}
              onClick={() => setCurrentIndex(idx)}
              style={{
                flex: '1',
                minWidth: '100px',
                padding: '10px 14px',
                borderRadius: '12px',
                background: isCurrent
                  ? 'rgba(99, 102, 241, 0.25)'
                  : isAnswered
                  ? 'rgba(16, 185, 129, 0.12)'
                  : 'rgba(255, 255, 255, 0.04)',
                border: isCurrent
                  ? '1px solid #6366f1'
                  : isAnswered
                  ? '1px solid rgba(16, 185, 129, 0.3)'
                  : '1px solid rgba(255, 255, 255, 0.08)',
                color: isCurrent ? '#fff' : isAnswered ? '#34d399' : '#94a3b8',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.2s ease'
              }}
            >
              {isAnswered ? <Check size={14} /> : null}
              <span>Q{idx + 1}</span>
              {hasAudio && (
                <Volume2
                  size={12}
                  style={{
                    color: isCurrent ? '#a5b4fc' : '#64748b',
                    opacity: 0.85
                  }}
                  title="Spoken question audio ready"
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Question Card */}
      <div className="glass-panel" style={{ padding: '32px', marginBottom: '28px' }}>
        {/* Question metadata badge */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              background: '#6366f1',
              color: '#fff',
              padding: '3px 10px',
              borderRadius: '6px'
            }}>
              Question {currentIndex + 1}
            </span>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              color: '#f59e0b',
              background: 'rgba(245, 158, 11, 0.12)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              padding: '3px 10px',
              borderRadius: '6px'
            }}>
              {currentQuestion.difficulty || 'Technical Scenario'}
            </span>
            {currentQuestion.concept && (
              <span style={{
                fontSize: '0.75rem',
                color: '#94a3b8',
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '3px 10px',
                borderRadius: '6px'
              }}>
                {currentQuestion.concept}
              </span>
            )}
          </div>
        </div>

        {/* Question Title & Text */}
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '14px' }}>
          {currentQuestion.title || `Technical Problem Scenario ${currentIndex + 1}`}
        </h3>
        <p style={{
          fontSize: '1.02rem',
          lineHeight: '1.7',
          color: '#cbd5e1',
          marginBottom: '28px',
          whiteSpace: 'pre-line'
        }}>
          {currentQuestion.question}
        </p>

        {/* Question Audio Player Bar */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: '14px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <button
              onClick={togglePlayQuestionAudio}
              className="gradient-btn"
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 0,
                position: 'relative',
                boxShadow: isPlayingQuestionAudio
                  ? '0 0 20px rgba(99, 102, 241, 0.6)'
                  : pendingPlay
                  ? '0 0 16px rgba(234, 179, 8, 0.5)'
                  : 'none',
                transition: 'all 0.25s ease'
              }}
              title={
                isQuestionAudioLoading
                  ? pendingPlay
                    ? 'Voice is generating — Will play automatically once ready'
                    : 'Click to queue playback as soon as voice finishes'
                  : isPlayingQuestionAudio
                  ? 'Pause Spoken Question'
                  : 'Play Spoken Question'
              }
            >
              {isQuestionAudioLoading ? (
                <Loader2 size={20} className="animate-spin" color="#fff" />
              ) : isPlayingQuestionAudio ? (
                <Pause size={20} />
              ) : (
                <Play size={20} style={{ marginLeft: '2px' }} />
              )}
            </button>

            <button
              onClick={replayQuestionAudio}
              disabled={isQuestionAudioLoading && !pendingPlay}
              className="btn-secondary"
              style={{ padding: '8px 14px', fontSize: '0.82rem' }}
              title="Replay from start"
            >
              <RotateCcw size={15} />
              <span>Replay</span>
            </button>

            <div>
              {isQuestionAudioLoading ? (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f1f5f9' }}>
                      {pendingPlay ? '🎙️ Question Audio Preparing...' : '🎙️ Preparing Audio...'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    {pendingPlay
                      ? 'Audio is preparing. Playback will begin automatically...'
                      : 'Audio is preparing. Click play to listen.'}
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f1f5f9' }}>
                      {isPlayingQuestionAudio ? 'Playing Spoken Question' : 'Listen to Question'}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    Click play to listen to this scenario question
                  </div>
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {isPlayingQuestionAudio && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span className="soundwave-bar" style={{ animationDelay: '0s' }} />
                <span className="soundwave-bar" style={{ animationDelay: '0.2s' }} />
                <span className="soundwave-bar" style={{ animationDelay: '0.4s' }} />
                <span className="soundwave-bar" style={{ animationDelay: '0.1s' }} />
                <span className="soundwave-bar" style={{ animationDelay: '0.3s' }} />
              </div>
            )}

            {/* Auto-play toggle */}
            <label style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              color: '#94a3b8',
              cursor: 'pointer',
              userSelect: 'none',
              background: 'rgba(255, 255, 255, 0.04)',
              padding: '4px 10px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.06)'
            }} title="Automatically read aloud when you navigate to a question">
              <input
                type="checkbox"
                checked={autoPlayQuestions}
                onChange={(e) => setAutoPlayQuestions(e.target.checked)}
                style={{ accentColor: '#6366f1', cursor: 'pointer' }}
              />
              <span>Auto-read</span>
            </label>
          </div>

          {/* Guaranteed permanent audio element */}
          <audio
            ref={questionAudioRef}
            key={currentQuestion.audio_url || `audio_${currentIndex}`}
            src={currentQuestion.audio_url || ''}
            preload="auto"
            onPlay={() => setIsPlayingQuestionAudio(true)}
            onPause={() => setIsPlayingQuestionAudio(false)}
            onEnded={() => setIsPlayingQuestionAudio(false)}
            onError={(e) => {
              console.warn('Audio tag event notice:', e);
              setIsPlayingQuestionAudio(false);
            }}
          />
        </div>
      </div>

      {/* Candidate Voice Answer Section */}
      <div className="glass-panel" style={{ padding: '32px', marginBottom: '32px' }}>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <h4 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#fff' }}>
              Your Spoken Answer
            </h4>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '4px' }}>
            Speak into your microphone. Your live transcript appears on screen in real time as you speak.
          </p>
        </div>

        {/* Recording error notification */}
        {recordingError && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            padding: '12px 16px',
            borderRadius: '12px',
            fontSize: '0.85rem',
            marginBottom: '20px'
          }}>
            <ShieldAlert size={18} style={{ flexShrink: 0 }} />
            <span>{recordingError}</span>
          </div>
        )}

        {/* Real-time live transcript display while speaking */}
        {isRecording && (
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            borderRadius: '14px',
            padding: '20px',
            marginBottom: '20px',
            boxShadow: '0 0 20px rgba(99, 102, 241, 0.15)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '10px'
            }}>
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
                  Live Transcript (Transcribing in real time as you speak...):
                </span>
              </div>
              <div style={{ fontSize: '0.82rem', color: '#a5b4fc', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                {formatTime(recordingSeconds)}
              </div>
            </div>

            <div style={{
              fontSize: '1rem',
              color: '#f8fafc',
              lineHeight: '1.6',
              minHeight: '48px',
              fontStyle: liveTranscript ? 'normal' : 'italic'
            }}>
              {liveTranscript ? liveTranscript : 'Listening to your speech... Speak now.'}
            </div>
          </div>
        )}

        {/* Recording controls */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '28px',
          background: 'rgba(15, 23, 42, 0.45)',
          borderRadius: '16px',
          border: '1px dashed rgba(255, 255, 255, 0.15)',
          marginBottom: '24px'
        }}>
          {!isRecording ? (
            <button
              onClick={handleStartRecording}
              disabled={isProcessingAnswer}
              style={{
                width: '84px',
                height: '84px',
                borderRadius: '50%',
                background: currentAnswer.recorded ? '#334155' : 'linear-gradient(135deg, #ef4444, #dc2626)',
                border: 'none',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: isProcessingAnswer ? 'not-allowed' : 'pointer',
                boxShadow: currentAnswer.recorded ? 'none' : '0 0 25px rgba(239, 68, 68, 0.5)',
                transition: 'all 0.25s ease'
              }}
              title={currentAnswer.recorded ? 'Click to re-record answer' : 'Click to record your answer'}
            >
              <Mic size={36} />
            </button>
          ) : (
            <button
              onClick={handleStopRecording}
              className="recording-pulse"
              style={{
                width: '84px',
                height: '84px',
                borderRadius: '50%',
                background: '#ef4444',
                border: 'none',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer'
              }}
              title="Click to Stop Recording"
            >
              <Square size={32} />
            </button>
          )}

          {/* Status text & timer */}
          <div style={{ textAlign: 'center', marginTop: '16px' }}>
            {isRecording ? (
              <div>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#ef4444', fontFamily: 'var(--font-mono)' }}>
                  {formatTime(recordingSeconds)}
                </div>
                <div style={{ fontSize: '0.85rem', color: '#f87171', fontWeight: 600, marginTop: '4px' }}>
                  Recording active • Click red square button when finished
                </div>
              </div>
            ) : isProcessingAnswer ? (
              <div>
                <div style={{ fontSize: '0.92rem', color: '#a5b4fc', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                  <Activity size={18} className="soundwave-bar" style={{ animation: 'spin 1.5s linear infinite' }} />
                  <span>{processingStatus}</span>
                </div>
                <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '4px' }}>
                  Running ElevenLabs Audio Isolation & Speech-to-Text...
                </div>
              </div>
            ) : currentAnswer.recorded ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', color: '#34d399', fontWeight: 700 }}>
                  <CheckCircle2 size={18} />
                  <span>Answer Recorded & Processed</span>
                </div>
                <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '4px' }}>
                  Click microphone again if you wish to re-record your answer.
                </div>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f1f5f9' }}>
                  Click Microphone to Record Answer
                </div>
                <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '2px' }}>
                  Transcript will appear in real time as you speak
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Display recorded answer review, ElevenLabs transcript & noise-free audio playback */}
        {currentAnswer.recorded && !isRecording && (
          <div style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            borderRadius: '16px',
            padding: '24px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.25)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '16px',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle2 size={16} />
                  <span>{currentAnswer.transcript ? 'Recognized Transcript' : 'Transcript Unavailable'}</span>
                </span>
              </div>

              {currentAnswer.audio_url && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <audio
                    ref={candidateAudioRef}
                    key={currentAnswer.audio_url}
                    src={currentAnswer.audio_url}
                    preload="auto"
                    onPlay={() => setIsPlayingCandidateAudio(true)}
                    onPause={() => setIsPlayingCandidateAudio(false)}
                    onEnded={() => setIsPlayingCandidateAudio(false)}
                  />
                  <button
                    onClick={() => {
                      if (!candidateAudioRef.current) return;
                      if (isPlayingCandidateAudio) {
                        candidateAudioRef.current.pause();
                        setIsPlayingCandidateAudio(false);
                      } else {
                        candidateAudioRef.current.currentTime = 0;
                        candidateAudioRef.current.play()
                          .then(() => setIsPlayingCandidateAudio(true))
                          .catch((err) => console.warn('Candidate playback error:', err));
                      }
                    }}
                    className="gradient-btn"
                    style={{
                      padding: '8px 16px',
                      fontSize: '0.82rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      background: isPlayingCandidateAudio
                        ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                        : 'linear-gradient(135deg, #6366f1, #8b5cf6)'
                    }}
                    title="Listen to your noise-free isolated answer audio"
                  >
                    {isPlayingCandidateAudio ? <Pause size={14} /> : <Play size={14} />}
                    <span>{isPlayingCandidateAudio ? 'Pause Audio' : 'Play My Answer'}</span>
                  </button>
                </div>
              )}
            </div>

            {/* Transcript text */}
            <div style={{
              fontSize: '0.98rem',
              color: '#f8fafc',
              lineHeight: '1.7',
              background: 'rgba(0, 0, 0, 0.35)',
              padding: '16px 20px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              whiteSpace: 'pre-wrap'
            }}>
              {currentAnswer.transcript || 'Your recording was saved, but speech could not be transcribed. Please try recording again.'}
            </div>

            {/* Voice Verification Proctoring Banner */}
            {currentAnswer.voice_match_status && currentAnswer.voice_match_status !== 'unverified' && (
              <div style={{
                marginTop: '16px',
                padding: '14px 18px',
                borderRadius: '12px',
                background: currentAnswer.voice_matched
                  ? 'rgba(16, 185, 129, 0.12)'
                  : 'rgba(239, 68, 68, 0.16)',
                border: currentAnswer.voice_matched
                  ? '1px solid rgba(16, 185, 129, 0.35)'
                  : '1px solid rgba(239, 68, 68, 0.5)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '12px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {currentAnswer.voice_matched ? (
                    <ShieldCheck size={24} color="#34d399" style={{ flexShrink: 0 }} />
                  ) : (
                    <AlertTriangle size={24} color="#ef4444" style={{ flexShrink: 0 }} />
                  )}
                  <div>
                    <div style={{
                      fontSize: '0.94rem',
                      fontWeight: 800,
                      color: currentAnswer.voice_matched ? '#34d399' : '#f87171',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <span>{currentAnswer.voice_matched ? 'Voice Verified' : 'Voice Not Matched'}</span>
                      <span style={{
                        fontSize: '0.72rem',
                        padding: '2px 8px',
                        borderRadius: '10px',
                        background: currentAnswer.voice_matched ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)',
                        color: currentAnswer.voice_matched ? '#a7f3d0' : '#fca5a5'
                      }}>
                        {currentAnswer.voice_similarity_score}% match
                      </span>
                    </div>
                    <div style={{
                      fontSize: '0.8rem',
                      color: currentAnswer.voice_matched ? '#a7f3d0' : '#fecaca',
                      marginTop: '3px'
                    }}>
                      {currentAnswer.voice_matched
                        ? 'Candidate voice matches the Terms & Conditions baseline voice.'
                        : 'Candidate voice does not match the Terms & Conditions baseline voice. Possible impersonation or different speaker detected.'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Re-record instruction */}
            <div style={{
              marginTop: '12px',
              fontSize: '0.78rem',
              color: '#94a3b8',
              textAlign: 'right'
            }}>
              <span>Click microphone above if you wish to re-record your answer.</span>
            </div>
          </div>
        )}
      </div>

      {/* Navigation & Submit Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <button
          onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
          disabled={currentIndex === 0}
          className="btn-secondary"
          style={{ padding: '12px 24px' }}
        >
          <ArrowLeft size={18} />
          <span>Previous Question</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {currentIndex < 4 ? (
            <button
              onClick={() => setCurrentIndex((prev) => Math.min(4, prev + 1))}
              className="gradient-btn"
              style={{
                padding: '12px 24px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <span>Next Question</span>
              <ArrowRight size={18} />
            </button>
          ) : (
            <button
              onClick={() => setShowSubmitModal(true)}
              disabled={!isAllAnswered}
              className="gradient-btn"
              style={{
                padding: '14px 28px',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: isAllAnswered
                  ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                  : 'rgba(255, 255, 255, 0.1)'
              }}
            >
              <Send size={18} />
              <span>Submit Assessment</span>
            </button>
          )}
        </div>
      </div>

      {/* Confirmation Modal before Submit */}
      {showSubmitModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '20px'
        }}>
          <div className="glass-panel" style={{
            maxWidth: '520px',
            width: '100%',
            padding: '36px',
            background: '#0f172a'
          }}>
            <h3 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff', marginBottom: '10px' }}>
              Confirm Assessment Submission
            </h3>
            <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '20px', lineHeight: '1.6' }}>
              You have answered all 5 scenario questions. Once submitted, your assessment will be finalized and marked for evaluation.
            </p>

            {submitError && (
              <div style={{
                background: 'rgba(244, 63, 94, 0.15)',
                border: '1px solid rgba(244, 63, 94, 0.3)',
                color: '#fb7185',
                padding: '10px 14px',
                borderRadius: '8px',
                fontSize: '0.85rem',
                marginBottom: '16px'
              }}>
                {submitError}
              </div>
            )}

            <div style={{ display: 'flex', gap: '14px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowSubmitModal(false)}
                disabled={isSubmitting}
                className="btn-secondary"
              >
                Cancel & Review
              </button>
              <button
                onClick={handleFinalSubmit}
                disabled={isSubmitting}
                className="gradient-btn"
                style={{
                  padding: '12px 24px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #10b981, #059669)'
                }}
              >
                {isSubmitting ? 'Submitting...' : 'Yes, Submit Assessment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
