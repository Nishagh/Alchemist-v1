/**
 * useAgentState Hook
 * 
 * Custom hook for managing agent state and related operations
 */
import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../utils/AuthContext';
import { onSnapshot, doc } from 'firebase/firestore';
import { db } from '../utils/firebase';

export const useAgentState = () => {
  const { agentId } = useParams();
  const { currentUser } = useAuth();
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const unsubscribeRef = useRef(null);

  // Load agent data from Firestore
  useEffect(() => {
    if (!currentUser || !agentId) {
      setLoading(false);
      return;
    }

    console.log(`Setting up Firestore listener for agent ${agentId}`);
    setLoading(true);
    setError('');

    try {
      const agentRef = doc(db, 'agents', agentId);
      
      unsubscribeRef.current = onSnapshot(
        agentRef,
        (docSnapshot) => {
          console.log('Agent document snapshot received');
          
          if (docSnapshot.exists()) {
            const agentData = { id: docSnapshot.id, ...docSnapshot.data() };
            console.log('Agent data loaded:', agentData);
            setAgent(agentData);
            setError('');
          } else {
            console.warn('Agent document does not exist');
            setAgent(null);
            setError('Agent not found');
          }
          
          setLoading(false);
        },
        (err) => {
          console.error('Error listening to agent document:', err);
          setError('Failed to load agent data');
          setLoading(false);
        }
      );
    } catch (err) {
      console.error('Error setting up agent listener:', err);
      setError('Failed to initialize agent data');
      setLoading(false);
    }

    // Cleanup function
    return () => {
      if (unsubscribeRef.current) {
        console.log('Cleaning up Firestore listener');
        unsubscribeRef.current();
        unsubscribeRef.current = null;
      }
    };
  }, [currentUser, agentId]);

  // Update agent data locally (optimistic updates)
  const updateAgentLocal = (updates) => {
    setAgent(prevAgent => prevAgent ? { ...prevAgent, ...updates } : null);
  };

  // Set saving state
  const setSavingState = (isSaving) => {
    setSaving(isSaving);
  };

  // Set error state
  const setErrorState = (errorMessage) => {
    setError(errorMessage);
  };

  // Clear error
  const clearError = () => {
    setError('');
  };

  return {
    agent,
    agentId,
    loading,
    error,
    saving,
    updateAgentLocal,
    setSaving: setSavingState,
    setError: setErrorState,
    clearError
  };
};

export default useAgentState;