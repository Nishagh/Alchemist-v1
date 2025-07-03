// Dashboard JavaScript

// Global state
let activityLog = [];
let agents = [];
let currentAgent = null;

// Agent action mappings - which actions are available for each agent type
const agentActions = {
    'requirements': ['analyze', 'update', 'get'],
    'prompt_engineer': ['create', 'update', 'get', 'validate', 'list_versions'],
    'knowledge_engineer': ['ingest', 'query', 'update', 'get', 'analyze'],
    'function_developer': ['create', 'update', 'get', 'list', 'validate', 'implement'],
    'testing': ['create_test', 'run_test', 'get_test', 'list_tests', 'analyze_results', 'generate_tests'],
    'orchestrator': ['process', 'delegate', 'get_status']
};

// Sample payloads for each action type
const samplePayloads = {
    'analyze': {
        'purpose': 'Create a customer support agent for my e-commerce store',
        'target_audience': 'Online shoppers with questions',
        'key_functionalities': ['Answer product questions', 'Process returns', 'Track orders'],
        'integration_requirements': ['Shopify'],
        'constraints': ['Must support English and Spanish']
    },
    'design': {},
    'create': {
        'requirements': {},
        'additional_instructions': 'Create a helpful, friendly tone'
    },
    'ingest': {
        'name': 'Document Name',
        'type': 'text',
        'content': 'Document content goes here...',
        'metadata': {'source': 'manual', 'language': 'en'}
    },
    'create_test': {
        'name': 'basic_functionality_test',
        'description': 'Test basic agent functionality',
        'input_data': {'query': 'What are your capabilities?'},
        'tags': ['basic', 'functionality']
    },
    'process': {
        'message': 'Process this request',
        'context': {'agent_id': 'test_agent'}
    }
};

// Initialize the dashboard
// Dashboard CSS for thought process display
const style = document.createElement('style');
style.textContent = `
.thought-process {
    background-color: #f8f9fa;
    border-left: 4px solid #6c757d;
    padding: 0.5rem;
    font-size: 0.9rem;
    max-height: 300px;
    overflow-y: auto;
}

.final-answer {
    background-color: #e9f0ff;
    border-left: 4px solid #007bff;
    padding: 0.5rem;
    border-radius: 0.25rem;
}

.user-message {
    background-color: #f0f7ff;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-right: 2rem;
}

.agent-message {
    background-color: #f7f7f7;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-left: 2rem;
}
`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    refreshDashboard();
    
    // Update connection status
    
    // Set up event listeners with null checks
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', refreshDashboard);
    
    const createAgentBtn = document.getElementById('create-agent-btn');
    if (createAgentBtn) createAgentBtn.addEventListener('click', createAgent);
    
    const executeActionBtn = document.getElementById('execute-action-btn');
    if (executeActionBtn) executeActionBtn.addEventListener('click', executeAgentAction);
    
    const deleteAgentBtn = document.getElementById('delete-agent-btn');
    if (deleteAgentBtn) deleteAgentBtn.addEventListener('click', deleteCurrentAgent);
    
    // Action type selection changes the sample payload
    const actionType = document.getElementById('action-type');
    if (actionType) actionType.addEventListener('change', updateActionPayload);
    
    // Set up conversation interface event listeners
    const sendInstructionBtn = document.getElementById('send-instruction-btn');
    if (sendInstructionBtn) sendInstructionBtn.addEventListener('click', sendInstruction);
    
    const instructionInput = document.getElementById('instruction-input');
    if (instructionInput) {
        instructionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendInstruction();
            }
        });
    }
    
    // Quick create agent from sidebar
    document.querySelectorAll('#specialized-agents-menu a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const agentType = e.target.closest('a').dataset.agentType;
            if (agentType) {
                // Set a relevant purpose based on agent type
                const agentPurpose = document.getElementById('agent-purpose');
                const agentDescription = document.getElementById('agent-description');
                
                // Set suggested purpose and description based on specialized agent type
                switch(agentType) {
                    case 'requirements':
                        agentPurpose.value = 'Requirements Analysis Assistant';
                        agentDescription.value = 'An agent that can help gather and analyze project requirements.';
                        break;
                    case 'prompt_engineer':
                        agentPurpose.value = 'Prompt Engineering Assistant';
                        agentDescription.value = 'An agent that can help create and refine AI prompts for optimal results.';
                        break;
                    case 'knowledge_engineer':
                        agentPurpose.value = 'Knowledge Base Assistant';
                        agentDescription.value = 'An agent that can help organize and structure knowledge for your system.';
                        break;
                    case 'function_developer':
                        agentPurpose.value = 'Development Assistant';
                        agentDescription.value = 'An agent that can help with programming tasks and function development.';
                        break;
                    case 'testing':
                        agentPurpose.value = 'Testing Assistant';
                        agentDescription.value = 'An agent that can help create and run tests for your system.';
                        break;
                    default:
                        agentPurpose.value = '';
                        agentDescription.value = '';
                }
                
                // Show the create agent modal
                new bootstrap.Modal(document.getElementById('createAgentModal')).show();
            }
        });
    });
});

function pollForUpdates() {
    // Only poll if needed
    if (currentAgent) {
        // Poll for agent updates
        fetch(`/api/agents/${currentAgent.id}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Handle any updates
                    if (data.updates) {
                        // Process updates
                    }
                }
            })
            .catch(error => {
                console.error('Error polling for updates:', error);
            });
    }
}

// Update the agent types chart
function updateAgentTypesChart() {
    try {
        const chartContainer = document.getElementById('agent-types-chart');
        if (!chartContainer) {
            console.warn('Agent types chart container not found');
            return;
        }
        
        // Ensure the chart container is ready
        if (chartContainer.offsetWidth === 0 && chartContainer.offsetHeight === 0) {
            console.log('Chart container not visible yet, delaying chart creation');
            setTimeout(updateAgentTypesChart, 300); // Retry after a delay
            return;
        }
        
        // Count agents by type
        const agentTypeCount = {};
        agents.forEach(agent => {
            const type = agent.type || 'unknown';
            agentTypeCount[type] = (agentTypeCount[type] || 0) + 1;
        });
        
        // If there are no agents yet, add a placeholder
        if (Object.keys(agentTypeCount).length === 0) {
            agentTypeCount['No Agents'] = 1;
        }
        
        // Prepare chart data
        const labels = Object.keys(agentTypeCount);
        const data = Object.values(agentTypeCount);
        const backgroundColors = [
            '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', 
            '#5a5c69', '#858796', '#6f42c1', '#20c9a6', '#f8f9fc'
        ];
        
        // Clear previous chart if exists
        if (window.agentTypesChart) {
            window.agentTypesChart.destroy();
        }
        
        // Create new chart
        window.agentTypesChart = new Chart(chartContainer.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors.slice(0, data.length),
                    hoverBackgroundColor: backgroundColors.slice(0, data.length),
                    hoverBorderColor: 'rgba(234, 236, 244, 1)',
                }],
            },
            options: {
                maintainAspectRatio: false,
                tooltips: {
                    backgroundColor: 'rgb(255,255,255)',
                    bodyFontColor: '#858796',
                    borderColor: '#dddfeb',
                    borderWidth: 1,
                    xPadding: 15,
                    yPadding: 15,
                    displayColors: false,
                    caretPadding: 10,
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                cutoutPercentage: 70,
            },
        });
    } catch (e) {
        console.error('Failed to create chart:', e.message);
    }
}

// Refresh the dashboard data
function refreshDashboard() {
    // Fetch agents
    fetch('/api/agents')
        .then(response => response.json())
        .then(data => {
            // Handle various API response formats
            if (data.status === 'success' && data.agents) {
                agents = data.agents;
                updateAgentCards();
                updateAgentTypesChart(); // Update the chart
                const agentCountElement = document.getElementById('active-agents-count');
                if (agentCountElement) agentCountElement.textContent = agents.length;
            } else if (Array.isArray(data.agents)) {
                // Handle array format
                agents = data.agents;
                updateAgentCards();
                updateAgentTypesChart(); // Update the chart
                const agentCountElement = document.getElementById('active-agents-count');
                if (agentCountElement) agentCountElement.textContent = agents.length;
            } else if (Array.isArray(data)) {
                // Handle direct array format
                agents = data;
                updateAgentCards();
                updateAgentTypesChart(); // Update the chart
                const agentCountElement = document.getElementById('active-agents-count');
                if (agentCountElement) agentCountElement.textContent = agents.length;
            } else {
                console.error('Invalid API response structure:', data);
                agents = [];
                updateAgentCards();
                updateAgentTypesChart(); // Update the chart with empty data
                const agentCountElement = document.getElementById('active-agents-count');
                if (agentCountElement) agentCountElement.textContent = '0';
            }
        })
        .catch(error => {
            console.error('Error fetching agents:', error);
            showError('Failed to fetch agents');
        });
}

// Update agent cards in the dashboard
function updateAgentCards() {
    const agentCardsContainer = document.getElementById('agent-cards');
    if (!agentCardsContainer) {
        console.warn('Agent cards container not found');
        return;
    }
    
    agentCardsContainer.innerHTML = '';
    
    if (!agents || agents.length === 0) {
        agentCardsContainer.innerHTML = '<div class="col-12"><div class="alert alert-info">No agents found. Create a new agent to get started.</div></div>';
        return;
    }
    
    agents.forEach(agent => {
        const card = document.createElement('div');
        card.className = 'col-md-4 mb-4';
        card.innerHTML = `
            <div class="card agent-card" data-agent-id="${agent.id}">
                <div class="card-body">
                    <h5 class="card-title">${agent.type}</h5>
                    <h6 class="card-subtitle mb-2 text-muted">${agent.id}</h6>
                    <p class="card-text">Agent ready for tasks</p>
                    <button class="btn btn-sm btn-primary view-agent-btn">View Details</button>
                </div>
            </div>
        `;
        
        // Add click handler
        card.querySelector('.view-agent-btn').addEventListener('click', () => {
            showAgentDetails(agent.id);
        });
        
        agentCardsContainer.appendChild(card);
    });
}

// Add new activity to the log
function addActivity(activity) {
    // Add to the beginning of the array
    activityLog.unshift(activity);
    
    // Keep only the last 20 activities
    if (activityLog.length > 20) {
        activityLog.pop();
    }
    
    // Update the activity log table
    updateActivityLog();
}

// Update the activity log table
function updateActivityLog() {
    const activityLogTable = document.getElementById('activity-log');
    activityLogTable.innerHTML = '';
    
    if (activityLog.length === 0) {
        activityLogTable.innerHTML = '<tr><td colspan="4" class="text-center">No activity recorded yet</td></tr>';
        return;
    }
    
    activityLog.forEach(activity => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatTime(activity.time)}</td>
            <td>${activity.agent}</td>
            <td>${activity.action}</td>
            <td><span class="badge ${getStatusBadgeClass(activity.status)}">${activity.status}</span></td>
        `;
        
        // Add click handler
        row.addEventListener('click', () => {
            showAgentDetails(activity.agent);
        });
        
        activityLogTable.appendChild(row);
    });
}

// Format time for display
function formatTime(time) {
    if (typeof time === 'string') {
        time = new Date(time);
    }
    return time.toLocaleTimeString();
}

// Get the appropriate badge class for a status
function getStatusBadgeClass(status) {
    switch (status.toLowerCase()) {
        case 'success':
            return 'bg-success';
        case 'error':
            return 'bg-danger';
        case 'warning':
            return 'bg-warning text-dark';
        case 'in progress':
        case 'in_progress':
            return 'bg-info text-dark';
        default:
            return 'bg-secondary';
    }
}

function createAgent() {
    const agentId = document.getElementById('agent-id').value.trim() || null;
    const agentPurpose = document.getElementById('agent-purpose').value.trim();
    const agentDescription = document.getElementById('agent-description').value.trim();
    let agentConfig = {};
    
    try {
        const configText = document.getElementById('agent-config').value.trim();
        if (configText) {
            agentConfig = JSON.parse(configText);
        }
        
        // Add the purpose and description to the config
        agentConfig.purpose = agentPurpose;
        agentConfig.description = agentDescription;
        
    } catch (error) {
        showError('Invalid JSON in agent configuration');
        return;
    }
    
    // Validate required inputs
    if (!agentPurpose) {
        showError('Agent purpose is required');
        return;
    }
    
    if (!agentDescription) {
        showError('Agent description is required');
        return;
    }
    
    // Use our new GenericAgent which is designed for custom configuration
    const actualAgentType = 'generic';
    
    // Create the agent
    fetch('/api/agents', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            agent_type: actualAgentType,  // Always use orchestrator
            agent_id: agentId,
            config: {
                ...agentConfig,
                purpose: agentPurpose,
                description: agentDescription
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Close the modal
            bootstrap.Modal.getInstance(document.getElementById('createAgentModal')).hide();
            
            // Show success message
            showSuccess(`Custom agent '${agentPurpose}' created successfully`);
            
            // Add to activity log
            addActivity({
                time: new Date(),
                agent: data.agent_id,
                action: 'create_custom_agent',
                status: 'success'
            });
            
            // Refresh the dashboard
            refreshDashboard();
        } else {
            showError(data.message || 'Failed to create agent');
        }
    })
    .catch(error => {
        console.error('Error creating agent:', error);
        showError('Failed to create agent');
    });
}

// Initialize default configuration
function initializeDefaultConfig() {
    const configField = document.getElementById('agent-config');
    const agentPurpose = document.getElementById('agent-purpose');
    const agentDescription = document.getElementById('agent-description');
    
    // Set a default empty config
    configField.value = '{}';
    
    // Reset purpose and description if needed
    if (!agentPurpose.value) {
        agentPurpose.placeholder = 'e.g., Customer Support Assistant, Code Reviewer, Data Analyst';
    }
    
    if (!agentDescription.value) {
        agentDescription.placeholder = 'Describe what you want this agent to do...';
    }
}
// Update action payload when action type changes
function updateActionPayload() {
    const actionType = document.getElementById('action-type').value;
    const payloadField = document.getElementById('action-payload');
    
    // Provide a sample payload based on action type
    if (actionType && samplePayloads[actionType]) {
        payloadField.value = JSON.stringify(samplePayloads[actionType], null, 2);
    } else {
        payloadField.value = '{}';
    }
}

// Execute an action on the current agent
function executeAgentAction() {
    const actionType = document.getElementById('action-type').value;
    let payload = {};
    
    try {
        const payloadText = document.getElementById('action-payload').value;
        if (payloadText.trim()) {
            payload = JSON.parse(payloadText);
        }
    } catch (error) {
        showError('Invalid JSON in payload');
        return;
    }
    
    // Validate inputs
    if (!actionType) {
        showError('Action type is required');
        return;
    }
    
    if (!currentAgent) {
        showError('No agent selected');
        return;
    }
    
    // Update result display
    document.getElementById('action-result').textContent = 'Executing action...';
    
    // Execute the action
    fetch(`/api/agents/${currentAgent}/action`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            agent_id: currentAgent,
            action: actionType,
            payload: payload
        })
    })
    .then(response => response.json())
    .then(data => {
        // Display the result
        document.getElementById('action-result').textContent = JSON.stringify(data, null, 2);
        
        // Add to activity log
        addActivity({
            time: new Date(),
            agent: currentAgent,
            action: actionType,
            status: data.status || 'unknown'
        });
        
        // Show appropriate message
        if (data.status === 'success') {
            showSuccess(`Action ${actionType} executed successfully`);
        } else if (data.status === 'error') {
            showError(data.message || 'Action failed');
        }
        
        // Refresh the agent details
        showAgentDetails(currentAgent);
    })
    .catch(error => {
        console.error('Error executing action:', error);
        showError('Failed to execute action');
        document.getElementById('action-result').textContent = 'Error executing action';
    });
}

// Delete the current agent
function deleteCurrentAgent() {
    if (!currentAgent) {
        showError('No agent selected');
        return;
    }
    
    // Confirm deletion
    if (!confirm(`Are you sure you want to delete agent ${currentAgent}?`)) {
        return;
    }
    
    // Delete the agent
    fetch(`/api/agents/${currentAgent}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Close the modal
            bootstrap.Modal.getInstance(document.getElementById('agentDetailsModal')).hide();
            
            // Show success message
            showSuccess(`Agent ${currentAgent} deleted successfully`);
            
            // Refresh the dashboard
            refreshDashboard();
        } else {
            showError(data.message || 'Failed to delete agent');
        }
    })
    .catch(error => {
        console.error('Error deleting agent:', error);
        showError('Failed to delete agent');
    });
}

// Show an error message
function showError(message) {
    // You can implement a toast or alert system here
    alert('Error: ' + message);
}

// Show a success message
function showSuccess(message) {
    // You can implement a toast or alert system here
    alert('Success: ' + message);
}

// ---------- Conversation Interface Functions ----------

// Send an instruction to the system
function sendInstruction() {
    const instructionInput = document.getElementById('instruction-input');
    const instruction = instructionInput.value.trim();
    
    if (!instruction) return;
    
    // Add user message to conversation
    addMessageToConversation('user', instruction);
    
    // Clear input
    instructionInput.value = '';
    
    // Add thinking indicator
    const thinkingId = 'thinking-' + Date.now();
    addSystemThinkingMessage(thinkingId);
    
    // Process instruction
    processInstruction(instruction, thinkingId);
}

// Process the user instruction
function processInstruction(instruction, thinkingId) {
    // Create payload for natural language processing
    const payload = {
        instruction: instruction,
        context: {
            current_agents: agents.map(agent => ({ 
                id: agent.id, 
                type: agent.type 
            }))
        }
    };
    
    // Send to server for processing
    fetch('/api/process-instruction', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        // Remove thinking message
        removeThinkingMessage(thinkingId);
        
        // Handle the response
        if (data.status === 'success') {
            // Add system response
            addMessageToConversation('system', data.response);
            
            // If there's an action, execute it
            if (data.action) {
                executeInstructionAction(data.action);
            }
        } else {
            // Add error message
            addMessageToConversation('system', 
                'I\'m sorry, I had trouble understanding that. Could you rephrase your instruction?');
            console.error('Error processing instruction:', data.message);
        }
    })
    .catch(error => {
        console.error('Error processing instruction:', error);
        removeThinkingMessage(thinkingId);
        addMessageToConversation('system', 
            'Sorry, there was an error processing your request. Please try again.');
    });
}

// Execute an action based on instruction analysis
function executeInstructionAction(action) {
    switch(action.type) {
        case 'create_agent':
            createAgentFromInstruction(action.data);
            break;
        case 'modify_agent':
            modifyAgentFromInstruction(action.data);
            break;
        case 'execute_action':
            executeAgentActionFromInstruction(action.data);
            break;
        default:
            console.warn('Unknown action type:', action.type);
    }
    
    // Refresh dashboard after action
    setTimeout(refreshDashboard, 1000);
}

// Create an agent based on instruction
function createAgentFromInstruction(data) {
    // Form the agent creation request
    const agentData = {
        agent_type: data.agent_type,
        agent_id: data.agent_id,
        config: data.config || {}
    };
    
    // Send creation request
    fetch('/api/agents', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(agentData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addMessageToConversation('system', 
                `I've created the ${agentData.agent_type} agent with ID: ${data.agent_id}`);
        } else {
            addMessageToConversation('system', 
                `I couldn't create the agent: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error creating agent:', error);
        addMessageToConversation('system', 
            'There was an error creating the agent. Please try again.');
    });
}

// Modify an agent based on instruction
function modifyAgentFromInstruction(data) {
    // Form the agent action request
    const actionRequest = {
        agent_id: data.agent_id,
        action: data.action,
        payload: data.payload || {}
    };
    
    // Send modification request
    fetch(`/api/agents/${data.agent_id}/action`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(actionRequest)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addMessageToConversation('system', 
                `The agent has been updated successfully.`);
        } else {
            addMessageToConversation('system', 
                `I couldn't modify the agent: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error modifying agent:', error);
        addMessageToConversation('system', 
            'There was an error modifying the agent. Please try again.');
    });
}

// Execute an agent action based on instruction
function executeAgentActionFromInstruction(data) {
    // Form the agent action request
    const actionRequest = {
        agent_id: data.agent_id,
        action: data.action,
        payload: data.payload || {}
    };
    
    // Execute the action
    fetch(`/api/agents/${data.agent_id}/action`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(actionRequest)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            addMessageToConversation('system', 
                `The action has been executed successfully. Here's the result:\n\n${JSON.stringify(data.result, null, 2)}`);
        } else {
            addMessageToConversation('system', 
                `I couldn't execute the action: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error executing action:', error);
        addMessageToConversation('system', 
            'There was an error executing the action. Please try again.');
    });
}

// Add a message to the conversation container
function addMessageToConversation(sender, message) {
    const conversationContainer = document.getElementById('conversation-container');
    
    // If the container is empty, clear the placeholder
    if (conversationContainer.querySelector('.text-center.text-muted')) {
        conversationContainer.innerHTML = '';
    }
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = sender === 'user' ? 'user-message my-2' : 'agent-message my-2';
    
    // Add appropriate icon
    const iconEl = document.createElement('div');
    iconEl.className = 'small text-muted mb-1';
    iconEl.innerHTML = sender === 'user' 
        ? '<i class="bi bi-person-circle"></i> You' 
        : '<i class="bi bi-robot"></i> Alchemist';
    
    // Add message content
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.innerHTML = formatMessageContent(message);
    
    // Assemble message
    messageEl.appendChild(iconEl);
    messageEl.appendChild(contentEl);
    
    // Add to container
    conversationContainer.appendChild(messageEl);
    
    // Scroll to bottom
    conversationContainer.scrollTop = conversationContainer.scrollHeight;
}

// Add a system thinking message
function addSystemThinkingMessage(id) {
    const conversationContainer = document.getElementById('conversation-container');
    
    // If the container is empty, clear the placeholder
    if (conversationContainer.querySelector('.text-center.text-muted')) {
        conversationContainer.innerHTML = '';
    }
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = 'agent-message my-2';
    messageEl.id = id;
    
    // Add appropriate icon
    const iconEl = document.createElement('div');
    iconEl.className = 'small text-muted mb-1';
    iconEl.innerHTML = '<i class="bi bi-robot"></i> Alchemist';
    
    // Add thinking indicator
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';
    contentEl.innerHTML = `
        <div class="d-flex align-items-center">
            <span class="me-2">Thinking</span>
            <div class="spinner-grow spinner-grow-sm text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    // Assemble message
    messageEl.appendChild(iconEl);
    messageEl.appendChild(contentEl);
    
    // Add to container
    conversationContainer.appendChild(messageEl);
    
    // Scroll to bottom
    conversationContainer.scrollTop = conversationContainer.scrollHeight;
}

// Remove thinking message
function removeThinkingMessage(id) {
    const thinkingMessage = document.getElementById(id);
    if (thinkingMessage) {
        thinkingMessage.remove();
    }
}

// Format message content with markdown-like syntax
function formatMessageContent(message) {
    // Convert newlines to <br>
    message = message.replace(/\n/g, '<br>');
    
    // Convert code blocks
    message = message.replace(/```(.*?)```/gs, '<pre class="bg-light p-2 rounded"><code>$1</code></pre>');
    
    // Convert inline code
    message = message.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    return message;
}
