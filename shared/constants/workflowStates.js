/**
 * Comprehensive Workflow States Constants for Alchemist Platform
 * 
 * Centralized definitions for all workflow states, statuses, and their metadata
 * used across all Alchemist services to ensure consistency.
 * 
 * This is the JavaScript/Node.js version that matches the Python constants.
 */

// ============================================================================
// WORKFLOW STAGE STATES
// ============================================================================

export const WORKFLOW_STAGE_STATUS = {
  PENDING: 'pending',
  AVAILABLE: 'available', 
  COMPLETED: 'completed',
  LOCKED: 'locked',
  IN_PROGRESS: 'in_progress'
};

// ============================================================================
// DEPLOYMENT STATUS STATES
// ============================================================================

export const DEPLOYMENT_STATUS = {
  // Queue states
  QUEUED: 'queued',
  INITIALIZING: 'initializing',
  
  // Build states
  GENERATING_CODE: 'generating_code',
  BUILDING_IMAGE: 'building_image',
  
  // Deploy states
  DEPLOYING: 'deploying',
  
  // Success states
  COMPLETED: 'completed',
  DEPLOYED: 'deployed',
  
  // Failure states
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  TIMEOUT: 'timeout',
  
  // Other states
  UNKNOWN: 'unknown'
};

// ============================================================================
// FEATURE ACCESS STATUS
// ============================================================================

export const FEATURE_STATUS = {
  COMPLETED: 'Completed',
  AVAILABLE: 'Available',
  PENDING: 'Pending',
  REQUIRES_DEPLOYMENT: 'Requires Deployment',
  LOCKED: 'Locked',
  DISABLED: 'Disabled'
};

// ============================================================================
// UI STATUS VARIANTS (for badges, chips, etc.)
// ============================================================================

export const STATUS_VARIANTS = {
  SUCCESS: 'success',
  WARNING: 'warning', 
  ERROR: 'error',
  INFO: 'info',
  DEFAULT: 'default',
  PRIMARY: 'primary',
  SECONDARY: 'secondary'
};

// ============================================================================
// STATUS GROUPS (logical groupings)
// ============================================================================

export const STATUS_GROUPS = {
  SUCCESS: [
    WORKFLOW_STAGE_STATUS.COMPLETED,
    DEPLOYMENT_STATUS.COMPLETED,
    DEPLOYMENT_STATUS.DEPLOYED,
    FEATURE_STATUS.COMPLETED,
    FEATURE_STATUS.AVAILABLE
  ],
  
  IN_PROGRESS: [
    WORKFLOW_STAGE_STATUS.IN_PROGRESS,
    WORKFLOW_STAGE_STATUS.AVAILABLE,
    DEPLOYMENT_STATUS.QUEUED,
    DEPLOYMENT_STATUS.INITIALIZING,
    DEPLOYMENT_STATUS.GENERATING_CODE,
    DEPLOYMENT_STATUS.BUILDING_IMAGE,
    DEPLOYMENT_STATUS.DEPLOYING,
    FEATURE_STATUS.PENDING
  ],
  
  ERROR: [
    DEPLOYMENT_STATUS.FAILED,
    DEPLOYMENT_STATUS.CANCELLED,
    DEPLOYMENT_STATUS.TIMEOUT
  ],
  
  BLOCKED: [
    WORKFLOW_STAGE_STATUS.LOCKED,
    WORKFLOW_STAGE_STATUS.PENDING,
    FEATURE_STATUS.REQUIRES_DEPLOYMENT,
    FEATURE_STATUS.LOCKED,
    FEATURE_STATUS.DISABLED
  ],
  
  INACTIVE: [
    DEPLOYMENT_STATUS.UNKNOWN,
    FEATURE_STATUS.DISABLED
  ]
};

// ============================================================================
// STATUS METADATA (icons, colors, descriptions)
// ============================================================================

export const STATUS_METADATA = {
  // Workflow Stage Metadata
  [WORKFLOW_STAGE_STATUS.PENDING]: {
    label: 'Pending',
    color: STATUS_VARIANTS.DEFAULT,
    variant: 'outlined',
    icon: 'CircleOutlined',
    description: 'Stage has not been started yet'
  },
  
  [WORKFLOW_STAGE_STATUS.AVAILABLE]: {
    label: 'Available',
    color: STATUS_VARIANTS.PRIMARY,
    variant: 'outlined',
    icon: 'Schedule',
    description: 'Stage is ready to be started'
  },
  
  [WORKFLOW_STAGE_STATUS.COMPLETED]: {
    label: 'Completed',
    color: STATUS_VARIANTS.SUCCESS,
    variant: 'filled',
    icon: 'CheckCircle',
    description: 'Stage has been successfully completed'
  },
  
  [WORKFLOW_STAGE_STATUS.LOCKED]: {
    label: 'Locked',
    color: STATUS_VARIANTS.DEFAULT,
    variant: 'outlined',
    icon: 'Lock',
    description: 'Stage is locked until requirements are met'
  },
  
  [WORKFLOW_STAGE_STATUS.IN_PROGRESS]: {
    label: 'In Progress',
    color: STATUS_VARIANTS.WARNING,
    variant: 'filled',
    icon: 'PlayArrow',
    description: 'Stage is currently being worked on'
  },

  // Deployment Status Metadata
  [DEPLOYMENT_STATUS.QUEUED]: {
    label: 'Queued',
    color: STATUS_VARIANTS.INFO,
    variant: 'outlined',
    icon: 'Queue',
    description: 'Deployment request is queued'
  },
  
  [DEPLOYMENT_STATUS.INITIALIZING]: {
    label: 'Initializing',
    color: STATUS_VARIANTS.WARNING,
    variant: 'outlined',
    icon: 'Refresh',
    description: 'Deployment is starting up'
  },
  
  [DEPLOYMENT_STATUS.GENERATING_CODE]: {
    label: 'Generating Code',
    color: STATUS_VARIANTS.WARNING,
    variant: 'filled',
    icon: 'Code',
    description: 'Generating agent code'
  },
  
  [DEPLOYMENT_STATUS.BUILDING_IMAGE]: {
    label: 'Building Image',
    color: STATUS_VARIANTS.WARNING,
    variant: 'filled',
    icon: 'Build',
    description: 'Building Docker image'
  },
  
  [DEPLOYMENT_STATUS.DEPLOYING]: {
    label: 'Deploying',
    color: STATUS_VARIANTS.WARNING,
    variant: 'filled',
    icon: 'RocketLaunch',
    description: 'Deploying to Cloud Run'
  },
  
  [DEPLOYMENT_STATUS.COMPLETED]: {
    label: 'Deployed',
    color: STATUS_VARIANTS.SUCCESS,
    variant: 'filled',
    icon: 'CheckCircle',
    description: 'Successfully deployed'
  },
  
  [DEPLOYMENT_STATUS.DEPLOYED]: {
    label: 'Deployed',
    color: STATUS_VARIANTS.SUCCESS,
    variant: 'filled',
    icon: 'CheckCircle',
    description: 'Successfully deployed'
  },
  
  [DEPLOYMENT_STATUS.FAILED]: {
    label: 'Failed',
    color: STATUS_VARIANTS.ERROR,
    variant: 'filled',
    icon: 'Error',
    description: 'Deployment failed'
  },
  
  [DEPLOYMENT_STATUS.CANCELLED]: {
    label: 'Cancelled',
    color: STATUS_VARIANTS.DEFAULT,
    variant: 'outlined',
    icon: 'Cancel',
    description: 'Deployment was cancelled'
  },
  
  [DEPLOYMENT_STATUS.TIMEOUT]: {
    label: 'Timeout',
    color: STATUS_VARIANTS.ERROR,
    variant: 'outlined',
    icon: 'AccessTime',
    description: 'Deployment timed out'
  },
  
  [DEPLOYMENT_STATUS.UNKNOWN]: {
    label: 'Unknown',
    color: STATUS_VARIANTS.DEFAULT,
    variant: 'outlined',
    icon: 'Help',
    description: 'Unknown deployment status'
  },

  // Feature Status Metadata
  [FEATURE_STATUS.COMPLETED]: {
    label: 'Completed',
    color: STATUS_VARIANTS.SUCCESS,
    variant: 'filled',
    icon: 'CheckCircle',
    description: 'Feature is completed and available'
  },
  
  [FEATURE_STATUS.AVAILABLE]: {
    label: 'Available',
    color: STATUS_VARIANTS.PRIMARY,
    variant: 'outlined',
    icon: 'Schedule',
    description: 'Feature is available to use'
  },
  
  [FEATURE_STATUS.PENDING]: {
    label: 'Pending',
    color: STATUS_VARIANTS.DEFAULT,
    variant: 'outlined',
    icon: 'Schedule',
    description: 'Feature is pending prerequisites'
  },
  
  [FEATURE_STATUS.REQUIRES_DEPLOYMENT]: {
    label: 'Requires Deployment',
    color: STATUS_VARIANTS.WARNING,
    variant: 'outlined',
    icon: 'Warning',
    description: 'Feature requires successful agent deployment'
  },
  
  [FEATURE_STATUS.LOCKED]: {
    label: 'Locked',
    color: STATUS_VARIANTS.DEFAULT,
    variant: 'outlined',
    icon: 'Lock',
    description: 'Feature is locked'
  },
  
  [FEATURE_STATUS.DISABLED]: {
    label: 'Disabled',
    color: STATUS_VARIANTS.DEFAULT,
    variant: 'outlined',
    icon: 'Block',
    description: 'Feature is disabled'
  }
};

// ============================================================================
// STATUS TRANSITION RULES
// ============================================================================

export const STATUS_TRANSITIONS = {
  // Workflow stage transitions
  [WORKFLOW_STAGE_STATUS.PENDING]: [
    WORKFLOW_STAGE_STATUS.AVAILABLE,
    WORKFLOW_STAGE_STATUS.LOCKED
  ],
  
  [WORKFLOW_STAGE_STATUS.AVAILABLE]: [
    WORKFLOW_STAGE_STATUS.IN_PROGRESS,
    WORKFLOW_STAGE_STATUS.COMPLETED,
    WORKFLOW_STAGE_STATUS.LOCKED
  ],
  
  [WORKFLOW_STAGE_STATUS.IN_PROGRESS]: [
    WORKFLOW_STAGE_STATUS.COMPLETED,
    WORKFLOW_STAGE_STATUS.AVAILABLE
  ],
  
  [WORKFLOW_STAGE_STATUS.LOCKED]: [
    WORKFLOW_STAGE_STATUS.AVAILABLE
  ],
  
  [WORKFLOW_STAGE_STATUS.COMPLETED]: [
    // Completed stages generally don't transition back
  ],

  // Deployment status transitions
  [DEPLOYMENT_STATUS.QUEUED]: [
    DEPLOYMENT_STATUS.INITIALIZING,
    DEPLOYMENT_STATUS.CANCELLED
  ],
  
  [DEPLOYMENT_STATUS.INITIALIZING]: [
    DEPLOYMENT_STATUS.GENERATING_CODE,
    DEPLOYMENT_STATUS.FAILED,
    DEPLOYMENT_STATUS.CANCELLED
  ],
  
  [DEPLOYMENT_STATUS.GENERATING_CODE]: [
    DEPLOYMENT_STATUS.BUILDING_IMAGE,
    DEPLOYMENT_STATUS.FAILED,
    DEPLOYMENT_STATUS.CANCELLED
  ],
  
  [DEPLOYMENT_STATUS.BUILDING_IMAGE]: [
    DEPLOYMENT_STATUS.DEPLOYING,
    DEPLOYMENT_STATUS.FAILED,
    DEPLOYMENT_STATUS.CANCELLED
  ],
  
  [DEPLOYMENT_STATUS.DEPLOYING]: [
    DEPLOYMENT_STATUS.COMPLETED,
    DEPLOYMENT_STATUS.DEPLOYED,
    DEPLOYMENT_STATUS.FAILED,
    DEPLOYMENT_STATUS.TIMEOUT
  ]
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Check if a status is in a specific group
 */
export const isStatusInGroup = (status, group) => {
  return STATUS_GROUPS[group]?.includes(status) || false;
};

/**
 * Check if a status represents success
 */
export const isSuccessStatus = (status) => {
  return isStatusInGroup(status, 'SUCCESS');
};

/**
 * Check if a status represents an in-progress state
 */
export const isInProgressStatus = (status) => {
  return isStatusInGroup(status, 'IN_PROGRESS');
};

/**
 * Check if a status represents an error state
 */
export const isErrorStatus = (status) => {
  return isStatusInGroup(status, 'ERROR');
};

/**
 * Check if a status represents a blocked state
 */
export const isBlockedStatus = (status) => {
  return isStatusInGroup(status, 'BLOCKED');
};

/**
 * Get metadata for a status
 */
export const getStatusMetadata = (status) => {
  return STATUS_METADATA[status] || STATUS_METADATA[DEPLOYMENT_STATUS.UNKNOWN];
};

/**
 * Check if a status transition is valid
 */
export const isValidTransition = (fromStatus, toStatus) => {
  const allowedTransitions = STATUS_TRANSITIONS[fromStatus];
  return allowedTransitions ? allowedTransitions.includes(toStatus) : false;
};

/**
 * Get all possible next statuses from current status
 */
export const getNextStatuses = (currentStatus) => {
  return STATUS_TRANSITIONS[currentStatus] || [];
};

/**
 * Normalize status string (lowercase, trim)
 */
export const normalizeStatus = (status) => {
  return status?.toString().toLowerCase().trim();
};

/**
 * Get UI variant for status (success, warning, error, etc.)
 */
export const getStatusVariant = (status) => {
  if (isSuccessStatus(status)) return STATUS_VARIANTS.SUCCESS;
  if (isInProgressStatus(status)) return STATUS_VARIANTS.WARNING;
  if (isErrorStatus(status)) return STATUS_VARIANTS.ERROR;
  if (isBlockedStatus(status)) return STATUS_VARIANTS.DEFAULT;
  return STATUS_VARIANTS.INFO;
};

/**
 * Get human-readable label for status
 */
export const getStatusLabel = (status) => {
  return getStatusMetadata(status).label;
};

/**
 * Get icon name for status
 */
export const getStatusIcon = (status) => {
  return getStatusMetadata(status).icon;
};

/**
 * Get color for status
 */
export const getStatusColor = (status) => {
  return getStatusMetadata(status).color;
};

/**
 * Get description for status
 */
export const getStatusDescription = (status) => {
  return getStatusMetadata(status).description;
};

// ============================================================================
// EXPORT ALL CONSTANTS
// ============================================================================

export default {
  WORKFLOW_STAGE_STATUS,
  DEPLOYMENT_STATUS,
  FEATURE_STATUS,
  STATUS_VARIANTS,
  STATUS_GROUPS,
  STATUS_METADATA,
  STATUS_TRANSITIONS,
  
  // Utility functions
  isStatusInGroup,
  isSuccessStatus,
  isInProgressStatus,
  isErrorStatus,
  isBlockedStatus,
  getStatusMetadata,
  isValidTransition,
  getNextStatuses,
  normalizeStatus,
  getStatusVariant,
  getStatusLabel,
  getStatusIcon,
  getStatusColor,
  getStatusDescription
};