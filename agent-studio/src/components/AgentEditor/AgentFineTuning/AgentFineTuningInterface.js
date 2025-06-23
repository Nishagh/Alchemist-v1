/**
 * Agent Fine-tuning Interface
 * 
 * Wrapper component that loads the new conversational fine-tuning interface
 */
import React from 'react';
import ConversationalFineTuning from './ConversationalFineTuning';

const AgentFineTuningInterface = ({ 
  agentId, 
  onNotification, 
  disabled = false 
}) => {
  return (
    <ConversationalFineTuning
      agentId={agentId}
      onNotification={onNotification}
      disabled={disabled}
    />
  );
};

export default AgentFineTuningInterface;