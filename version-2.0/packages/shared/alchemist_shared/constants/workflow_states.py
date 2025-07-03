"""
Comprehensive Workflow States Constants for Alchemist Platform

Centralized definitions for all workflow states, statuses, and their metadata
used across all Alchemist services to ensure consistency.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# ============================================================================
# WORKFLOW STAGE STATES
# ============================================================================

class WorkflowStageStatus(str, Enum):
    """Workflow stage states"""
    PENDING = "pending"
    AVAILABLE = "available"
    COMPLETED = "completed"
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"


# ============================================================================
# DEPLOYMENT STATUS STATES
# ============================================================================

class DeploymentStatus(str, Enum):
    """Deployment status states"""
    # Queue states
    QUEUED = "queued"
    INITIALIZING = "initializing"
    
    # Build states
    GENERATING_CODE = "generating_code"
    BUILDING_IMAGE = "building_image"
    
    # Deploy states
    DEPLOYING = "deploying"
    
    # Success states
    COMPLETED = "completed"
    DEPLOYED = "deployed"
    
    # Failure states
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    
    # Other states
    UNKNOWN = "unknown"


# ============================================================================
# FEATURE ACCESS STATUS
# ============================================================================

class FeatureStatus(str, Enum):
    """Feature access status"""
    COMPLETED = "Completed"
    AVAILABLE = "Available"
    PENDING = "Pending"
    REQUIRES_DEPLOYMENT = "Requires Deployment"
    LOCKED = "Locked"
    DISABLED = "Disabled"


# ============================================================================
# UI STATUS VARIANTS
# ============================================================================

class StatusVariants(str, Enum):
    """UI status variants for badges, chips, etc."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    DEFAULT = "default"
    PRIMARY = "primary"
    SECONDARY = "secondary"


# ============================================================================
# STATUS METADATA
# ============================================================================

@dataclass
class StatusMetadata:
    """Metadata for a status"""
    label: str
    color: str
    variant: str
    icon: str
    description: str


# Status metadata mapping
STATUS_METADATA: Dict[str, StatusMetadata] = {
    # Workflow Stage Metadata
    WorkflowStageStatus.PENDING: StatusMetadata(
        label="Pending",
        color=StatusVariants.DEFAULT,
        variant="outlined",
        icon="CircleOutlined",
        description="Stage has not been started yet"
    ),
    
    WorkflowStageStatus.AVAILABLE: StatusMetadata(
        label="Available",
        color=StatusVariants.PRIMARY,
        variant="outlined",
        icon="Schedule",
        description="Stage is ready to be started"
    ),
    
    WorkflowStageStatus.COMPLETED: StatusMetadata(
        label="Completed",
        color=StatusVariants.SUCCESS,
        variant="filled",
        icon="CheckCircle",
        description="Stage has been successfully completed"
    ),
    
    WorkflowStageStatus.LOCKED: StatusMetadata(
        label="Locked",
        color=StatusVariants.DEFAULT,
        variant="outlined",
        icon="Lock",
        description="Stage is locked until requirements are met"
    ),
    
    WorkflowStageStatus.IN_PROGRESS: StatusMetadata(
        label="In Progress",
        color=StatusVariants.WARNING,
        variant="filled",
        icon="PlayArrow",
        description="Stage is currently being worked on"
    ),

    # Deployment Status Metadata
    DeploymentStatus.QUEUED: StatusMetadata(
        label="Queued",
        color=StatusVariants.INFO,
        variant="outlined",
        icon="Queue",
        description="Deployment request is queued"
    ),
    
    DeploymentStatus.INITIALIZING: StatusMetadata(
        label="Initializing",
        color=StatusVariants.WARNING,
        variant="outlined",
        icon="Refresh",
        description="Deployment is starting up"
    ),
    
    DeploymentStatus.GENERATING_CODE: StatusMetadata(
        label="Generating Code",
        color=StatusVariants.WARNING,
        variant="filled",
        icon="Code",
        description="Generating agent code"
    ),
    
    DeploymentStatus.BUILDING_IMAGE: StatusMetadata(
        label="Building Image",
        color=StatusVariants.WARNING,
        variant="filled",
        icon="Build",
        description="Building Docker image"
    ),
    
    DeploymentStatus.DEPLOYING: StatusMetadata(
        label="Deploying",
        color=StatusVariants.WARNING,
        variant="filled",
        icon="RocketLaunch",
        description="Deploying to Cloud Run"
    ),
    
    DeploymentStatus.COMPLETED: StatusMetadata(
        label="Deployed",
        color=StatusVariants.SUCCESS,
        variant="filled",
        icon="CheckCircle",
        description="Successfully deployed"
    ),
    
    DeploymentStatus.DEPLOYED: StatusMetadata(
        label="Deployed",
        color=StatusVariants.SUCCESS,
        variant="filled",
        icon="CheckCircle",
        description="Successfully deployed"
    ),
    
    DeploymentStatus.FAILED: StatusMetadata(
        label="Failed",
        color=StatusVariants.ERROR,
        variant="filled",
        icon="Error",
        description="Deployment failed"
    ),
    
    DeploymentStatus.CANCELLED: StatusMetadata(
        label="Cancelled",
        color=StatusVariants.DEFAULT,
        variant="outlined",
        icon="Cancel",
        description="Deployment was cancelled"
    ),
    
    DeploymentStatus.TIMEOUT: StatusMetadata(
        label="Timeout",
        color=StatusVariants.ERROR,
        variant="outlined",
        icon="AccessTime",
        description="Deployment timed out"
    ),
    
    DeploymentStatus.UNKNOWN: StatusMetadata(
        label="Unknown",
        color=StatusVariants.DEFAULT,
        variant="outlined",
        icon="Help",
        description="Unknown deployment status"
    ),

    # Feature Status Metadata
    FeatureStatus.COMPLETED: StatusMetadata(
        label="Completed",
        color=StatusVariants.SUCCESS,
        variant="filled",
        icon="CheckCircle",
        description="Feature is completed and available"
    ),
    
    FeatureStatus.AVAILABLE: StatusMetadata(
        label="Available",
        color=StatusVariants.PRIMARY,
        variant="outlined",
        icon="Schedule",
        description="Feature is available to use"
    ),
    
    FeatureStatus.PENDING: StatusMetadata(
        label="Pending",
        color=StatusVariants.DEFAULT,
        variant="outlined",
        icon="Schedule",
        description="Feature is pending prerequisites"
    ),
    
    FeatureStatus.REQUIRES_DEPLOYMENT: StatusMetadata(
        label="Requires Deployment",
        color=StatusVariants.WARNING,
        variant="outlined",
        icon="Warning",
        description="Feature requires successful agent deployment"
    ),
    
    FeatureStatus.LOCKED: StatusMetadata(
        label="Locked",
        color=StatusVariants.DEFAULT,
        variant="outlined",
        icon="Lock",
        description="Feature is locked"
    ),
    
    FeatureStatus.DISABLED: StatusMetadata(
        label="Disabled",
        color=StatusVariants.DEFAULT,
        variant="outlined",
        icon="Block",
        description="Feature is disabled"
    )
}


# ============================================================================
# STATUS GROUPS
# ============================================================================

STATUS_GROUPS = {
    "SUCCESS": [
        WorkflowStageStatus.COMPLETED,
        DeploymentStatus.COMPLETED,
        DeploymentStatus.DEPLOYED,
        FeatureStatus.COMPLETED,
        FeatureStatus.AVAILABLE
    ],
    
    "IN_PROGRESS": [
        WorkflowStageStatus.IN_PROGRESS,
        WorkflowStageStatus.AVAILABLE,
        DeploymentStatus.QUEUED,
        DeploymentStatus.INITIALIZING,
        DeploymentStatus.GENERATING_CODE,
        DeploymentStatus.BUILDING_IMAGE,
        DeploymentStatus.DEPLOYING,
        FeatureStatus.PENDING
    ],
    
    "ERROR": [
        DeploymentStatus.FAILED,
        DeploymentStatus.CANCELLED,
        DeploymentStatus.TIMEOUT
    ],
    
    "BLOCKED": [
        WorkflowStageStatus.LOCKED,
        WorkflowStageStatus.PENDING,
        FeatureStatus.REQUIRES_DEPLOYMENT,
        FeatureStatus.LOCKED,
        FeatureStatus.DISABLED
    ],
    
    "INACTIVE": [
        DeploymentStatus.UNKNOWN,
        FeatureStatus.DISABLED
    ]
}


# ============================================================================
# STATUS TRANSITION RULES
# ============================================================================

STATUS_TRANSITIONS = {
    # Workflow stage transitions
    WorkflowStageStatus.PENDING: [
        WorkflowStageStatus.AVAILABLE,
        WorkflowStageStatus.LOCKED
    ],
    
    WorkflowStageStatus.AVAILABLE: [
        WorkflowStageStatus.IN_PROGRESS,
        WorkflowStageStatus.COMPLETED,
        WorkflowStageStatus.LOCKED
    ],
    
    WorkflowStageStatus.IN_PROGRESS: [
        WorkflowStageStatus.COMPLETED,
        WorkflowStageStatus.AVAILABLE
    ],
    
    WorkflowStageStatus.LOCKED: [
        WorkflowStageStatus.AVAILABLE
    ],
    
    WorkflowStageStatus.COMPLETED: [],  # Completed stages generally don't transition back

    # Deployment status transitions
    DeploymentStatus.QUEUED: [
        DeploymentStatus.INITIALIZING,
        DeploymentStatus.CANCELLED
    ],
    
    DeploymentStatus.INITIALIZING: [
        DeploymentStatus.GENERATING_CODE,
        DeploymentStatus.FAILED,
        DeploymentStatus.CANCELLED
    ],
    
    DeploymentStatus.GENERATING_CODE: [
        DeploymentStatus.BUILDING_IMAGE,
        DeploymentStatus.FAILED,
        DeploymentStatus.CANCELLED
    ],
    
    DeploymentStatus.BUILDING_IMAGE: [
        DeploymentStatus.DEPLOYING,
        DeploymentStatus.FAILED,
        DeploymentStatus.CANCELLED
    ],
    
    DeploymentStatus.DEPLOYING: [
        DeploymentStatus.COMPLETED,
        DeploymentStatus.DEPLOYED,
        DeploymentStatus.FAILED,
        DeploymentStatus.TIMEOUT
    ]
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_status_in_group(status: str, group: str) -> bool:
    """Check if a status is in a specific group"""
    return status in STATUS_GROUPS.get(group, [])


def is_success_status(status: str) -> bool:
    """Check if a status represents success"""
    return is_status_in_group(status, "SUCCESS")


def is_in_progress_status(status: str) -> bool:
    """Check if a status represents an in-progress state"""
    return is_status_in_group(status, "IN_PROGRESS")


def is_error_status(status: str) -> bool:
    """Check if a status represents an error state"""
    return is_status_in_group(status, "ERROR")


def is_blocked_status(status: str) -> bool:
    """Check if a status represents a blocked state"""
    return is_status_in_group(status, "BLOCKED")


def get_status_metadata(status: str) -> StatusMetadata:
    """Get metadata for a status"""
    return STATUS_METADATA.get(status, STATUS_METADATA[DeploymentStatus.UNKNOWN])


def is_valid_transition(from_status: str, to_status: str) -> bool:
    """Check if a status transition is valid"""
    allowed_transitions = STATUS_TRANSITIONS.get(from_status, [])
    return to_status in allowed_transitions


def get_next_statuses(current_status: str) -> List[str]:
    """Get all possible next statuses from current status"""
    return STATUS_TRANSITIONS.get(current_status, [])


def normalize_status(status: str) -> str:
    """Normalize status string (lowercase, strip)"""
    return status.lower().strip() if status else ""


def get_status_variant(status: str) -> str:
    """Get UI variant for status"""
    if is_success_status(status):
        return StatusVariants.SUCCESS
    elif is_in_progress_status(status):
        return StatusVariants.WARNING
    elif is_error_status(status):
        return StatusVariants.ERROR
    elif is_blocked_status(status):
        return StatusVariants.DEFAULT
    else:
        return StatusVariants.INFO


def get_status_label(status: str) -> str:
    """Get human-readable label for status"""
    return get_status_metadata(status).label


def get_status_icon(status: str) -> str:
    """Get icon name for status"""
    return get_status_metadata(status).icon


def get_status_color(status: str) -> str:
    """Get color for status"""
    return get_status_metadata(status).color


def get_status_description(status: str) -> str:
    """Get description for status"""
    return get_status_metadata(status).description


# ============================================================================
# EXPORT ALL CONSTANTS
# ============================================================================

__all__ = [
    # Enums
    "WorkflowStageStatus",
    "DeploymentStatus", 
    "FeatureStatus",
    "StatusVariants",
    
    # Data classes
    "StatusMetadata",
    
    # Constants
    "STATUS_METADATA",
    "STATUS_GROUPS",
    "STATUS_TRANSITIONS",
    
    # Utility functions
    "is_status_in_group",
    "is_success_status",
    "is_in_progress_status", 
    "is_error_status",
    "is_blocked_status",
    "get_status_metadata",
    "is_valid_transition",
    "get_next_statuses",
    "normalize_status",
    "get_status_variant",
    "get_status_label",
    "get_status_icon",
    "get_status_color",
    "get_status_description"
]