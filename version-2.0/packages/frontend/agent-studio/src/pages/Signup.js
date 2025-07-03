import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import './LandingPage.css'; // Reuse the landing page styles

const Signup = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { signup, signInWithGoogle, error: authError, currentUser } = useAuth();
  const navigate = useNavigate();

  // Redirect if already logged in
  useEffect(() => {
    if (currentUser) {
      navigate('/dashboard');
    }
  }, [currentUser, navigate]);

  const handleSignup = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      return setError('Passwords do not match');
    }
    
    if (password.length < 6) {
      return setError('Password must be at least 6 characters');
    }

    setError('');
    setLoading(true);

    try {
      await signup(email, password);
      navigate('/dashboard');
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      await signInWithGoogle();
      navigate('/dashboard');
    } catch (error) {
      setError(error.message);
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="signup-page">
      {/* Signup Content */}
      <section className="signup-section">
        <div className="signup-container">
          <div className="signup-content">
            {/* Left Side - Branding */}
            <div className="signup-branding">
              <div className="signup-badge">
                ✨ Join the AI Revolution
              </div>
              <h1>Start Building AI Agents Today</h1>
              <p className="signup-subtitle">
                Create intelligent AI agents that transform your workflow. No coding required, 
                just describe what you want and watch your ideas come to life.
              </p>
              <div className="signup-features">
                <div className="signup-feature">
                  <div className="feature-icon">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div className="feature-content">
                    <div className="feature-title">Build Unlimited Agents</div>
                    <div className="feature-description">Create as many AI agents as you need</div>
                  </div>
                </div>
                <div className="signup-feature">
                  <div className="feature-icon">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div className="feature-content">
                    <div className="feature-title">Deploy in 30 Seconds</div>
                    <div className="feature-description">From idea to live agent instantly</div>
                  </div>
                </div>
                <div className="signup-feature">
                  <div className="feature-icon">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div className="feature-content">
                    <div className="feature-title">WhatsApp Integration</div>
                    <div className="feature-description">Connect to WhatsApp Business API</div>
                  </div>
                </div>
              </div>
              <div className="signup-stats">
                <div className="stat">
                  <span className="stat-number">500+</span>
                  <span className="stat-label">Active Users</span>
                </div>
                <div className="stat">
                  <span className="stat-number">10K+</span>
                  <span className="stat-label">AI Agents Created</span>
                </div>
              </div>
            </div>

            {/* Right Side - Signup Form */}
            <div className="signup-form-container">
              <div className="signup-form-card">
                <div className="form-header">
                  <div className="form-icon">
                    <svg width="32" height="32" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z"></path>
                    </svg>
                  </div>
                  <h2>Create Your Account</h2>
                  <p>Start building AI agents in minutes</p>
                </div>

                {(error || authError) && (
                  <div className="error-alert">
                    {error || authError}
                  </div>
                )}

                <form onSubmit={handleSignup} className="signup-form">
                  <div className="input-group">
                    <label htmlFor="email">Email Address</label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      autoComplete="email"
                      autoFocus
                      placeholder="Enter your email"
                    />
                  </div>

                  <div className="input-group">
                    <label htmlFor="password">Password</label>
                    <input
                      type="password"
                      id="password"
                      name="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      autoComplete="new-password"
                      placeholder="Minimum 6 characters"
                    />
                  </div>

                  <div className="input-group">
                    <label htmlFor="confirmPassword">Confirm Password</label>
                    <input
                      type="password"
                      id="confirmPassword"
                      name="confirmPassword"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      autoComplete="new-password"
                      placeholder="Confirm your password"
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn btn-primary btn-full"
                    disabled={loading || googleLoading}
                  >
                    {loading ? (
                      <>
                        <svg className="loading-spinner" width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="32 32" />
                        </svg>
                        Creating Account...
                      </>
                    ) : (
                      <>
                        Create My Account
                        <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd"></path>
                        </svg>
                      </>
                    )}
                  </button>

                  <div className="divider">
                    <span>OR</span>
                  </div>

                  <button
                    type="button"
                    className="btn btn-outline btn-full"
                    onClick={handleGoogleSignIn}
                    disabled={loading || googleLoading}
                  >
                    {googleLoading ? (
                      <>
                        <svg className="loading-spinner" width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="32 32" />
                        </svg>
                        Connecting...
                      </>
                    ) : (
                      <>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                        </svg>
                        Continue with Google
                      </>
                    )}
                  </button>

                  <div className="form-footer">
                    <p>
                      Already have an account? {" "}
                      <Link to="/login" className="form-link">
                        Sign in here
                      </Link>
                    </p>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Signup;