import React, { useState, useEffect } from 'react';
import {
  FileText, Play, Pause, ArrowLeft, CheckCircle2, ShieldCheck, Download,
  Volume2, ExternalLink, Calendar, Code, Globe, AlertTriangle, ShieldAlert
} from 'lucide-react';

export default function ReviewPage({ assessmentId, onBackToSetup }) {
  const [reviewData, setReviewData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeAudioUrl, setActiveAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = React.useRef(null);

  useEffect(() => {
    const fetchReview = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/assessment/${assessmentId}/review`);
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || 'Failed to load assessment review.');
        }
        setReviewData(data);
      } catch (err) {
        setError(err.message || 'Failed to fetch review data.');
      } finally {
        setLoading(false);
      }
    };

    fetchReview();
  }, [assessmentId]);

  const togglePlayAudio = (url) => {
    if (!audioRef.current) return;
    if (activeAudioUrl === url && isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      setActiveAudioUrl(url);
      audioRef.current.src = url;
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 24px', color: '#94a3b8' }}>
        <p>Loading assessment review...</p>
      </div>
    );
  }

  if (error || !reviewData) {
    return (
      <div style={{ maxWidth: '640px', margin: '60px auto', padding: '0 24px', textAlign: 'center' }}>
        <div className="glass-panel" style={{ padding: '40px' }}>
          <p style={{ color: '#f43f5e', marginBottom: '16px' }}>{error || 'Review data not found.'}</p>
          <button onClick={onBackToSetup} className="btn-secondary">
            <ArrowLeft size={16} />
            <span>Back to Dashboard</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '960px', margin: '30px auto 80px', padding: '0 24px' }}>
      {/* Hidden global audio element */}
      <audio
        ref={audioRef}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Header bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '28px',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff' }}>
              Assessment Review
            </h2>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              background: reviewData.status === 'submitted' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
              color: reviewData.status === 'submitted' ? '#34d399' : '#fbbf24',
              border: reviewData.status === 'submitted' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(245, 158, 11, 0.4)',
              padding: '3px 10px',
              borderRadius: '20px'
            }}>
              {reviewData.status === 'submitted' ? 'Finalized & Submitted' : 'In Progress'}
            </span>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Candidate: <strong style={{ color: '#e2e8f0' }}>{reviewData.user_email}</strong> • Programming: <strong style={{ color: '#a5b4fc' }}>{reviewData.programming_language}</strong> • Language: <strong style={{ color: '#f0abfc' }}>{reviewData.assessment_language}</strong>
          </p>
        </div>

        <button onClick={onBackToSetup} className="btn-secondary">
          <ArrowLeft size={16} />
          <span>New Assessment</span>
        </button>
      </div>

      {/* Terms & Conditions Baseline Voice Card */}
      {reviewData.baseline_audio_url && (
        <div className="glass-panel" style={{
          padding: '24px 28px',
          marginBottom: '28px',
          border: '1px solid rgba(99, 102, 241, 0.35)',
          background: 'rgba(15, 23, 42, 0.6)'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '12px',
            flexWrap: 'wrap',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShieldCheck size={22} color="#818cf8" />
              <div>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                  Terms & Conditions Voice Identity Baseline
                </h4>
                <p style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                  Recorded prior to assessment start to establish anti-impersonation voice identity.
                </p>
              </div>
            </div>

            <button
              onClick={() => togglePlayAudio(reviewData.baseline_audio_url)}
              className="gradient-btn"
              style={{
                padding: '8px 16px',
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                background: activeAudioUrl === reviewData.baseline_audio_url && isPlaying
                  ? 'linear-gradient(135deg, #ef4444, #dc2626)'
                  : 'linear-gradient(135deg, #6366f1, #8b5cf6)'
              }}
            >
              {activeAudioUrl === reviewData.baseline_audio_url && isPlaying ? <Pause size={14} /> : <Play size={14} />}
              <span>{activeAudioUrl === reviewData.baseline_audio_url && isPlaying ? 'Pause Declaration' : 'Play Terms Declaration Voice'}</span>
            </button>
          </div>

          {reviewData.baseline_transcript && (
            <div style={{
              background: 'rgba(0, 0, 0, 0.35)',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '0.86rem',
              color: '#cbd5e1',
              fontStyle: 'italic',
              borderLeft: '3px solid #6366f1'
            }}>
              "{reviewData.baseline_transcript}"
            </div>
          )}
        </div>
      )}

      {/* All 5 Questions list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {reviewData.review_items?.map((item) => (
          <div key={item.question_number} className="glass-panel" style={{ padding: '28px' }}>
            {/* Header of question */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '14px',
              flexWrap: 'wrap',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  background: '#6366f1',
                  color: '#fff',
                  padding: '3px 8px',
                  borderRadius: '6px'
                }}>
                  Question {item.question_number} of 5
                </span>
                <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: 600 }}>
                  {item.difficulty}
                </span>
                {item.concept && (
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    • {item.concept}
                  </span>
                )}

                {/* Voice Verification Badge */}
                {item.voice_match_status && (
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '3px 10px',
                    borderRadius: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    background: item.voice_matched ? 'rgba(16, 185, 129, 0.18)' : 'rgba(239, 68, 68, 0.2)',
                    color: item.voice_matched ? '#34d399' : '#f87171',
                    border: item.voice_matched ? '1px solid rgba(16, 185, 129, 0.35)' : '1px solid rgba(239, 68, 68, 0.45)'
                  }}>
                    {item.voice_matched ? <ShieldCheck size={13} /> : <AlertTriangle size={13} />}
                    <span>{item.voice_matched ? 'Voice Verified' : 'Voice Not Matched'} ({item.voice_similarity_score}%)</span>
                  </span>
                )}
              </div>

              {item.recorded && item.audio_url && (
                <button
                  onClick={() => togglePlayAudio(item.audio_url)}
                  className="btn-secondary"
                  style={{
                    padding: '6px 12px',
                    fontSize: '0.8rem',
                    borderColor: activeAudioUrl === item.audio_url && isPlaying ? '#10b981' : undefined
                  }}
                >
                  {activeAudioUrl === item.audio_url && isPlaying ? <Pause size={14} color="#10b981" /> : <Play size={14} color="#a5b4fc" />}
                  <span>{activeAudioUrl === item.audio_url && isPlaying ? 'Pause Audio' : 'Play Candidate Audio'}</span>
                </button>
              )}
            </div>

            {/* Question title & text */}
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
              {item.title}
            </h4>
            <p style={{ fontSize: '0.92rem', color: '#cbd5e1', lineHeight: '1.6', marginBottom: '20px' }}>
              {item.question}
            </p>

            {/* Candidate Transcript Box */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.75)',
              border: item.voice_matched === false
                ? '1px solid rgba(239, 68, 68, 0.4)'
                : '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '12px',
              padding: '16px'
            }}>
              <div style={{
                marginBottom: '8px'
              }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#a5b4fc' }}>
                  Candidate Spoken Response Transcript:
                </span>
              </div>

              <div style={{
                fontSize: '0.92rem',
                color: item.transcript ? '#f1f5f9' : '#64748b',
                fontStyle: item.transcript ? 'normal' : 'italic',
                lineHeight: '1.6'
              }}>
                {item.transcript || (item.recorded
                  ? 'Your recording was saved, but speech could not be transcribed.'
                  : 'No answer recorded for this question.')}
              </div>

              {/* Status explanation for mismatch if any */}
              {item.voice_matched === false && (
                <div style={{
                  marginTop: '10px',
                  padding: '8px 12px',
                  background: 'rgba(239, 68, 68, 0.12)',
                  borderRadius: '8px',
                  fontSize: '0.78rem',
                  color: '#fca5a5',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <ShieldAlert size={14} color="#ef4444" style={{ flexShrink: 0 }} />
                  <span>Voice similarity ({item.voice_similarity_score}%) fell below threshold. Speaker did not match Terms & Conditions baseline.</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
