# 🧪 Alchemist Agent Studio

The most elegant way to create intelligent AI agents without code. Build, test, and deploy production-ready agents in minutes, not months.

> **Frontend-Only Service**: This is the React frontend for the Alchemist platform. All backend functionality is handled by dedicated microservices. See [AGENT_ENGINE_INTEGRATION.md](./AGENT_ENGINE_INTEGRATION.md) for API integration details.

## ✨ Features

- **Visual Agent Builder** - Create AI agents through natural conversation
- **Smart Knowledge Integration** - Upload documents, PDFs, and files for semantic search
- **Seamless API Integration** - Connect any service with OpenAPI specifications
- **One-Click Deployment** - Deploy to Google Cloud Run with enterprise-grade performance
- **WhatsApp Integration** - Connect your agents to WhatsApp Business in 4 simple steps
- **AI Training & Fine-tuning** - Improve your agents with conversational training
- **Real-time Billing** - Track costs and usage with development vs production modes
- **Analytics Dashboard** - Comprehensive insights and reporting

## 🚀 Quick Start

### Prerequisites

- Node.js 18 or higher
- Firebase account for authentication and database
- Google Cloud account for deployment (optional)

### Installation

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd agent-studio
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   
   Update `.env` with your configuration:
   ```env
   # Firebase Configuration
   REACT_APP_FIREBASE_API_KEY=your-firebase-api-key
   REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   REACT_APP_FIREBASE_PROJECT_ID=your-project-id
   REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
   REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
   REACT_APP_FIREBASE_APP_ID=your-app-id
   
   # API Configuration
   REACT_APP_API_BASE_URL=http://localhost:3001
   REACT_APP_UNIVERSAL_AGENT_URL=https://your-agent-service-url
   
   # WhatsApp Business API (optional)
   REACT_APP_WHATSAPP_SERVICE_URL=http://localhost:8000
   REACT_APP_WHATSAPP_API_KEY=your-optional-api-key
   ```

3. **Start development server:**
   ```bash
   npm start
   ```
   
   Open [http://localhost:3000](http://localhost:3000) to view the application.

## 🏗️ Architecture

### Frontend Structure

```
src/
├── components/
│   ├── AgentEditor/              # Agent creation and management
│   │   ├── AgentConfiguration/   # Agent settings and configuration
│   │   ├── AgentConversation/    # Alchemist chat interface
│   │   ├── KnowledgeBase/        # Document management
│   │   ├── ApiIntegration/       # API and MCP server management
│   │   ├── AgentTesting/         # Testing interface with billing
│   │   ├── AgentDeployment/      # Cloud deployment management
│   │   ├── AgentAnalytics/       # Usage analytics and reporting
│   │   ├── AgentFineTuning/      # Conversational training
│   │   └── WhatsAppIntegration/  # WhatsApp Business setup
│   ├── shared/                   # Reusable UI components
│   │   ├── CommandPalette.js     # Global search (⌘K)
│   │   ├── StatusBadge.js        # Status indicators
│   │   ├── FileIcon.js           # File type icons
│   │   └── NotificationSystem.js # Enhanced notifications
│   └── Layout.js                 # Main app layout and navigation
├── pages/
│   ├── LandingPage.js           # Marketing landing page
│   ├── Dashboard.js             # Central hub with overview
│   ├── AgentsList.js            # Enhanced agent gallery
│   ├── AgentEditor.js           # Main agent editor
│   ├── IntegrationsHub.js       # Unified integrations management
│   ├── Login.js / Signup.js     # Authentication pages
│   └── ...
├── services/                    # Modular API services
│   ├── config/apiConfig.js      # Base configurations
│   ├── auth/authService.js      # Authentication management
│   ├── agents/agentService.js   # Agent CRUD operations
│   ├── conversations/           # Conversation and billing
│   ├── knowledgeBase/          # File uploads and search
│   ├── deployment/             # Cloud deployment
│   ├── tuning/                 # Fine-tuning services
│   └── whatsapp/               # WhatsApp integration
└── utils/
    ├── AuthContext.js          # Firebase auth context
    ├── CommandPaletteContext.js # Global search context
    └── agentEditorHelpers.js   # Utility functions
```

### Backend Integration

The frontend integrates with multiple backend services:

- **Alchemist Platform** - Core agent management and conversations
- **Universal Agent Service** - Deployed agent runtime and billing
- **Agent Tuning Service** - Fine-tuning and training data
- **WhatsApp Service** - WhatsApp Business API integration

## 🛠️ Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm run test` - Run test suite
- `npm run lint` - Run ESLint
- `npm run eject` - Eject from Create React App (not recommended)

### Key Development Features

- **Hot Reload** - Instant updates during development
- **Error Boundaries** - Graceful error handling
- **Debug Mode** - Enhanced logging and debugging tools
- **Component Isolation** - Each feature is self-contained

## 🚀 Deployment

### Google Cloud Run (Recommended)

This application is configured for Google Cloud Run deployment:

1. **Prerequisites:**
   ```bash
   # Install Google Cloud CLI
   gcloud auth login
   gcloud config set project your-project-id
   ```

2. **Deploy using Cloud Build:**
   ```bash
   gcloud builds submit
   ```
   
   This uses the included `cloudbuild.yaml` configuration.

3. **Manual deployment:**
   ```bash
   # Build and deploy in one command
   gcloud run deploy agent-studio-web \
     --source . \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated
   ```

### Docker Deployment

1. **Build Docker image:**
   ```bash
   docker build -t agent-studio .
   ```

2. **Run locally:**
   ```bash
   docker run -p 8080:8080 agent-studio
   ```

### Other Platforms

The application can also be deployed to:
- **Netlify** - Static hosting with edge functions
- **Vercel** - Serverless deployment
- **AWS Amplify** - Full-stack deployment
- **Azure Static Web Apps** - Microsoft cloud hosting

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `REACT_APP_FIREBASE_API_KEY` | Firebase API key | Yes |
| `REACT_APP_FIREBASE_PROJECT_ID` | Firebase project ID | Yes |
| `REACT_APP_API_BASE_URL` | Backend API URL | Yes |
| `REACT_APP_UNIVERSAL_AGENT_URL` | Deployed agent service URL | For production testing |
| `REACT_APP_WHATSAPP_SERVICE_URL` | WhatsApp service URL | For WhatsApp integration |

### Firebase Setup

1. **Create Firebase project** at [Firebase Console](https://console.firebase.google.com)

2. **Enable Authentication:**
   - Email/Password provider
   - Google provider (optional)

3. **Setup Firestore Database:**
   ```javascript
   // Security rules
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /alchemist_agents/{agentId} {
         allow read, write: if request.auth != null 
           && request.auth.uid == resource.data.userId;
       }
       // Add other collection rules as needed
     }
   }
   ```

## 📱 User Guide

### Getting Started

1. **Sign up** for an account or use Google sign-in
2. **Dashboard** - Your central hub for all agent activities
3. **Create Agent** - Use the visual builder to describe your agent
4. **Add Knowledge** - Upload documents for your agent to learn from
5. **Test Agent** - Chat with your agent and refine its responses
6. **Deploy** - One-click deployment to production
7. **Integrate** - Connect to WhatsApp, websites, or APIs

### Navigation

- **Dashboard (/)** - Overview of your agents and recent activity
- **My Agents (/agents)** - Browse and manage all your agents
- **Integrations Hub (/integrations-hub)** - Unified integration management
- **Command Palette (⌘K)** - Fast navigation and search

### Key Features

#### Agent Creation
- Natural language description
- Automatic capability detection
- Template-based quick start
- Advanced configuration options

#### Knowledge Management
- Drag & drop file uploads
- Semantic search capabilities
- Document preprocessing
- Knowledge base organization

#### Testing & Analytics
- Development mode (free testing)
- Production mode (billable usage)
- Real-time cost tracking
- Comprehensive analytics dashboard

#### Deployment
- One-click Cloud Run deployment
- Automatic scaling and monitoring
- Environment management
- Health checks and logging

#### WhatsApp Integration
- Business API webhook setup
- Message routing and responses
- Rich media support
- Analytics and monitoring

## 🧮 Billing System

### Development vs Production

- **Development Mode** - Free testing with full functionality
- **Production Mode** - Billable usage with real-time cost tracking

### Cost Calculation

Based on OpenAI GPT-4 pricing:
- **Prompt tokens**: $0.03 per 1,000 tokens
- **Completion tokens**: $0.06 per 1,000 tokens

### Analytics

- Token usage tracking
- Cost analysis and optimization
- Conversation history and audit trails
- Export functionality for billing reconciliation

## 🔌 Integrations

### WhatsApp Business

For users with existing WhatsApp Business API access:

1. **Deploy your agent** using the deployment manager
2. **Configure webhook** in WhatsApp Integration panel
3. **Update WhatsApp Business Platform** with webhook URL
4. **Test integration** by sending messages

Required information:
- Phone Number ID
- Access Token
- Verify Token (create any secure string)
- App Secret (optional, recommended for production)

### API Integration

- OpenAPI specification upload
- Automatic endpoint discovery
- MCP (Model Context Protocol) server deployment
- API testing and validation

### Website Integration

- Embeddable chat widgets
- Custom styling and branding
- Analytics and conversation tracking
- Lead capture and routing

## 🧪 Fine-tuning & Training

### Conversational Training

- Interactive training sessions
- Automatic query generation
- Response optimization
- Performance analytics

### Training Process

1. **Start training session** in Agent Editor
2. **Generate queries** based on agent context
3. **Provide responses** for training data
4. **Automatic training** triggers based on data thresholds
5. **Monitor improvements** through analytics

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Firebase configuration
   - Check API keys and permissions
   - Clear browser cache and cookies

2. **Deployment Failures**
   - Check Google Cloud permissions
   - Verify Docker configuration
   - Review Cloud Build logs

3. **Agent Not Responding**
   - Check deployment status
   - Verify knowledge base uploads
   - Review conversation logs

4. **WhatsApp Integration Issues**
   - Verify webhook URL accessibility
   - Check Verify Token matches
   - Ensure webhook subscription to "messages"

### Debug Mode

Enable enhanced logging:
```javascript
localStorage.setItem('DEBUG_MODE', 'true');
localStorage.setItem('DEBUG_BILLING', 'true');
```

### Support

For technical issues:
1. Check browser console for error messages
2. Review application logs and status
3. Verify all configuration values
4. Contact support with specific error details and agent IDs

## 🚀 Performance

### Optimization Features

- **Code splitting** - Load components on demand
- **Lazy loading** - Images and non-critical resources
- **Service worker** - Offline capabilities and caching
- **Tree shaking** - Eliminate unused code
- **Bundle optimization** - Minimized production builds

### Performance Monitoring

- Real-time performance metrics
- Error tracking and reporting
- User experience analytics
- API response time monitoring

## 🔒 Security

### Authentication

- Firebase Authentication with JWT tokens
- Secure API communication
- Session management and timeouts
- Multi-factor authentication support

### Data Protection

- Firestore security rules
- User data isolation
- Encrypted data transmission
- GDPR compliance ready

### API Security

- Bearer token authentication
- Request rate limiting
- Input validation and sanitization
- Error handling without information leakage

## 🧑‍💻 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install dependencies and setup environment
4. Make your changes with tests
5. Submit a pull request

### Code Standards

- ESLint configuration for consistent code style
- Component documentation with PropTypes
- Test coverage for critical functionality
- Semantic commit messages

### Architecture Principles

- **Component isolation** - Single responsibility principle
- **Service modularity** - Focused API services
- **Reusable utilities** - Shared helper functions
- **Progressive enhancement** - Graceful degradation

## 📈 Roadmap

### Near Term

- Enhanced analytics and reporting
- Advanced fine-tuning capabilities
- Multi-language support
- Team collaboration features

### Long Term

- Marketplace for agent templates
- Advanced workflow automation
- Enterprise security features
- Custom model support

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with React, Material-UI, and Firebase
- Powered by OpenAI GPT models
- Deployed on Google Cloud Platform
- Integrated with WhatsApp Business API

---

**Alchemist Agent Studio** - Transforming ideas into intelligent agents. Built with ❤️ for the AI community.