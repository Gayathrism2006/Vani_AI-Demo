import React from 'react';
import { CheckCircle, Award, Eye, FileText, ArrowRight } from 'lucide-react';

export default function SuccessPage({ assessmentId, onGoToReview }) {
  return (
    <div style={{
      maxWidth: '680px',
      margin: '60px auto',
      padding: '0 24px',
      textAlign: 'center'
    }}>
      <div className="glass-panel" style={{
        padding: '50px 40px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Decorative background glow */}
        <div style={{
          position: 'absolute',
          top: '-80px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '240px',
          height: '240px',
          background: 'rgba(16, 185, 129, 0.2)',
          borderRadius: '50%',
          filter: 'blur(60px)',
          pointerEvents: 'none'
        }} />

        {/* Large Success Icon */}
        <div style={{
          width: '84px',
          height: '84px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #10b981, #059669)',
          margin: '0 auto 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 35px rgba(16, 185, 129, 0.5)'
        }}>
          <CheckCircle size={48} color="#fff" />
        </div>

        {/* Required Headline verbatim */}
        <h2 style={{
          fontSize: '1.85rem',
          fontWeight: 800,
          color: '#f8fafc',
          marginBottom: '12px',
          letterSpacing: '-0.02em'
        }}>
          Your answers have been submitted successfully!
        </h2>

        <p style={{
          color: '#94a3b8',
          fontSize: '1rem',
          lineHeight: '1.6',
          maxWidth: '520px',
          margin: '0 auto 32px'
        }}>
          Your responses, audio recordings, and transcripts have been securely archived. You can now review your answers and listen back to your recordings.
        </p>

        {/* Action Button: Review Answers */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button
            onClick={() => onGoToReview(assessmentId)}
            className="gradient-btn"
            style={{
              padding: '16px 36px',
              borderRadius: '14px',
              fontSize: '1.05rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <Eye size={20} />
            <span>Review Answers</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
