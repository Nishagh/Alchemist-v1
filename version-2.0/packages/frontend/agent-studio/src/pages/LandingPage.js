import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // If user is already logged in, redirect to dashboard
  useEffect(() => {
    if (currentUser) {
      navigate('/dashboard');
    }
  }, [currentUser, navigate]);

  // Handle scroll effect for navbar
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Handle smooth scrolling for anchor links
  const handleAnchorClick = (e, href) => {
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      const offsetTop = target.offsetTop - 80;
      window.scrollTo({
        top: offsetTop,
        behavior: 'smooth'
      });
    }
  };

  const handleStartBuilding = () => {
    navigate('/signup');
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const handleMobileMenuClick = (e, href) => {
    setMobileMenuOpen(false);
    if (href) {
      handleAnchorClick(e, href);
    }
  };

  return (
    <div>
      {/* Modern Navigation */}
      <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`} id="navbar">
        <div className="nav-container">
          <div className="nav-logo">
            <h2>
              <svg width="28" height="28" fill="currentColor" viewBox="0 0 24 24" style={{ marginRight: '0.5rem' }}>
                <path d="m19 9 1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25z"></path>
              </svg>
              Alchemist
            </h2>
          </div>
          <ul className={`nav-menu ${mobileMenuOpen ? 'active' : ''}`}>
            <li><a href="#features" onClick={(e) => handleMobileMenuClick(e, '#features')}>Features</a></li>
            <li><a href="#how-it-works" onClick={(e) => handleMobileMenuClick(e, '#how-it-works')}>How It Works</a></li>
            <li><a href="#pricing" onClick={(e) => handleMobileMenuClick(e, '#pricing')}>Pricing</a></li>
            <li><a href="#demo" className="nav-cta" onClick={(e) => { e.preventDefault(); setMobileMenuOpen(false); handleStartBuilding(); }}>Start Building Free</a></li>
          </ul>
          <div className={`hamburger ${mobileMenuOpen ? 'active' : ''}`} onClick={toggleMobileMenu}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </nav>

      {/* Modern Hero Section */}
      <section className="hero">
        <div className="hero-container">
          <div className="hero-content">
            <div className="hero-badge">
              New: Build unlimited agents for free
            </div>
            <h1>Build AI Agents<br />Without Code</h1>
            <p className="hero-subtitle">
              The most elegant way to create intelligent AI agents. No coding required, no limits on creativity. 
              Build, test, and deploy production-ready agents in minutes, not months.
            </p>
            <div className="hero-features">
              <div className="feature-chip">🎯 Visual Builder</div>
              <div className="feature-chip">📚 Smart Knowledge</div>
              <div className="feature-chip">🚀 One-Click Deploy</div>
              <div className="feature-chip">💬 WhatsApp Ready</div>
            </div>
            <div className="hero-cta">
              <a href="#demo" className="btn btn-primary" onClick={handleStartBuilding}>
                Start Building Free
                <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd"></path>
                </svg>
              </a>
              <a href="#how-it-works" className="btn btn-secondary" onClick={(e) => handleAnchorClick(e, '#how-it-works')}>
                See How It Works
                <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"></path>
                  <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"></path>
                </svg>
              </a>
            </div>
          </div>
          <div className="hero-visual">
            <div className="hero-dashboard">
              <div className="dashboard-grid">
                <div className="dashboard-card">
                  <div className="card-header">
                    <div className="status-dot active"></div>
                    <span>Agent Status</span>
                  </div>
                  <div className="card-metric">Active</div>
                </div>
                <div className="dashboard-card">
                  <div className="card-header">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z"/>
                    </svg>
                    <span>Messages</span>
                  </div>
                  <div className="card-metric">1.2K</div>
                </div>
                <div className="dashboard-card">
                  <div className="card-header">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M13 3l-6 18h4l6-18h-4z"/>
                    </svg>
                    <span>Deploy Time</span>
                  </div>
                  <div className="card-metric">30s</div>
                </div>
                <div className="dashboard-card">
                  <div className="card-header">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    </svg>
                    <span>Performance</span>
                  </div>
                  <div className="card-metric">99.9%</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="section" id="features">
        <div className="container">
          <div className="section-header">
            <div className="section-badge">Features</div>
            <h2 className="section-title">Everything You Need to Build AI Agents</h2>
            <p className="section-subtitle">
              Powerful, intuitive tools designed to make AI agent creation simple, secure, and scalable. 
              No technical expertise required.
            </p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <svg width="64" height="64" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  <circle cx="12" cy="8" r="2"/>
                  <path d="M12 14c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
              </div>
              <h3>Visual Agent Builder</h3>
              <p>Create AI agents through natural conversation. Simply describe what you want your agent to do - no coding, no complexity, just pure creativity.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="64" height="64" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                  <polyline points="14,2 14,8 20,8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10,9 9,9 8,9"/>
                </svg>
              </div>
              <h3>Smart Knowledge Integration</h3>
              <p>Upload documents, PDFs, and files. Your agents automatically learn from your content with advanced semantic search and understanding.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="64" height="64" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M18.5 12.5l-1.41-1.41"/>
                  <path d="M6.91 6.91l-1.41-1.41"/>
                </svg>
              </div>
              <h3>Seamless API Integration</h3>
              <p>Connect any service with OpenAPI specifications. Your agents can interact with external tools, databases, and services automatically.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="64" height="64" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                  <path d="M12 6V4l4 4-4 4v-2"/>
                </svg>
              </div>
              <h3>One-Click Deployment</h3>
              <p>Deploy to Google Cloud Run with enterprise-grade performance. 60-80% faster response times with automatic scaling.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="64" height="64" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-5 2.5l3.5 2.5-3.5 2.5V6.5zM6.5 6.5L10 9l-3.5 2.5V6.5z"/>
                  <circle cx="12" cy="12" r="2"/>
                </svg>
              </div>
              <h3>WhatsApp Integration</h3>
              <p>Connect your agents to WhatsApp Business in 4 simple steps. No new accounts needed - use your existing business setup.</p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <svg width="64" height="64" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
              </div>
              <h3>AI Training & Fine-tuning</h3>
              <p>Improve your agents with conversational training. Generate training data and optimize models for better performance over time.</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="section" id="how-it-works">
        <div className="container">
          <div className="section-header">
            <div className="section-badge">Process</div>
            <h2 className="section-title">From Idea to Agent in Minutes</h2>
            <p className="section-subtitle">
              Our streamlined process makes AI agent creation intuitive and fast. 
              No technical knowledge required.
            </p>
          </div>
          <div className="steps-container">
            <div className="steps-grid">
              <div className="step-card">
                <div className="step-number">1</div>
                <div className="step-content">
                  <h3>Describe Your Vision</h3>
                  <p>Simply tell Alchemist what you want your agent to do using natural language. Our AI understands your requirements and creates the foundation.</p>
                </div>
              </div>
              <div className="step-card">
                <div className="step-number">2</div>
                <div className="step-content">
                  <h3>Add Knowledge & Connect APIs</h3>
                  <p>Upload documents, PDFs, or connect APIs. Your agent learns from your content and gains the ability to interact with external services.</p>
                </div>
              </div>
              <div className="step-card">
                <div className="step-number">3</div>
                <div className="step-content">
                  <h3>Test & Refine</h3>
                  <p>Test your agent in our built-in interface. Train it with conversation examples to improve responses and accuracy over time.</p>
                </div>
              </div>
              <div className="step-card">
                <div className="step-number">4</div>
                <div className="step-content">
                  <h3>Deploy & Scale</h3>
                  <p>One-click deployment to production. Connect to WhatsApp, embed on your website, or integrate via API. Scale automatically.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Billing Model Section */}
      <section className="section billing-model">
        <div className="container">
          <div className="section-header">
            <div className="section-badge">Billing</div>
            <h2 className="section-title">Simple, Fair Pricing</h2>
            <p className="section-subtitle">
              Build unlimited agents for free. Pay only when you deploy to production. 
              No hidden fees, no surprises.
            </p>
          </div>
          <div className="billing-steps">
            <div className="billing-step">
              <div className="billing-icon">🆓</div>
              <h3>Build for Free</h3>
              <p>Create unlimited AI agents, add knowledge bases, connect APIs, and test everything completely free. No time limits, no feature restrictions.</p>
            </div>
            <div className="billing-step">
              <div className="billing-icon">🚀</div>
              <h3>Deploy When Ready</h3>
              <p>Only when you're ready to make your agent live and start serving real users do you begin paying for deployment and usage.</p>
            </div>
            <div className="billing-step">
              <div className="billing-icon">📊</div>
              <h3>Pay Per Use</h3>
              <p>Simple usage-based pricing: ₹1 per 1,000 characters. No monthly fees, no hidden costs. Scale up or down automatically.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="section" id="pricing">
        <div className="container">
          <div className="section-header">
            <div className="section-badge">Pricing</div>
            <h2 className="section-title">Choose Your Plan</h2>
            <p className="section-subtitle">
              Start building for free. Scale when you're ready. 
              Enterprise options available for large organizations.
            </p>
          </div>
          <div className="pricing-grid">
            <div className="pricing-card">
              <div className="pricing-header">
                <h3>Development</h3>
                <div className="pricing-price">
                  <span className="price">₹0</span>
                  <span className="price-period">forever</span>
                </div>
                <p>Perfect for building and testing</p>
              </div>
              <div className="pricing-features">
                <div className="feature">✅ Unlimited agent creation</div>
                <div className="feature">✅ Full testing environment</div>
                <div className="feature">✅ Knowledge base integration</div>
                <div className="feature">✅ API connections</div>
                <div className="feature">✅ Fine-tuning & training</div>
                <div className="feature">✅ Community support</div>
              </div>
              <a href="#demo" className="btn btn-outline" onClick={handleStartBuilding}>Start Building Free</a>
            </div>

            <div className="pricing-card featured">
              <div className="pricing-badge">Pay Per Use</div>
              <div className="pricing-header">
                <h3>Production</h3>
                <div className="pricing-price">
                  <span className="price">₹1</span>
                  <span className="price-period">per 1K characters</span>
                </div>
                <p>When you're ready to go live</p>
              </div>
              <div className="pricing-features">
                <div className="feature">✅ Everything in Development</div>
                <div className="feature">✅ Production deployment</div>
                <div className="feature">✅ WhatsApp integration</div>
                <div className="feature">✅ Custom domain</div>
                <div className="feature">✅ Analytics & monitoring</div>
                <div className="feature">✅ Priority support</div>
              </div>
              <a href="#demo" className="btn btn-primary" onClick={handleStartBuilding}>Deploy Your Agent</a>
            </div>

            <div className="pricing-card">
              <div className="pricing-header">
                <h3>Enterprise</h3>
                <div className="pricing-price">
                  <span className="price">Custom</span>
                  <span className="price-period">volume pricing</span>
                </div>
                <p>For large organizations</p>
              </div>
              <div className="pricing-features">
                <div className="feature">✅ Everything in Production</div>
                <div className="feature">✅ Volume discounts</div>
                <div className="feature">✅ Dedicated infrastructure</div>
                <div className="feature">✅ SLA guarantees</div>
                <div className="feature">✅ Dedicated support</div>
                <div className="feature">✅ Custom integrations</div>
              </div>
              <a href="#contact" className="btn btn-outline">Contact Sales</a>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="section cta-section" id="demo">
        <div className="container">
          <div className="cta-content">
            <div className="section-badge">Get Started</div>
            <h2>Ready to Build Your First AI Agent?</h2>
            <p>Start building your first AI agent today. Create unlimited agents for free - pay only when you deploy to production.</p>
            <div className="cta-buttons">
              <a href="#" className="btn btn-primary" onClick={handleStartBuilding}>
                Start Building Free
                <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd"></path>
                </svg>
              </a>
              <a href="#" className="btn btn-outline">
                View Documentation
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <div className="footer-content">
            <div className="footer-section">
              <h3>
                <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24" style={{ marginRight: '0.5rem', verticalAlign: 'middle' }}>
                  <path d="m19 9 1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25z"></path>
                </svg>
                Alchemist
              </h3>
              <p>Build, deploy, and manage intelligent AI agents without code. Create your first agent in minutes, not months.</p>
              <div className="social-links">
                <a href="#" aria-label="Twitter">
                  <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"></path>
                  </svg>
                </a>
                <a href="#" aria-label="LinkedIn">
                  <svg width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"></path>
                  </svg>
                </a>
              </div>
            </div>
            <div className="footer-section">
              <h4>Product</h4>
              <ul>
                <li><a href="#features">Features</a></li>
                <li><a href="#pricing">Pricing</a></li>
                <li><a href="#">Documentation</a></li>
                <li><a href="#">API Reference</a></li>
                <li><a href="#">Status</a></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Company</h4>
              <ul>
                <li><a href="#">About</a></li>
                <li><a href="#">Blog</a></li>
                <li><a href="#">Careers</a></li>
                <li><a href="#">Press</a></li>
                <li><a href="#">Partners</a></li>
              </ul>
            </div>
            <div className="footer-section">
              <h4>Support</h4>
              <ul>
                <li><a href="#">Help Center</a></li>
                <li><a href="#">Community</a></li>
                <li><a href="#">Contact</a></li>
                <li><a href="#">Security</a></li>
                <li><a href="#">Privacy</a></li>
              </ul>
            </div>
          </div>
          <div className="footer-bottom">
            <p>&copy; 2024 Alchemist. All rights reserved. Built with ❤️ for the AI community.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;