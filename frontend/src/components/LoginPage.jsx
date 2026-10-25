import React, { useState } from 'react';
import { Mic, Lock, Mail, User, ArrowRight, ShieldCheck, AlertCircle, CheckCircle2, Sparkles, Volume2 } from 'lucide-react';

export default function LoginPage({ onLoginSuccess }) {
  // Mode: 'LOGIN' or 'REGISTER'
  const [mode, setMode] = useState('LOGIN');

  // Form states (empty by default so any user can register and log in)
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);

  // Switch between Login and Register tabs
  const handleSwitchMode = (newMode) => {
    setMode(newMode);
    setError('');
    setSuccessMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    const cleanEmail = email.trim().toLowerCase();
    const cleanName = fullName.trim();

    // Validations
    if (!cleanEmail) {
      setError('Email address is required.');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(cleanEmail)) {
      setError('Please enter a valid email address (e.g., user@example.com).');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (mode === 'REGISTER') {
      if (!cleanName) {
        setError('Full name is required to create an account.');
        return;
      }
      if (cleanName.length < 2) {
        setError('Full name must be at least 2 characters long.');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match. Please verify your password confirmation.');
        return;
      }
    }

    setLoading(true);
    const endpoint = mode === 'REGISTER' ? '/api/auth/register' : '/api/auth/login';
    const payload = mode === 'REGISTER'
      ? { full_name: cleanName, email: cleanEmail, password }
      : { email: cleanEmail, password };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `${mode === 'REGISTER' ? 'Registration' : 'Login'} failed. Please try again.`);
      }

      setSuccessMsg(mode === 'REGISTER' ? 'Account created successfully! Logging you in...' : 'Login successful! Redirecting...');

      // Notify parent on success
      setTimeout(() => {
        onLoginSuccess(data.user, data.token);
      }, 400);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: 'calc(100vh - 80px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '480px',
        padding: '36px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Subtle decorative glow */}
        <div style={{
          position: 'absolute',
          top: '-60px',
          right: '-60px',
          width: '180px',
          height: '180px',
          background: 'rgba(99, 102, 241, 0.25)',
          borderRadius: '50%',
          filter: 'blur(50px)',
          pointerEvents: 'none'
        }} />

        {/* Brand header */}
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <div style={{
            width: '60px',
            height: '60px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #6366f1, #d946ef)',
            margin: '0 auto 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 30px rgba(99, 102, 241, 0.5)'
          }}>
            <Mic size={30} color="#fff" />
          </div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#fff', marginBottom: '4px' }}>
            Vani <span className="gradient-text">AI</span>
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.86rem' }}>
            AI-Powered Voice Assessment & Interview Platform
          </p>
        </div>

        {/* Tabs: Sign In vs Create Account */}
        <div style={{
          display: 'flex',
          background: 'rgba(15, 23, 42, 0.7)',
          borderRadius: '12px',
          padding: '4px',
          marginBottom: '22px',
          border: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          <button
            type="button"
            onClick={() => handleSwitchMode('LOGIN')}
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: '9px',
              border: 'none',
              background: mode === 'LOGIN' ? 'linear-gradient(135deg, #6366f1, #4f46e5)' : 'transparent',
              color: mode === 'LOGIN' ? '#fff' : '#94a3b8',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => handleSwitchMode('REGISTER')}
            style={{
              flex: 1,
              padding: '10px',
              borderRadius: '9px',
              border: 'none',
              background: mode === 'REGISTER' ? 'linear-gradient(135deg, #d946ef, #a21caf)' : 'transparent',
              color: mode === 'REGISTER' ? '#fff' : '#94a3b8',
              fontWeight: 700,
              fontSize: '0.88rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error notification */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: '#fb7185',
            padding: '12px 14px',
            borderRadius: '10px',
            fontSize: '0.84rem',
            marginBottom: '18px'
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Success notification */}
        {successMsg && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#34d399',
            padding: '12px 14px',
            borderRadius: '10px',
            fontSize: '0.84rem',
            marginBottom: '18px'
          }}>
            <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Full name input for registration */}
          {mode === 'REGISTER' && (
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                Full Name
              </label>
              <div style={{ position: 'relative' }}>
                <User size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
                  autoComplete="name"
                  style={{
                    width: '100%',
                    padding: '11px 16px 11px 42px',
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '10px',
                    color: '#fff',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#d946ef'}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.12)'}
                />
              </div>
            </div>
          )}

          {/* Email input */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
              Email Address
            </label>
            <div style={{ position: 'relative' }}>
              <Mail size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your.email@example.com"
                autoComplete="email"
                style={{
                  width: '100%',
                  padding: '11px 16px 11px 42px',
                  background: 'rgba(15, 23, 42, 0.65)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '10px',
                  color: '#fff',
                  fontSize: '0.9rem',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
                onFocus={(e) => e.target.style.borderColor = mode === 'REGISTER' ? '#d946ef' : '#6366f1'}
                onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.12)'}
              />
            </div>
          </div>

          {/* Password input */}
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <Lock size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                autoComplete={mode === 'REGISTER' ? 'new-password' : 'current-password'}
                style={{
                  width: '100%',
                  padding: '11px 16px 11px 42px',
                  background: 'rgba(15, 23, 42, 0.65)',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                  borderRadius: '10px',
                  color: '#fff',
                  fontSize: '0.9rem',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
                onFocus={(e) => e.target.style.borderColor = mode === 'REGISTER' ? '#d946ef' : '#6366f1'}
                onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.12)'}
              />
            </div>
          </div>

          {/* Confirm Password input for registration */}
          {mode === 'REGISTER' && (
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                Confirm Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={18} color="#64748b" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  autoComplete="new-password"
                  style={{
                    width: '100%',
                    padding: '11px 16px 11px 42px',
                    background: 'rgba(15, 23, 42, 0.65)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '10px',
                    color: '#fff',
                    fontSize: '0.9rem',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#d946ef'}
                  onBlur={(e) => e.target.style.borderColor = 'rgba(255, 255, 255, 0.12)'}
                />
              </div>
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="gradient-btn"
            style={{
              padding: '13px',
              borderRadius: '10px',
              fontSize: '0.94rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginTop: '6px',
              background: mode === 'REGISTER'
                ? 'linear-gradient(135deg, #d946ef 0%, #8b5cf6 100%)'
                : 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)'
            }}
          >
            {loading ? (
              <span>{mode === 'REGISTER' ? 'Creating Account...' : 'Authenticating...'}</span>
            ) : (
              <>
                <span>{mode === 'REGISTER' ? 'Create My Account' : 'Sign In to Portal'}</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Switch mode footer */}
        <div style={{
          marginTop: '22px',
          textAlign: 'center',
          fontSize: '0.84rem',
          color: '#94a3b8'
        }}>
          {mode === 'LOGIN' ? (
            <span>
              Don't have an account yet?{' '}
              <button
                type="button"
                onClick={() => handleSwitchMode('REGISTER')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#f0abfc',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
              >
                Sign up here
              </button>
            </span>
          ) : (
            <span>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => handleSwitchMode('LOGIN')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#a5b4fc',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textDecoration: 'underline'
                }}
              >
                Sign in here
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
