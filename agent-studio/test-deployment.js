/**
 * Test script to create sample deployment data for testing Dashboard functionality
 * Run this in browser console after authentication
 */

async function createTestDeployment(agentId, status = 'completed') {
  const db = firebase.firestore();
  
  const deploymentData = {
    agent_id: agentId,
    status: status,
    deployed_url: `https://agent-${agentId}.alchemist.com`,
    created_at: firebase.firestore.FieldValue.serverTimestamp(),
    updated_at: firebase.firestore.FieldValue.serverTimestamp(),
    deployment_config: {
      platform: 'cloud_run',
      region: 'us-central1'
    }
  };
  
  try {
    const docRef = await db.collection('agent_deployments').add(deploymentData);
    console.log('Test deployment created:', docRef.id, deploymentData);
    return docRef.id;
  } catch (error) {
    console.error('Error creating test deployment:', error);
    throw error;
  }
}

async function createTestAgent(userId) {
  const db = firebase.firestore();
  
  const agentData = {
    userId: userId,
    name: 'Test Agent ' + Date.now(),
    description: 'Test agent for deployment testing',
    created_at: firebase.firestore.FieldValue.serverTimestamp(),
    updated_at: firebase.firestore.FieldValue.serverTimestamp(),
    status: 'active'
  };
  
  try {
    const docRef = await db.collection('alchemist_agents').add(agentData);
    console.log('Test agent created:', docRef.id, agentData);
    return docRef.id;
  } catch (error) {
    console.error('Error creating test agent:', error);
    throw error;
  }
}

// Example usage:
// 1. Get current user ID
// const userId = firebase.auth().currentUser.uid;
// 
// 2. Create test agent and deployment
// createTestAgent(userId).then(agentId => {
//   return createTestDeployment(agentId, 'completed');
// }).then(deploymentId => {
//   console.log('Test setup complete! Deployment ID:', deploymentId);
// });

console.log('Test functions loaded. Use createTestAgent() and createTestDeployment() to create test data.');