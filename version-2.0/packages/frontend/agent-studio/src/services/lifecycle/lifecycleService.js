/**
 * Agent Lifecycle Service
 * 
 * Service to fetch and display agent lifecycle events from Firestore
 */
import { db } from '../../utils/firebase';
import { collection, query, where, orderBy, limit, getDocs } from 'firebase/firestore';

class LifecycleService {
  
  /**
   * Get all lifecycle events for an agent
   */
  async getAgentLifecycleEvents(agentId, maxEvents = 100) {
    try {
      const eventsRef = collection(db, 'agent_lifecycle_events');
      const eventsQuery = query(
        eventsRef,
        where('agent_id', '==', agentId),
        orderBy('timestamp', 'desc'),
        limit(maxEvents)
      );
      
      const snapshot = await getDocs(eventsQuery);
      const events = [];
      
      snapshot.forEach((doc) => {
        const eventData = doc.data();
        events.push({
          id: doc.id,
          ...eventData,
          timestamp: eventData.timestamp?.toDate() || new Date()
        });
      });
      
      return events;
    } catch (error) {
      console.error('Error fetching agent lifecycle events:', error);
      return [];
    }
  }
  
  /**
   * Get lifecycle events grouped by type
   */
  async getGroupedLifecycleEvents(agentId) {
    const events = await this.getAgentLifecycleEvents(agentId);
    
    const grouped = {
      creation: [],
      configuration: [],
      knowledge: [],
      deployment: [],
      other: []
    };
    
    events.forEach(event => {
      switch (event.event_type) {
        case 'agent_created':
        case 'agent_named':
          grouped.creation.push(event);
          break;
        case 'agent_description_updated':
        case 'prompt_update':
        case 'configuration_updated':
          grouped.configuration.push(event);
          break;
        case 'knowledge_base_file_added':
        case 'knowledge_base_file_removed':
        case 'external_api_attached':
        case 'external_api_detached':
          grouped.knowledge.push(event);
          break;
        case 'agent_deployed':
        case 'agent_undeployed':
        case 'agent_status_changed':
        case 'agent_deleted':
          grouped.deployment.push(event);
          break;
        default:
          grouped.other.push(event);
      }
    });
    
    return grouped;
  }
  
  /**
   * Get event icon based on event type
   */
  getEventIcon(eventType) {
    const iconMap = {
      'agent_created': '🎂',
      'agent_named': '📝',
      'agent_description_updated': '✏️',
      'prompt_update': '🔧',
      'knowledge_base_file_added': '📄',
      'knowledge_base_file_removed': '🗑️',
      'external_api_attached': '🔗',
      'external_api_detached': '🔌',
      'agent_deployed': '🚀',
      'agent_undeployed': '📤',
      'agent_status_changed': '🔄',
      'configuration_updated': '⚙️',
      'training_started': '🎓',
      'training_completed': '✅',
      'agent_deleted': '🪦'
    };
    
    return iconMap[eventType] || '📋';
  }
  
  /**
   * Get event color based on event type
   */
  getEventColor(eventType) {
    const colorMap = {
      'agent_created': 'success',
      'agent_named': 'info',
      'agent_description_updated': 'info',
      'prompt_update': 'warning',
      'knowledge_base_file_added': 'primary',
      'knowledge_base_file_removed': 'error',
      'external_api_attached': 'primary',
      'external_api_detached': 'warning',
      'agent_deployed': 'success',
      'agent_undeployed': 'warning',
      'agent_status_changed': 'info',
      'configuration_updated': 'info',
      'training_started': 'info',
      'training_completed': 'success',
      'agent_deleted': 'error'
    };
    
    return colorMap[eventType] || 'default';
  }
  
  /**
   * Format event for display
   */
  formatEventForDisplay(event) {
    const timeSince = this.getTimeSince(event.timestamp);
    
    return {
      ...event,
      icon: this.getEventIcon(event.event_type),
      color: this.getEventColor(event.event_type),
      timeSince: timeSince,
      formattedDate: event.timestamp.toLocaleString()
    };
  }
  
  /**
   * Get human-readable time since event
   */
  getTimeSince(timestamp) {
    const now = new Date();
    const diffMs = now - timestamp;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    
    return timestamp.toLocaleDateString();
  }
  
  /**
   * Get lifecycle statistics
   */
  getLifecycleStats(events) {
    const stats = {
      totalEvents: events.length,
      creationDate: null,
      lastActivity: null,
      deploymentCount: 0,
      knowledgeUpdates: 0,
      configurationUpdates: 0
    };
    
    if (events.length === 0) return stats;
    
    // Find creation date (oldest event)
    const creationEvent = events.find(e => e.event_type === 'agent_created');
    if (creationEvent) {
      stats.creationDate = creationEvent.timestamp;
    }
    
    // Last activity (newest event)
    stats.lastActivity = events[0].timestamp; // Events are ordered desc
    
    // Count specific event types
    events.forEach(event => {
      switch (event.event_type) {
        case 'agent_deployed':
          stats.deploymentCount++;
          break;
        case 'knowledge_base_file_added':
        case 'knowledge_base_file_removed':
        case 'external_api_attached':
        case 'external_api_detached':
          stats.knowledgeUpdates++;
          break;
        case 'agent_description_updated':
        case 'prompt_update':
        case 'configuration_updated':
          stats.configurationUpdates++;
          break;
      }
    });
    
    return stats;
  }
}

export const lifecycleService = new LifecycleService();
export default lifecycleService;