"""
Alert Service

Manages alerts and notifications for story-loss threshold exceedance,
umwelt conflicts, and other system events requiring attention.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

from firebase_admin import firestore

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    STORY_LOSS_THRESHOLD = "story_loss_threshold"
    UMWELT_CONFLICT = "umwelt_conflict"
    SYSTEM_ERROR = "system_error"
    AGENT_FAILURE = "agent_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class AlertStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Defines conditions for triggering alerts"""
    id: str
    name: str
    alert_type: AlertType
    severity: AlertSeverity
    conditions: Dict[str, Any]
    enabled: bool = True
    cooldown_minutes: int = 60
    description: str = ""
    
    def matches_event(self, event_data: Dict[str, Any]) -> bool:
        """Check if an event matches this alert rule"""
        try:
            # Check alert type
            if event_data.get("event_type") != self.alert_type.value:
                return False
            
            # Check specific conditions
            for key, expected_value in self.conditions.items():
                if key not in event_data:
                    return False
                
                actual_value = event_data[key]
                
                # Handle different comparison types
                if isinstance(expected_value, dict):
                    if "min" in expected_value and actual_value < expected_value["min"]:
                        return False
                    if "max" in expected_value and actual_value > expected_value["max"]:
                        return False
                    if "equals" in expected_value and actual_value != expected_value["equals"]:
                        return False
                elif actual_value != expected_value:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching event to alert rule {self.id}: {e}")
            return False


@dataclass
class Alert:
    """Represents an active alert"""
    id: str
    rule_id: str
    agent_id: Optional[str]
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    description: str
    event_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for storage"""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "agent_id": self.agent_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "event_data": self.event_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "acknowledged_at": self.acknowledged_at,
            "resolved_at": self.resolved_at,
            "acknowledged_by": self.acknowledged_by
        }


class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, channel_id: str, config: Dict[str, Any]):
        self.channel_id = channel_id
        self.config = config
        self.enabled = config.get("enabled", True)
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for an alert"""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send email notification"""
        try:
            # In a real implementation, this would integrate with email service
            logger.info(f"Sending email notification for alert {alert.id}")
            
            # Mock email sending
            email_data = {
                "to": self.config.get("recipients", []),
                "subject": f"[{alert.severity.value.upper()}] {alert.title}",
                "body": f"""
                Alert: {alert.title}
                Severity: {alert.severity.value}
                Agent: {alert.agent_id or 'System'}
                Description: {alert.description}
                
                Time: {alert.created_at.isoformat()}
                
                Event Data:
                {json.dumps(alert.event_data, indent=2)}
                """
            }
            
            logger.info(f"Email notification sent: {email_data}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification for alert {alert.id}: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send webhook notification"""
        try:
            import aiohttp
            
            webhook_url = self.config.get("url")
            if not webhook_url:
                logger.error("No webhook URL configured")
                return False
            
            payload = {
                "alert_id": alert.id,
                "agent_id": alert.agent_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.created_at.isoformat(),
                "event_data": alert.event_data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent for alert {alert.id}")
                        return True
                    else:
                        logger.error(f"Webhook returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send webhook notification for alert {alert.id}: {e}")
            return False


class AlertService:
    """Main alert management service"""
    
    def __init__(self):
        self.db = None  # Will be initialized lazily
        self.alert_rules: Dict[str, AlertRule] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self._initialized = False
        
        # Default alert rules
        self._setup_default_rules()
    
    async def initialize(self):
        """Initialize the alert service"""
        if self._initialized:
            return
        
        self.db = firestore.client()
        
        # Load alert rules from Firebase
        await self._load_alert_rules()
        
        # Setup notification channels
        await self._setup_notification_channels()
        
        # Load active alerts
        await self._load_active_alerts()
        
        self._initialized = True
        logger.info("AlertService initialized")
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        # Story-loss threshold alert
        self.alert_rules["story_loss_threshold"] = AlertRule(
            id="story_loss_threshold",
            name="Story-Loss Threshold Exceeded",
            alert_type=AlertType.STORY_LOSS_THRESHOLD,
            severity=AlertSeverity.WARNING,
            conditions={
                "story_loss": {"min": 0.15},
                "threshold_exceeded": True
            },
            cooldown_minutes=30,
            description="Triggered when agent's story-loss exceeds 0.15 threshold"
        )
        
        # Critical story-loss alert
        self.alert_rules["story_loss_critical"] = AlertRule(
            id="story_loss_critical",
            name="Critical Story-Loss Level",
            alert_type=AlertType.STORY_LOSS_THRESHOLD,
            severity=AlertSeverity.ERROR,
            conditions={
                "story_loss": {"min": 0.3}
            },
            cooldown_minutes=15,
            description="Triggered when agent's story-loss reaches critical levels (>0.3)"
        )
        
        # Umwelt conflict alert
        self.alert_rules["umwelt_conflict"] = AlertRule(
            id="umwelt_conflict",
            name="Umwelt Conflict Detected",
            alert_type=AlertType.UMWELT_CONFLICT,
            severity=AlertSeverity.WARNING,
            conditions={
                "severity": {"equals": "high"}
            },
            cooldown_minutes=60,
            description="Triggered when high-severity Umwelt conflicts are detected"
        )
        
        # Critical Umwelt conflict alert
        self.alert_rules["umwelt_conflict_critical"] = AlertRule(
            id="umwelt_conflict_critical",
            name="Critical Umwelt Conflict",
            alert_type=AlertType.UMWELT_CONFLICT,
            severity=AlertSeverity.ERROR,
            conditions={
                "severity": {"equals": "critical"}
            },
            cooldown_minutes=15,
            description="Triggered when critical Umwelt conflicts are detected"
        )
    
    async def _load_alert_rules(self):
        """Load alert rules from Firebase"""
        try:
            rules_ref = self.db.collection('alert_rules')
            docs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(rules_ref.stream())
            )
            
            for doc in docs:
                data = doc.to_dict()
                rule = AlertRule(
                    id=doc.id,
                    name=data["name"],
                    alert_type=AlertType(data["alert_type"]),
                    severity=AlertSeverity(data["severity"]),
                    conditions=data["conditions"],
                    enabled=data.get("enabled", True),
                    cooldown_minutes=data.get("cooldown_minutes", 60),
                    description=data.get("description", "")
                )
                self.alert_rules[rule.id] = rule
                
            logger.info(f"Loaded {len(docs)} alert rules from Firebase")
            
        except Exception as e:
            logger.error(f"Error loading alert rules: {e}")
    
    async def _setup_notification_channels(self):
        """Setup notification channels"""
        try:
            channels_ref = self.db.collection('notification_channels')
            docs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(channels_ref.stream())
            )
            
            for doc in docs:
                data = doc.to_dict()
                channel_type = data.get("type", "email")
                
                if channel_type == "email":
                    channel = EmailNotificationChannel(doc.id, data)
                elif channel_type == "webhook":
                    channel = WebhookNotificationChannel(doc.id, data)
                else:
                    logger.warning(f"Unknown notification channel type: {channel_type}")
                    continue
                
                self.notification_channels[doc.id] = channel
                
            logger.info(f"Setup {len(self.notification_channels)} notification channels")
            
        except Exception as e:
            logger.error(f"Error setting up notification channels: {e}")
    
    async def _load_active_alerts(self):
        """Load active alerts from Firebase"""
        try:
            alerts_ref = self.db.collection('alerts').where('status', 'in', ['active', 'acknowledged'])
            docs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(alerts_ref.stream())
            )
            
            for doc in docs:
                data = doc.to_dict()
                alert = Alert(
                    id=doc.id,
                    rule_id=data["rule_id"],
                    agent_id=data.get("agent_id"),
                    alert_type=AlertType(data["alert_type"]),
                    severity=AlertSeverity(data["severity"]),
                    status=AlertStatus(data["status"]),
                    title=data["title"],
                    description=data["description"],
                    event_data=data["event_data"],
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    acknowledged_at=data.get("acknowledged_at"),
                    resolved_at=data.get("resolved_at"),
                    acknowledged_by=data.get("acknowledged_by")
                )
                self.active_alerts[alert.id] = alert
                
            logger.info(f"Loaded {len(self.active_alerts)} active alerts")
            
        except Exception as e:
            logger.error(f"Error loading active alerts: {e}")
    
    async def process_event(self, event_data: Dict[str, Any]) -> List[str]:
        """
        Process an event and create alerts if rules match
        
        Args:
            event_data: Event data containing type and relevant information
            
        Returns:
            List of alert IDs that were created
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            created_alerts = []
            
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                if rule.matches_event(event_data):
                    # Check cooldown period
                    if await self._is_in_cooldown(rule, event_data.get("agent_id")):
                        logger.debug(f"Alert rule {rule.id} is in cooldown period")
                        continue
                    
                    # Create alert
                    alert_id = await self._create_alert(rule, event_data)
                    if alert_id:
                        created_alerts.append(alert_id)
                        
                        # Send notifications
                        await self._send_notifications(self.active_alerts[alert_id])
            
            return created_alerts
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return []
    
    async def _is_in_cooldown(self, rule: AlertRule, agent_id: Optional[str]) -> bool:
        """Check if alert rule is in cooldown period"""
        try:
            # Check for recent alerts with same rule and agent
            cutoff_time = datetime.now() - timedelta(minutes=rule.cooldown_minutes)
            
            for alert in self.active_alerts.values():
                if (alert.rule_id == rule.id and 
                    alert.agent_id == agent_id and 
                    alert.created_at > cutoff_time):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking cooldown for rule {rule.id}: {e}")
            return True  # Err on the side of caution
    
    async def _create_alert(self, rule: AlertRule, event_data: Dict[str, Any]) -> Optional[str]:
        """Create a new alert"""
        try:
            alert_id = f"alert_{rule.id}_{int(datetime.now().timestamp())}"
            
            # Generate title and description
            title = self._generate_alert_title(rule, event_data)
            description = self._generate_alert_description(rule, event_data)
            
            alert = Alert(
                id=alert_id,
                rule_id=rule.id,
                agent_id=event_data.get("agent_id"),
                alert_type=rule.alert_type,
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                title=title,
                description=description,
                event_data=event_data,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store in Firebase
            alert_ref = self.db.collection('alerts').document(alert_id)
            await asyncio.get_event_loop().run_in_executor(
                None, alert_ref.set, alert.to_dict()
            )
            
            # Add to active alerts
            self.active_alerts[alert_id] = alert
            
            logger.info(f"Created alert {alert_id} for rule {rule.id}")
            return alert_id
            
        except Exception as e:
            logger.error(f"Error creating alert for rule {rule.id}: {e}")
            return None
    
    def _generate_alert_title(self, rule: AlertRule, event_data: Dict[str, Any]) -> str:
        """Generate alert title based on rule and event data"""
        agent_id = event_data.get("agent_id", "Unknown")
        
        if rule.alert_type == AlertType.STORY_LOSS_THRESHOLD:
            story_loss = event_data.get("story_loss", 0)
            return f"Story-Loss Alert: Agent {agent_id} ({story_loss:.3f})"
        elif rule.alert_type == AlertType.UMWELT_CONFLICT:
            conflict_type = event_data.get("conflict_type", "unknown")
            return f"Umwelt Conflict: {conflict_type} (Agent {agent_id})"
        else:
            return f"{rule.name}: Agent {agent_id}"
    
    def _generate_alert_description(self, rule: AlertRule, event_data: Dict[str, Any]) -> str:
        """Generate alert description based on rule and event data"""
        base_description = rule.description
        
        if rule.alert_type == AlertType.STORY_LOSS_THRESHOLD:
            story_loss = event_data.get("story_loss", 0)
            threshold = event_data.get("threshold", 0.15)
            return f"{base_description}. Current value: {story_loss:.3f}, Threshold: {threshold}"
        elif rule.alert_type == AlertType.UMWELT_CONFLICT:
            conflict_type = event_data.get("conflict_type", "unknown")
            description = event_data.get("description", "No details available")
            return f"{base_description}. Conflict type: {conflict_type}. Details: {description}"
        else:
            return base_description
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        try:
            for channel in self.notification_channels.values():
                if not channel.enabled:
                    continue
                
                # Check if this channel should handle this severity
                min_severity = AlertSeverity(channel.config.get("min_severity", "info"))
                severity_order = {"info": 0, "warning": 1, "error": 2, "critical": 3}
                
                if severity_order[alert.severity.value] >= severity_order[min_severity.value]:
                    success = await channel.send_notification(alert)
                    if success:
                        logger.info(f"Notification sent via {channel.channel_id} for alert {alert.id}")
                    else:
                        logger.error(f"Failed to send notification via {channel.channel_id} for alert {alert.id}")
                        
        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.id}: {e}")
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = acknowledged_by
            alert.updated_at = datetime.now()
            
            # Update in Firebase
            alert_ref = self.db.collection('alerts').document(alert_id)
            await asyncio.get_event_loop().run_in_executor(
                None, alert_ref.update, {
                    'status': alert.status.value,
                    'acknowledged_at': alert.acknowledged_at,
                    'acknowledged_by': alert.acknowledged_by,
                    'updated_at': alert.updated_at
                }
            )
            
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.updated_at = datetime.now()
            
            # Update in Firebase
            alert_ref = self.db.collection('alerts').document(alert_id)
            await asyncio.get_event_loop().run_in_executor(
                None, alert_ref.update, {
                    'status': alert.status.value,
                    'resolved_at': alert.resolved_at,
                    'updated_at': alert.updated_at
                }
            )
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
    
    async def get_active_alerts(self, agent_id: Optional[str] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by agent ID"""
        if agent_id:
            return [alert for alert in self.active_alerts.values() if alert.agent_id == agent_id]
        else:
            return list(self.active_alerts.values())


# Global instance
_alert_service: Optional[AlertService] = None


async def get_alert_service() -> AlertService:
    """Get the global alert service instance"""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    if not _alert_service._initialized:
        await _alert_service.initialize()
    return _alert_service


async def init_alert_service() -> AlertService:
    """Initialize and return the global alert service instance"""
    return await get_alert_service()