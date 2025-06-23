const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 8080;

// Import Firebase Admin
const { auth, db } = require('./server/firebase-admin');
const { configureFirebaseAuth } = require('./server/auth-config');

// Import billing routes (now using CommonJS)
let billingRoutes = null;
let creditsRoutes = null;
let webhookRoutes = null;
let usageTrackingMiddleware = null;
let creditsMiddleware = null;

// Load modules
function loadModules() {
  try {
    // Enable payment modules
    console.log('Loading payment modules...');
    billingRoutes = require('./server/routes/billing');
    creditsRoutes = require('./server/routes/credits');
    webhookRoutes = require('./server/routes/webhooks');
    usageTrackingMiddleware = require('./server/middleware/usageTracking');
    creditsMiddleware = require('./server/middleware/creditsMiddleware');
    
    console.log('All modules loaded successfully including payment modules');
  } catch (error) {
    console.error('Error loading modules:', error);
    // Continue without billing if modules fail to load
    console.log('Continuing without payment modules due to error');
  }
}

// Initialize Firebase Authentication
configureFirebaseAuth().catch(error => {
  console.error('Failed to configure Firebase authentication:', error);
});

// Middleware for parsing JSON and urlencoded form data
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Middleware to verify Firebase ID token
const authenticateUser = async (req, res, next) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  const idToken = authHeader.split('Bearer ')[1];
  
  try {
    const decodedToken = await auth.verifyIdToken(idToken);
    req.user = decodedToken;
    next();
  } catch (error) {
    console.error('Error verifying auth token:', error);
    res.status(401).json({ error: 'Unauthorized' });
  }
};

// Middleware to validate user ID in requests
const validateUserId = (req, res, next) => {
  const authenticatedUserId = req.user.uid;
  
  // Check query parameters (GET, DELETE)
  const queryUserId = req.query.userId;
  if (queryUserId) {
    // Handle case where userId is an array (multiple userId parameters)
    if (Array.isArray(queryUserId)) {
      // Check if any of the provided userIds don't match the authenticated user
      const hasInvalidUserId = queryUserId.some(id => id !== authenticatedUserId);
      if (hasInvalidUserId) {
        console.log(`User ID mismatch: authenticated=${authenticatedUserId}, requested=${queryUserId}`);
        return res.status(403).json({ error: 'Access denied: User ID mismatch' });
      }
    } else if (queryUserId !== authenticatedUserId) {
      console.log(`User ID mismatch: authenticated=${authenticatedUserId}, requested=${queryUserId}`);
      return res.status(403).json({ error: 'Access denied: User ID mismatch' });
    }
  }
  
  // Check body (POST, PUT)
  const bodyUserId = req.body.userId;
  if (bodyUserId && bodyUserId !== authenticatedUserId) {
    console.log(`User ID mismatch in body: authenticated=${authenticatedUserId}, requested=${bodyUserId}`);
    return res.status(403).json({ error: 'Access denied: User ID mismatch' });
  }
  
  next();
};

// Helper function to verify agent ownership
const verifyAgentOwnership = async (agentId, userId) => {
  try {
    // Get the agent document
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    
    if (!agentDoc.exists) {
      return { 
        success: false, 
        status: 404, 
        error: 'Agent not found' 
      };
    }
    
    const agent = agentDoc.data();
    
    // Check if the user owns this agent
    if (agent.owner_id !== userId) {
      return { 
        success: false, 
        status: 403, 
        error: 'Access denied: You do not have permission to access this agent' 
      };
    }
    
    return { 
      success: true, 
      agent: { 
        agent_id: agentId, 
        ...agent 
      } 
    };
  } catch (error) {
    console.error('Error verifying agent ownership:', error);
    return { 
      success: false, 
      status: 500, 
      error: 'Server error while verifying ownership' 
    };
  }
};

// OPTIONS handler for CORS preflight
app.options('/api/health', (req, res) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Accept, Content-Type, Authorization');
  res.sendStatus(200);
});

app.options('/health', (req, res) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Accept, Content-Type, Authorization');
  res.sendStatus(200);
});

// API routes
app.get('/api/health', async (req, res) => {
  // Set CORS headers
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Accept, Content-Type, Authorization');
  
  try {
    // Check Firebase connection
    let firebase_healthy = true;
    try {
      await db.collection('test').limit(1).get();
    } catch (e) {
      firebase_healthy = false;
    }
    
    // Check Firebase Auth
    let auth_healthy = true;
    try {
      await auth.listUsers(1);
    } catch (e) {
      auth_healthy = false;
    }
    
    const health_status = {
      "service": "agent-studio",
      "status": "healthy",
      "timestamp": new Date().toISOString(),
      "version": "1.0.0",
      "components": {
        "firebase": {
          "status": firebase_healthy ? "healthy" : "unhealthy",
          "connected": firebase_healthy
        },
        "auth": {
          "status": auth_healthy ? "healthy" : "unhealthy",
          "configured": auth_healthy
        },
        "server": {
          "status": "healthy",
          "port": PORT
        }
      }
    };
    
    // Determine overall status
    if (!firebase_healthy || !auth_healthy) {
      health_status.status = "degraded";
    }
    
    res.status(200).json(health_status);
  } catch (error) {
    console.error('Health check failed:', error);
    res.status(503).json({
      "service": "agent-studio",
      "status": "unhealthy",
      "timestamp": new Date().toISOString(),
      "error": error.message
    });
  }
});

// Legacy health endpoint
app.get('/health', async (req, res) => {
  // Set CORS headers
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Accept, Content-Type, Authorization');
  
  try {
    // Check Firebase connection
    let firebase_healthy = true;
    try {
      await db.collection('test').limit(1).get();
    } catch (e) {
      firebase_healthy = false;
    }
    
    const health_status = {
      "service": "agent-studio",
      "status": firebase_healthy ? "healthy" : "degraded",
      "timestamp": new Date().toISOString(),
      "version": "1.0.0"
    };
    
    res.status(200).json(health_status);
  } catch (error) {
    res.status(503).json({
      "service": "agent-studio",
      "status": "unhealthy",
      "timestamp": new Date().toISOString(),
      "error": error.message
    });
  }
});

// Protected API routes
app.get('/api/user/profile', authenticateUser, (req, res) => {
  res.status(200).json({ user: req.user });
});

// Auth-related API endpoints
app.post('/api/auth/google-signin', async (req, res) => {
  try {
    const { idToken } = req.body;
    
    if (!idToken) {
      return res.status(400).json({ error: 'ID token is required' });
    }
    
    // Verify the ID token
    const decodedToken = await auth.verifyIdToken(idToken);
    
    // Create a custom token for the client
    const customToken = await auth.createCustomToken(decodedToken.uid);
    
    res.status(200).json({ token: customToken });
  } catch (error) {
    console.error('Error processing Google sign-in:', error);
    res.status(500).json({ error: 'Authentication failed' });
  }
});

// =========== AGENT API ROUTES =============

// Get all agents for the authenticated user
app.get('/api/agents', authenticateUser, validateUserId, async (req, res) => {
  try {
    // Get user ID from authenticated request
    const userId = req.user.uid;
    
    // Query agents owned by this user
    // In a real implementation, this would query your database
    // This is a simplified example using Firestore
    const agentsSnapshot = await db.collection('alchemist_agents')
      .where('user_id', '==', userId)
      .get();
    
    const agents = [];
    agentsSnapshot.forEach(doc => {
      agents.push({
        agent_id: doc.id,
        ...doc.data()
      });
    });
    
    res.status(200).json({ agents });
  } catch (error) {
    console.error('Error fetching agents:', error);
    res.status(500).json({ error: 'Failed to fetch agents' });
  }
});

// Get a specific agent, ensuring the user owns it
app.get('/api/agents/:agentId', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    
    // Use the helper function to verify ownership
    const verificationResult = await verifyAgentOwnership(agentId, userId);
    
    if (!verificationResult.success) {
      return res.status(verificationResult.status).json({ error: verificationResult.error });
    }
    
    // If verification succeeded, return the agent
    res.status(200).json({ agent: verificationResult.agent });
  } catch (error) {
    console.error('Error fetching agent:', error);
    res.status(500).json({ error: 'Failed to fetch agent' });
  }
});

// Create a new agent
app.post('/api/agents', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentData = req.body;
    
    // Ensure the owner_id is set to the authenticated user
    agentData.owner_id = userId;
    agentData.created_at = new Date().toISOString();
    
    // Create the agent document
    const agentRef = await db.collection('alchemist_agents').add(agentData);
    
    res.status(201).json({ 
      agent_id: agentRef.id,
      ...agentData
    });
  } catch (error) {
    console.error('Error creating agent:', error);
    res.status(500).json({ error: 'Failed to create agent' });
  }
});

// Update an agent
app.put('/api/agents/:agentId', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    const updates = req.body;
    
    // Get the agent document
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    
    if (!agentDoc.exists) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentDoc.data();
    
    // Check if the user owns this agent
    if (agent.owner_id !== userId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    // Update the agent document
    // Never allow owner_id to be changed
    delete updates.owner_id;
    updates.updated_at = new Date().toISOString();
    
    await db.collection('alchemist_agents').doc(agentId).update(updates);
    
    res.status(200).json({ 
      agent_id: agentId,
      ...agent,
      ...updates
    });
  } catch (error) {
    console.error('Error updating agent:', error);
    res.status(500).json({ error: 'Failed to update agent' });
  }
});

// Delete an agent
app.delete('/api/agents/:agentId', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    
    // Get the agent document
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    
    if (!agentDoc.exists) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentDoc.data();
    
    // Check if the user owns this agent
    if (agent.owner_id !== userId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    // Delete the agent
    await db.collection('alchemist_agents').doc(agentId).delete();
    
    res.status(200).json({ message: 'Agent deleted successfully' });
  } catch (error) {
    console.error('Error deleting agent:', error);
    res.status(500).json({ error: 'Failed to delete agent' });
  }
});

// =========== AGENT KNOWLEDGE BASE ROUTES =============

// Get knowledge base files for an agent
app.get('/api/agents/:agentId/knowledge', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    
    // Verify the user owns this agent
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    if (!agentDoc.exists) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentDoc.data();
    if (agent.owner_id !== userId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    // Get knowledge base files
    const files = agent.knowledge_base || [];
    
    res.status(200).json({ files });
  } catch (error) {
    console.error('Error fetching knowledge base:', error);
    res.status(500).json({ error: 'Failed to fetch knowledge base' });
  }
});

// Upload file to knowledge base
app.post('/api/agents/:agentId/knowledge', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    
    // Verify the user owns this agent
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    if (!agentDoc.exists) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentDoc.data();
    if (agent.owner_id !== userId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    // Process file upload logic here
    // ...
    
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error uploading to knowledge base:', error);
    res.status(500).json({ error: 'Failed to upload file' });
  }
});

// Delete file from knowledge base
app.delete('/api/agents/:agentId/knowledge/:fileId', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const { agentId, fileId } = req.params;
    
    // Verify the user owns this agent
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    if (!agentDoc.exists) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentDoc.data();
    if (agent.owner_id !== userId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    // Delete file logic here
    // ...
    
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error deleting from knowledge base:', error);
    res.status(500).json({ error: 'Failed to delete file' });
  }
});

// =========== AGENT CONVERSATION ROUTES =============

// Get conversations for an agent
app.get('/api/agents/:agentId/conversations', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    
    // Verify the user owns this agent
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    if (!agentDoc.exists) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentDoc.data();
    if (agent.owner_id !== userId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    // Get conversations logic here
    // ...
    
    res.status(200).json({ conversations: [] });
  } catch (error) {
    console.error('Error fetching conversations:', error);
    res.status(500).json({ error: 'Failed to fetch conversations' });
  }
});

// Execute action on an agent
app.post('/api/agents/:agentId/action', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    const { action, payload } = req.body;
    
    // Verify the user owns this agent
    const agentDoc = await db.collection('alchemist_agents').doc(agentId).get();
    if (!agentDoc.exists) {
      return res.status(404).json({ error: 'Agent not found' });
    }
    
    const agent = agentDoc.data();
    if (agent.owner_id !== userId) {
      return res.status(403).json({ error: 'Access denied' });
    }
    
    // Execute action logic here
    // ...
    
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error executing agent action:', error);
    res.status(500).json({ error: 'Failed to execute action' });
  }
});

// =========== USER AGENT ROUTES =============

// Execute action on user agent
app.post('/api/user-agents/:agentId/action', authenticateUser, validateUserId, async (req, res) => {
  try {
    const userId = req.user.uid;
    const agentId = req.params.agentId;
    const { action, payload } = req.body;
    
    // User agents might have different permissions, implement your logic here
    // ...
    
    res.status(200).json({ success: true });
  } catch (error) {
    console.error('Error executing user agent action:', error);
    res.status(500).json({ error: 'Failed to execute action' });
  }
});

// =========== ALCHEMIST AGENT ROUTES =============

// Interact with Alchemist agent
app.post('/api/alchemist/interact', authenticateUser, validateUserId, async (req, res, next) => {
  // Apply credits middleware if available
  if (creditsMiddleware) {
    await creditsMiddleware.checkCreditsBeforeUsage(req, res, () => {
      creditsMiddleware.deductCreditsAfterUsage(req, res, next);
    });
  } else {
    next();
  }
}, async (req, res) => {
  try {
    const userId = req.user.uid;
    const { message, agent_id, create_agent, agent_requirement } = req.body;
    
    // If agent_id is provided, verify ownership
    if (agent_id) {
      const agentDoc = await db.collection('alchemist_agents').doc(agent_id).get();
      if (agentDoc.exists) {
        const agent = agentDoc.data();
        if (agent.owner_id !== userId) {
          return res.status(403).json({ error: 'Access denied' });
        }
      } else if (!create_agent) {
        // If agent doesn't exist and we're not creating a new one, return 404
        return res.status(404).json({ error: 'Agent not found' });
      }
    }
    
    // Process interaction logic here
    // ...
    
    res.status(200).json({ response: "This is a placeholder response" });
  } catch (error) {
    console.error('Error interacting with Alchemist:', error);
    res.status(500).json({ error: 'Failed to process interaction' });
  }
});

// =========== WEBHOOK ROUTES =============

// Webhook routes (no authentication required)
app.use('/webhooks', async (req, res, next) => {
  if (webhookRoutes) {
    webhookRoutes(req, res, next);
  } else {
    res.status(503).json({ error: 'Webhook service not available' });
  }
});

// =========== CREDITS API ROUTES =============

// Use credits routes if available (primary billing system)
app.use('/api/credits', authenticateUser, validateUserId, async (req, res, next) => {
  if (creditsRoutes) {
    creditsRoutes(req, res, next);
  } else {
    res.status(503).json({ error: 'Credits service not available' });
  }
});

// =========== BILLING API ROUTES =============

// Use billing routes if available (legacy postpaid system)
app.use('/api/billing', authenticateUser, validateUserId, async (req, res, next) => {
  if (billingRoutes) {
    billingRoutes(req, res, next);
  } else {
    res.status(503).json({ error: 'Billing service not available' });
  }
});

// Serve static files from the build directory
app.use(express.static(path.join(__dirname, 'build')));

// Handle SPA routing by redirecting all remaining requests to index.html
app.get('/*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  
  // Load modules after server starts
  loadModules();
}); 