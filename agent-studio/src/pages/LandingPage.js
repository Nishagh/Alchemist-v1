import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { useAuth } from '../utils/AuthContext';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Container,
  Grid,
  CircularProgress,
  Card,
  CardContent,
  Divider,
  useTheme,
  alpha,
  Fade,
  Grow,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stack
} from '@mui/material';
import { 
  AutoAwesome as AutoAwesomeIcon,
  Psychology as PsychologyIcon,
  LocalLibrary as LibraryIcon,
  RocketLaunch as RocketLaunchIcon,
  Code as CodeIcon,
  Business as BusinessIcon,
  Science as ScienceIcon,
  AttachMoney as MoneyIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  CloudSync as CloudSyncIcon,
  CheckCircle as CheckCircleIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  Timer as TimerIcon,
  ExpandMore as ExpandMoreIcon,
  LinkedIn as LinkedInIcon,
  Twitter as TwitterIcon,
  GitHub as GitHubIcon,
  AutoAwesome
} from '@mui/icons-material';
import { interactWithAlchemist } from '../services';

// Example agent requirements for inspiration
const exampleRequirements = [
  {
    text: "Create a marketing assistant that helps write social media posts and analyzes their performance",
    icon: <BusinessIcon />,
  },
  {
    text: "Build a coding tutor that can explain complex programming concepts and review code",
    icon: <CodeIcon />,
  },
  {
    text: "Make a research agent that can summarize scientific papers and extract key findings",
    icon: <ScienceIcon />,
  },
  {
    text: "Design a financial advisor that helps with budgeting and investment recommendations",
    icon: <MoneyIcon />,
  }
];

// Features data
const features = [
  {
    icon: <SpeedIcon />,
    title: "Lightning Fast",
    description: "Create and deploy AI agents in minutes, not hours. Our streamlined process gets you up and running quickly."
  },
  {
    icon: <SecurityIcon />,
    title: "Enterprise Security",
    description: "Bank-level security with encrypted data transmission and secure cloud infrastructure."
  },
  {
    icon: <CloudSyncIcon />,
    title: "Cloud-Native",
    description: "Scalable cloud infrastructure that grows with your needs. No setup or maintenance required."
  },
  {
    icon: <PsychologyIcon />,
    title: "Advanced AI",
    description: "Powered by cutting-edge AI models that understand context and provide intelligent responses."
  }
];

// Statistics data
const stats = [
  { number: "10,000+", label: "Agents Created", icon: <AutoAwesomeIcon /> },
  { number: "500+", label: "Happy Users", icon: <PeopleIcon /> },
  { number: "99.9%", label: "Uptime", icon: <TrendingUpIcon /> },
  { number: "< 2min", label: "Avg. Setup Time", icon: <TimerIcon /> }
];

// Testimonials data
const testimonials = [
  {
    name: "Sarah Chen",
    role: "Product Manager at TechCorp",
    avatar: "SC",
    text: "Alchemist has transformed how we handle customer support. Our AI agent handles 80% of inquiries automatically.",
    rating: 5
  },
  {
    name: "Michael Rodriguez",
    role: "Startup Founder",
    avatar: "MR", 
    text: "Built a research assistant in 5 minutes that would have taken our team weeks to develop. Incredible!",
    rating: 5
  },
  {
    name: "Dr. Emily Watson",
    role: "Research Scientist",
    avatar: "EW",
    text: "The scientific paper summarization agent has saved me hours of research time every week.",
    rating: 5
  }
];

// FAQ data
const faqs = [
  {
    question: "How quickly can I create an AI agent?",
    answer: "Most agents can be created and deployed in under 2 minutes. Simply describe what you want your agent to do, and Alchemist handles the rest."
  },
  {
    question: "Do I need programming knowledge?",
    answer: "No programming knowledge required! Alchemist uses natural language processing to understand your requirements and automatically generates the agent code."
  },
  {
    question: "How secure is my data?",
    answer: "We use enterprise-grade security with encrypted data transmission, secure cloud infrastructure, and compliance with industry standards."
  },
  {
    question: "Can I customize my agent after creation?",
    answer: "Yes! You can continuously refine and improve your agent's capabilities through our intuitive editor interface."
  },
  {
    question: "What kind of agents can I create?",
    answer: "You can create agents for customer support, research assistance, content creation, data analysis, coding help, and much more."
  }
];

const LandingPage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const { currentUser } = useAuth();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Check if user is authenticated
    if (!currentUser) {
      // Store the agent creation data in sessionStorage for after login
      sessionStorage.setItem('pendingAgentCreation', JSON.stringify({
        input: input.trim(),
        timestamp: Date.now()
      }));
      
      // Redirect to login with return path
      navigate('/login', { 
        state: { 
          from: '/agent-creation-redirect',
          message: 'Please sign in to create your AI agent'
        } 
      });
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      
      // Generate a new agent ID
      const newAgentId = uuidv4();
      
      // Send the user input to Alchemist
      await interactWithAlchemist(input, newAgentId);
      
      // Navigate to the agent editor with the new agent ID
      navigate(`/agent-editor/${newAgentId}`);
    } catch (error) {
      console.error('Error creating agent:', error);
      setError('Failed to create agent. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillExampleRequirement = (example) => {
    setInput(example.text);
  };

  return (
    <Box sx={{ width: '100%', overflow: 'hidden' }}>
      {/* Hero Section */}
      <Box 
        sx={{ 
          background: `linear-gradient(135deg, ${alpha(theme.palette.grey[50], 1)} 0%, ${alpha(theme.palette.grey[100], 1)} 100%)`,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.05) 100%)'
          }
        }}
      >
        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Fade in={true} timeout={1000}>
            <Grid container spacing={6} alignItems="center">
              <Grid item xs={12} md={6}>
                <Box sx={{ textAlign: { xs: 'center', md: 'left' } }}>
                  <Chip 
                    label="🚀 New: AI Agent Builder 2.0" 
                    color="primary" 
                    variant="outlined"
                    sx={{ mb: 3, fontWeight: 'bold' }}
                  />
                  <Typography 
                    variant="h1" 
                    component="h1" 
                    sx={{ 
                      fontWeight: 900,
                      fontSize: { xs: '2.5rem', md: '3.5rem' },
                      color: theme.palette.text.primary,
                      mb: 2,
                      lineHeight: 1.2
                    }}
                  >
                    Build AI Agents in
                    <Box component="span" sx={{ color: theme.palette.text.primary, display: 'block', fontWeight: 900 }}>
                      Under 2 Minutes
                    </Box>
                  </Typography>
                  <Typography 
                    variant="h5" 
                    color="text.secondary" 
                    sx={{ mb: 4, fontWeight: 400, lineHeight: 1.4 }}
                  >
                    Transform your ideas into intelligent AI agents with natural language. 
                    No coding required, enterprise-ready security.
                  </Typography>
                  <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 4 }}>
                    <Button
                      variant="contained"
                      size="large"
                      startIcon={<RocketLaunchIcon />}
                      onClick={() => document.getElementById('agent-builder').scrollIntoView({ behavior: 'smooth' })}
                      sx={{ 
                        py: 1.5,
                        px: 4,
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        borderRadius: 3
                      }}
                    >
                      Start Building Now
                    </Button>
                    <Button
                      variant="outlined"
                      size="large"
                      sx={{ py: 1.5, px: 4, fontWeight: 'bold', borderRadius: 3 }}
                    >
                      View Examples
                    </Button>
                  </Stack>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                    <Typography variant="body2" color="text.secondary">Trusted by:</Typography>
                    <Chip label="500+ Users" size="small" variant="outlined" />
                    <Chip label="10K+ Agents" size="small" variant="outlined" />
                    <Chip label="99.9% Uptime" size="small" variant="outlined" />
                  </Box>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                  <Box 
                    component="img" 
                    src="/img/agent-illustration.svg" 
                    alt="AI Agent Illustration" 
                    sx={{ 
                      maxWidth: '500px', 
                      width: '100%',
                      height: 'auto',
                      filter: 'drop-shadow(0px 10px 30px rgba(0, 0, 0, 0.1))',
                      animation: 'float 3s ease-in-out infinite'
                    }}
                    onError={(e) => {e.target.style.display = 'none'}}
                  />
                </Box>
              </Grid>
            </Grid>
          </Fade>
        </Container>
      </Box>

      {/* Stats Section */}
      <Box sx={{ py: 8, bgcolor: theme.palette.background.paper }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            {stats.map((stat, index) => (
              <Grid item xs={6} md={3} key={index}>
                <Grow in={true} timeout={800 + index * 200}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Box sx={{ 
                      display: 'inline-flex',
                      p: 2,
                      borderRadius: '50%',
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      mb: 2
                    }}>
                      {stat.icon}
                    </Box>
                    <Typography variant="h3" component="div" sx={{ fontWeight: 900, mb: 1 }}>
                      {stat.number}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {stat.label}
                    </Typography>
                  </Box>
                </Grow>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Agent Builder Section */}
      <Box id="agent-builder" sx={{ py: 10, bgcolor: alpha(theme.palette.primary.main, 0.02) }}>
        <Container maxWidth="lg">
          <Grid container spacing={6} alignItems="stretch">
            <Grid item xs={12} md={7}>
              <Grow in={true} timeout={800}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 4, 
                    borderRadius: 3, 
                    height: '100%',
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    boxShadow: '0 8px 40px rgba(0, 0, 0, 0.08)',
                  }}
                >
                  <Typography variant="h4" component="h2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <PsychologyIcon sx={{ mr: 1.5, color: theme.palette.primary.main }} />
                    Create Your Agent
                  </Typography>
                  
                  <form onSubmit={handleSubmit}>
                    <TextField
                      fullWidth
                      multiline
                      rows={6}
                      label="What should your AI agent do?"
                      placeholder="Describe the purpose, capabilities, and any specific knowledge your agent should have..."
                      variant="outlined"
                      value={input}
                      onChange={handleInputChange}
                      disabled={loading}
                      sx={{ 
                        mb: 3, 
                        mt: 2,
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 2
                        }
                      }}
                    />
                    
                    <Button
                      type="submit"
                      variant="contained"
                      color="primary"
                      size="large"
                      fullWidth
                      endIcon={loading ? <CircularProgress size={24} color="inherit" /> : <RocketLaunchIcon />}
                      disabled={loading || !input.trim()}
                      sx={{ 
                        py: 2,
                        fontWeight: 'bold',
                        fontSize: '1.1rem',
                        borderRadius: 2
                      }}
                    >
                      {loading ? 'Creating Your Agent...' : currentUser ? 'Create My Agent' : 'Sign In & Create Agent'}
                    </Button>
                    
                    {error && (
                      <Typography color="error" sx={{ mt: 2 }}>
                        {error}
                      </Typography>
                    )}
                    
                    {!currentUser && (
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                        🔒 You'll be asked to sign in before creating your agent
                      </Typography>
                    )}
                  </form>
                </Paper>
              </Grow>
            </Grid>
            
            <Grid item xs={12} md={5}>
              <Grow in={true} timeout={1000}>
                <Paper 
                  elevation={0}
                  sx={{ 
                    p: 4, 
                    borderRadius: 3, 
                    height: '100%',
                    border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                    boxShadow: '0 8px 40px rgba(0, 0, 0, 0.08)',
                  }}
                >
                  <Typography variant="h5" component="h3" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <LibraryIcon sx={{ mr: 1.5, color: theme.palette.primary.main }} />
                    Popular Examples
                  </Typography>
                  
                  <Box sx={{ mt: 3 }}>
                    {exampleRequirements.map((example, index) => (
                      <Card 
                        key={index}
                        elevation={0}
                        onClick={() => fillExampleRequirement(example)}
                        sx={{ 
                          cursor: 'pointer', 
                          mb: 2,
                          transition: 'all 0.3s ease',
                          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                          borderRadius: 2,
                          '&:hover': {
                            transform: 'translateY(-4px)',
                            bgcolor: alpha(theme.palette.primary.light, 0.05),
                            borderColor: alpha(theme.palette.primary.main, 0.3),
                            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.1)'
                          }
                        }}
                      >
                        <CardContent sx={{ 
                          display: 'flex',
                          alignItems: 'flex-start',
                          p: 3,
                          '&:last-child': { pb: 3 }
                        }}>
                          <Box sx={{ 
                            mr: 2, 
                            color: theme.palette.primary.main,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            p: 1.5,
                            borderRadius: 2,
                            backgroundColor: alpha(theme.palette.primary.main, 0.1),
                          }}>
                            {example.icon}
                          </Box>
                          <Typography variant="body1" sx={{ lineHeight: 1.5 }}>
                            {example.text}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                </Paper>
              </Grow>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Features Section */}
      <Box sx={{ py: 10 }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h3" component="h2" gutterBottom sx={{ fontWeight: 'bold' }}>
              Why Choose Alchemist?
            </Typography>
            <Typography variant="h6" color="text.secondary" sx={{ maxWidth: '600px', mx: 'auto' }}>
              Powerful features designed to make AI agent creation simple, secure, and scalable.
            </Typography>
          </Box>
          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Grow in={true} timeout={1000 + index * 200}>
                  <Card 
                    elevation={0}
                    sx={{ 
                      p: 3, 
                      textAlign: 'center',
                      height: '100%',
                      border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                      borderRadius: 3,
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: '0 12px 40px rgba(0, 0, 0, 0.1)',
                        borderColor: alpha(theme.palette.primary.main, 0.2)
                      }
                    }}
                  >
                    <Box sx={{ 
                      display: 'inline-flex',
                      p: 2,
                      borderRadius: 3,
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      mb: 3
                    }}>
                      {feature.icon}
                    </Box>
                    <Typography variant="h5" component="h3" gutterBottom sx={{ fontWeight: 'bold' }}>
                      {feature.title}
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </Card>
                </Grow>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* Testimonials Section */}
      <Box sx={{ py: 10, bgcolor: alpha(theme.palette.primary.main, 0.02) }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h3" component="h2" gutterBottom sx={{ fontWeight: 'bold' }}>
              What Our Users Say
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Join thousands of satisfied users who've transformed their workflows with Alchemist.
            </Typography>
          </Box>
          <Grid container spacing={4}>
            {testimonials.map((testimonial, index) => (
              <Grid item xs={12} md={4} key={index}>
                <Grow in={true} timeout={1200 + index * 200}>
                  <Card 
                    elevation={0}
                    sx={{ 
                      p: 4,
                      height: '100%',
                      border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                      borderRadius: 3,
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.1)'
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', mb: 3 }}>
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <StarIcon key={i} sx={{ color: '#ffd700', fontSize: '1.2rem' }} />
                      ))}
                    </Box>
                    <Typography variant="body1" sx={{ mb: 3, fontStyle: 'italic', lineHeight: 1.6 }}>
                      "{testimonial.text}"
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, bgcolor: theme.palette.primary.main }}>
                        {testimonial.avatar}
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {testimonial.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {testimonial.role}
                        </Typography>
                      </Box>
                    </Box>
                  </Card>
                </Grow>
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* FAQ Section */}
      <Box sx={{ py: 10 }}>
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <Typography variant="h3" component="h2" gutterBottom sx={{ fontWeight: 'bold' }}>
              Frequently Asked Questions
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Everything you need to know about creating AI agents with Alchemist.
            </Typography>
          </Box>
          {faqs.map((faq, index) => (
            <Grow in={true} timeout={1000 + index * 100} key={index}>
              <Accordion 
                elevation={0}
                sx={{ 
                  mb: 2,
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                  borderRadius: 2,
                  '&:before': { display: 'none' },
                  '&.Mui-expanded': {
                    margin: '0 0 16px 0'
                  }
                }}
              >
                <AccordionSummary 
                  expandIcon={<ExpandMoreIcon />}
                  sx={{ 
                    px: 3,
                    py: 2,
                    '&.Mui-expanded': {
                      minHeight: 'auto'
                    },
                    '& .MuiAccordionSummary-content.Mui-expanded': {
                      margin: '12px 0'
                    }
                  }}
                >
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    {faq.question}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ px: 3, pb: 3 }}>
                  <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                    {faq.answer}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            </Grow>
          ))}
        </Container>
      </Box>

      {/* Footer */}
      <Box sx={{ py: 6, bgcolor: theme.palette.grey[900], color: 'white' }}>
        <Container maxWidth="lg">
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <AutoAwesome sx={{ mr: 1 }} />
                Alchemist
              </Typography>
              <Typography variant="body1" color="grey.300" sx={{ mb: 3, maxWidth: '400px' }}>
                Transform your ideas into intelligent AI agents. No coding required, 
                enterprise-ready security, and lightning-fast deployment.
              </Typography>
              <Stack direction="row" spacing={2}>
                <Button 
                  variant="outlined" 
                  size="small" 
                  startIcon={<TwitterIcon />}
                  sx={{ color: 'white', borderColor: 'grey.600' }}
                >
                  Twitter
                </Button>
                <Button 
                  variant="outlined" 
                  size="small" 
                  startIcon={<LinkedInIcon />}
                  sx={{ color: 'white', borderColor: 'grey.600' }}
                >
                  LinkedIn
                </Button>
                <Button 
                  variant="outlined" 
                  size="small" 
                  startIcon={<GitHubIcon />}
                  sx={{ color: 'white', borderColor: 'grey.600' }}
                >
                  GitHub
                </Button>
              </Stack>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="h6" gutterBottom>
                Product
              </Typography>
              <List dense>
                <ListItem disablePadding>
                  <ListItemText primary="Features" sx={{ color: 'grey.300' }} />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemText primary="Pricing" sx={{ color: 'grey.300' }} />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemText primary="Documentation" sx={{ color: 'grey.300' }} />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemText primary="API" sx={{ color: 'grey.300' }} />
                </ListItem>
              </List>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="h6" gutterBottom>
                Support
              </Typography>
              <List dense>
                <ListItem disablePadding>
                  <ListItemText primary="Help Center" sx={{ color: 'grey.300' }} />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemText primary="Contact Us" sx={{ color: 'grey.300' }} />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemText primary="Status" sx={{ color: 'grey.300' }} />
                </ListItem>
                <ListItem disablePadding>
                  <ListItemText primary="Community" sx={{ color: 'grey.300' }} />
                </ListItem>
              </List>
            </Grid>
          </Grid>
          <Divider sx={{ my: 4, borderColor: 'grey.700' }} />
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap' }}>
            <Typography variant="body2" color="grey.400">
              © 2024 Alchemist. All rights reserved.
            </Typography>
            <Box sx={{ display: 'flex', gap: 3 }}>
              <Typography variant="body2" color="grey.400" sx={{ cursor: 'pointer', '&:hover': { color: 'white' } }}>
                Privacy Policy
              </Typography>
              <Typography variant="body2" color="grey.400" sx={{ cursor: 'pointer', '&:hover': { color: 'white' } }}>
                Terms of Service
              </Typography>
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Add CSS keyframes for floating animation */}
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
      `}</style>
    </Box>
  );
};

export default LandingPage; 