import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import './LandingPage.css'; // Use the landing page styles to match signup

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { login, signInWithGoogle, error: authError, currentUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the path to redirect to after login (if any)
  const from = location.state?.from || '/';
  const loginMessage = location.state?.message;
  
  // Check if user is already logged in
  useEffect(() => {
    console.log("Login page mounted, checking auth state");
    console.log("Current user:", currentUser);
    console.log("Redirect path:", from);
    
    if (currentUser) {
      console.log("User already logged in, redirecting to:", from);
      navigate(from, { replace: true });
    }
  }, [currentUser, navigate, from]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log("Attempting login with email:", email);
      await login(email, password);
      console.log("Login successful, waiting for auth state update");
      // Don't navigate here - let the useEffect handle redirection when currentUser updates
    } catch (error) {
      console.error("Login error:", error);
      setError(error.message || "Failed to sign in");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError('');
    setGoogleLoading(true);

    try {
      console.log("Attempting Google sign in");
      await signInWithGoogle();
      console.log("Google sign in successful, waiting for auth state update");
      // Don't navigate here - let the useEffect handle redirection when currentUser updates
    } catch (error) {
      console.error("Google sign in error:", error);
      setError(error.userFriendlyMessage || error.message || "Failed to sign in with Google");
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="signup-page">
      {/* Login Content */}
      <section className="signup-section">
        <div className="signup-container">
          <div className="signup-content">
            {/* Left Side - Branding */}
            <div className="signup-branding">
              <div className="signup-badge">
                ✨ Welcome Back
              </div>
              <h1>Sign in to Your AI Hub</h1>
              <p className="signup-subtitle">
                Continue building amazing AI agents with Alchemist. Access your dashboard, 
                manage deployments, and create intelligent agents in minutes.
              </p>
              <div className="signup-features">
                <div className="signup-feature">
                  <div className="feature-icon">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div className="feature-content">
                    <div className="feature-title">Enterprise Security</div>
                    <div className="feature-description">Bank-grade encryption & security</div>
                  </div>
                </div>
                <div className="signup-feature">
                  <div className="feature-icon">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div className="feature-content">
                    <div className="feature-title">Lightning Fast</div>
                    <div className="feature-description">Deploy agents in 30 seconds</div>
                  </div>
                </div>
                <div className="signup-feature">
                  <div className="feature-icon">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                    </svg>
                  </div>
                  <div className="feature-content">
                    <div className="feature-title">Smart Analytics</div>
                    <div className="feature-description">Real-time performance insights</div>
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

            {/* Right Side - Login Form */}
            <div className="signup-form-container">
              <div className="signup-form-card">
                <div className="form-header">
                  <div className="form-icon">
                    <svg width="32" height="32" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"></path>
                    </svg>
                  </div>
                  <h2>Sign In</h2>
                  <p>{loginMessage || 'Access your AI agent dashboard'}</p>
                </div>

                {(error || authError) && (
                  <div className="error-alert">
                    {error || authError}
                  </div>
                )}

                <form onSubmit={handleLogin} className="signup-form">
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
                      autoComplete="current-password"
                      placeholder="Enter your password"
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
                        Signing in...
                      </>
                    ) : (
                      <>
                        Sign In
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
                      Don't have an account? {" "}
                      <Link to="/signup" className="form-link">
                        Create one here
                      </Link>
                    </p>
                    <p style={{ marginTop: '0.5rem' }}>
                      <Link to="/forgot-password" className="form-link">
                        Forgot your password?
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

export default Login;
