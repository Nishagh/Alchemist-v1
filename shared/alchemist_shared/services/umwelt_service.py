"""
Umwelt Service

Manages task-specific Umwelt layers for agents - live "world snapshots" relevant
to each agent's Core Objective Function (CoF). Provides filtered external signals
and maintains agent-specific environmental context.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import time

from firebase_admin import firestore

logger = logging.getLogger(__name__)


class SignalType(Enum):
    API = "api"
    DATABASE = "database"
    SENSOR = "sensor"
    EVENT = "event"
    MESSAGE = "message"


class UpdatePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExternalSignal:
    """Represents an external signal source for Umwelt"""
    id: str
    type: SignalType
    source: str
    endpoint: Optional[str] = None
    query: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 300  # 5 minutes default
    last_updated: Optional[datetime] = None
    active: bool = True
    
    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique ID for signal"""
        content = f"{self.type.value}_{self.source}_{self.endpoint or ''}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class UmweltEntry:
    """Individual entry in an agent's Umwelt"""
    key: str
    value: Any
    timestamp: datetime
    signal_id: Optional[str] = None
    confidence: float = 1.0
    priority: UpdatePriority = UpdatePriority.MEDIUM
    ttl: Optional[int] = None  # TTL in seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL"""
        if self.ttl is None:
            return False
        
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > self.ttl
    
    def size_bytes(self) -> int:
        """Estimate size of entry in bytes"""
        return len(json.dumps({
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata
        }, default=str).encode('utf-8'))


@dataclass
class CoreObjectiveFunction:
    """Represents an agent's Core Objective Function"""
    agent_id: str
    primary_goal: str
    context_keywords: List[str] = field(default_factory=list)
    signal_filters: List[str] = field(default_factory=list)
    priority_domains: List[str] = field(default_factory=list)
    max_umwelt_size: int = 65536  # 64KB default
    refresh_interval: int = 300  # 5 minutes default
    
    @classmethod
    def from_agent_metadata(cls, agent_id: str, metadata: Dict[str, Any]) -> 'CoreObjectiveFunction':
        """Create CoF from agent metadata"""
        return cls(
            agent_id=agent_id,
            primary_goal=metadata.get('primary_goal', 'General assistance'),
            context_keywords=metadata.get('context_keywords', []),
            signal_filters=metadata.get('signal_filters', []),
            priority_domains=metadata.get('priority_domains', []),
            max_umwelt_size=metadata.get('max_umwelt_size', 65536),
            refresh_interval=metadata.get('refresh_interval', 300)
        )


class SignalProcessor:
    """Processes external signals for Umwelt updates"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.db = None  # Will be initialized lazily
    
    async def initialize(self):
        """Initialize the signal processor"""
        self.db = firestore.client()
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        logger.info("SignalProcessor initialized")
    
    async def shutdown(self):
        """Shutdown the signal processor"""
        if self.session:
            await self.session.close()
        logger.info("SignalProcessor shutdown")
    
    async def process_signal(
        self,
        signal: ExternalSignal,
        cof: CoreObjectiveFunction
    ) -> Dict[str, Any]:
        """Process a single external signal"""
        try:
            if signal.type == SignalType.API:
                return await self._process_api_signal(signal, cof)
            elif signal.type == SignalType.DATABASE:
                return await self._process_database_signal(signal, cof)
            elif signal.type == SignalType.SENSOR:
                return await self._process_sensor_signal(signal, cof)
            elif signal.type == SignalType.EVENT:
                return await self._process_event_signal(signal, cof)
            else:
                logger.warning(f"Unknown signal type: {signal.type}")
                return {}
                
        except Exception as e:
            logger.error(f"Error processing signal {signal.id}: {e}")
            return {}
    
    async def _process_api_signal(
        self,
        signal: ExternalSignal,
        cof: CoreObjectiveFunction
    ) -> Dict[str, Any]:
        """Process API-based signal"""
        if not self.session or not signal.endpoint:
            return {}
        
        try:
            async with self.session.get(
                signal.endpoint,
                params=signal.params,
                headers={'User-Agent': 'Alchemist-Umwelt/1.0'}
            ) as response:
                if response.status != 200:
                    logger.warning(f"API signal {signal.id} returned status {response.status}")
                    return {}
                
                data = await response.json()
                
                # Filter data based on CoF
                filtered_data = self._filter_by_cof(data, cof)
                
                return filtered_data
                
        except Exception as e:
            logger.error(f"Error fetching API signal {signal.id}: {e}")
            return {}
    
    async def _process_database_signal(
        self,
        signal: ExternalSignal,
        cof: CoreObjectiveFunction
    ) -> Dict[str, Any]:
        """Process database-based signal"""
        try:
            # Query Firebase based on signal configuration
            collection_ref = self.db.collection(signal.source)
            
            # Apply query filters if specified
            query = collection_ref
            if signal.query:
                # Parse and apply query filters
                # For now, just limit to recent documents
                query = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
            
            docs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(query.stream())
            )
            
            # Extract and filter data
            data = {}
            for doc in docs:
                doc_data = doc.to_dict()
                if doc_data:
                    filtered_doc = self._filter_by_cof(doc_data, cof)
                    if filtered_doc:
                        data[doc.id] = filtered_doc
            
            return data
            
        except Exception as e:
            logger.error(f"Error querying database signal {signal.id}: {e}")
            return {}
    
    async def _process_sensor_signal(
        self,
        signal: ExternalSignal,
        cof: CoreObjectiveFunction
    ) -> Dict[str, Any]:
        """Process sensor-based signal"""
        # Placeholder for sensor data processing
        # In a real implementation, this would connect to IoT devices, monitoring systems, etc.
        logger.debug(f"Processing sensor signal {signal.id}")
        return {}
    
    async def _process_event_signal(
        self,
        signal: ExternalSignal,
        cof: CoreObjectiveFunction
    ) -> Dict[str, Any]:
        """Process event-based signal"""
        try:
            # Query recent events from Firebase
            events_ref = self.db.collection('agent_events')
            query = (
                events_ref
                .where('timestamp', '>=', datetime.now() - timedelta(minutes=5))
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
                .limit(20)
            )
            
            docs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(query.stream())
            )
            
            events = {}
            for doc in docs:
                event_data = doc.to_dict()
                if event_data:
                    filtered_event = self._filter_by_cof(event_data, cof)
                    if filtered_event:
                        events[doc.id] = filtered_event
            
            return events
            
        except Exception as e:
            logger.error(f"Error processing event signal {signal.id}: {e}")
            return {}
    
    def _filter_by_cof(self, data: Dict[str, Any], cof: CoreObjectiveFunction) -> Dict[str, Any]:
        """Filter data based on Core Objective Function"""
        if not cof.context_keywords and not cof.signal_filters:
            return data
        
        filtered = {}
        
        # Convert data to string for keyword matching
        data_str = json.dumps(data, default=str).lower()
        
        # Check if any context keywords are present
        keyword_match = not cof.context_keywords or any(
            keyword.lower() in data_str for keyword in cof.context_keywords
        )
        
        # Check signal filters
        filter_match = not cof.signal_filters or any(
            filter_term.lower() in data_str for filter_term in cof.signal_filters
        )
        
        if keyword_match and filter_match:
            # Include relevant fields only
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    filtered[key] = value
                elif isinstance(value, dict) and len(filtered) < 10:  # Limit nested objects
                    nested_filtered = self._filter_by_cof(value, cof)
                    if nested_filtered:
                        filtered[key] = nested_filtered
        
        return filtered


class UmweltManager:
    """Main Umwelt management service"""
    
    def __init__(self):
        self.agent_umwelts: Dict[str, Dict[str, UmweltEntry]] = {}
        self.agent_cofs: Dict[str, CoreObjectiveFunction] = {}
        self.agent_signals: Dict[str, List[ExternalSignal]] = {}
        self.signal_processor = SignalProcessor()
        self.db = firestore.client()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialized = False
        self._background_tasks: Set[asyncio.Task] = set()
    
    async def initialize(self):
        """Initialize the Umwelt manager"""
        if self._initialized:
            return
        
        await self.signal_processor.initialize()
        
        # Start background refresh task
        refresh_task = asyncio.create_task(self._background_refresh_loop())
        self._background_tasks.add(refresh_task)
        refresh_task.add_done_callback(self._background_tasks.discard)
        
        self._initialized = True
        logger.info("UmweltManager initialized")
    
    async def shutdown(self):
        """Shutdown the Umwelt manager"""
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        await self.signal_processor.shutdown()
        self.executor.shutdown(wait=True)
        
        self._initialized = False
        logger.info("UmweltManager shutdown")
    
    async def setup_agent_umwelt(
        self,
        agent_id: str,
        agent_metadata: Dict[str, Any]
    ) -> bool:
        """
        Setup Umwelt for an agent on instantiation
        
        Args:
            agent_id: ID of the agent
            agent_metadata: Agent's goal metadata and configuration
            
        Returns:
            True if setup was successful
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Parse Core Objective Function
            cof = CoreObjectiveFunction.from_agent_metadata(agent_id, agent_metadata)
            self.agent_cofs[agent_id] = cof
            
            # Initialize empty Umwelt
            self.agent_umwelts[agent_id] = {}
            
            # Setup external signals based on CoF
            signals = await self._setup_external_signals(cof)
            self.agent_signals[agent_id] = signals
            
            # Perform initial data population
            await self._refresh_agent_umwelt(agent_id)
            
            logger.info(f"Umwelt setup completed for agent {agent_id} with {len(signals)} signals")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Umwelt for agent {agent_id}: {e}")
            return False
    
    async def _setup_external_signals(
        self,
        cof: CoreObjectiveFunction
    ) -> List[ExternalSignal]:
        """Setup external signals based on Core Objective Function"""
        signals = []
        
        # Add default system events signal
        signals.append(ExternalSignal(
            id="",
            type=SignalType.EVENT,
            source="agent_events",
            refresh_interval=60  # 1 minute for events
        ))
        
        # Add agent-specific signals based on priority domains
        for domain in cof.priority_domains:
            if domain == "conversation":
                signals.append(ExternalSignal(
                    id="",
                    type=SignalType.DATABASE,
                    source="conversations",
                    query="recent",
                    refresh_interval=120
                ))
            elif domain == "knowledge":
                signals.append(ExternalSignal(
                    id="",
                    type=SignalType.DATABASE,
                    source="knowledge_base",
                    query="updated",
                    refresh_interval=300
                ))
            elif domain == "metrics":
                signals.append(ExternalSignal(
                    id="",
                    type=SignalType.DATABASE,
                    source="agent_metrics",
                    query="recent",
                    refresh_interval=180
                ))
        
        # Add API signals for external data
        if "external_apis" in cof.priority_domains:
            # Example API signals (would be configured per deployment)
            signals.append(ExternalSignal(
                id="",
                type=SignalType.API,
                source="weather_api",
                endpoint="https://api.openweathermap.org/data/2.5/weather",
                params={"q": "San Francisco", "appid": "demo"},
                refresh_interval=1800  # 30 minutes
            ))
        
        return signals
    
    async def get_umwelt(self, agent_id: str) -> Dict[str, Any]:
        """
        Get current Umwelt for an agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Current key-value hash of Umwelt data
        """
        try:
            if agent_id not in self.agent_umwelts:
                logger.warning(f"No Umwelt found for agent {agent_id}")
                return {}
            
            umwelt = self.agent_umwelts[agent_id]
            current_time = datetime.now()
            
            # Filter out expired entries and convert to dict
            current_umwelt = {}
            for key, entry in umwelt.items():
                if not entry.is_expired():
                    current_umwelt[key] = entry.value
            
            # Check size limit
            size_bytes = len(json.dumps(current_umwelt, default=str).encode('utf-8'))
            cof = self.agent_cofs.get(agent_id)
            max_size = cof.max_umwelt_size if cof else 65536
            
            if size_bytes > max_size:
                logger.warning(f"Umwelt for agent {agent_id} exceeds size limit: {size_bytes} > {max_size}")
                # Prioritize by update priority and recency
                current_umwelt = self._trim_umwelt(current_umwelt, max_size)
            
            return current_umwelt
            
        except Exception as e:
            logger.error(f"Error getting Umwelt for agent {agent_id}: {e}")
            return {}
    
    async def update_umwelt(
        self,
        agent_id: str,
        delta: Dict[str, Any],
        priority: UpdatePriority = UpdatePriority.MEDIUM,
        source: Optional[str] = None
    ) -> bool:
        """
        Update agent's Umwelt with new observations
        
        Args:
            agent_id: ID of the agent
            delta: Dictionary of key-value updates
            priority: Priority of the update
            source: Source of the update (agent, minion, system)
            
        Returns:
            True if update was successful and fast enough
        """
        start_time = time.time()
        
        try:
            if agent_id not in self.agent_umwelts:
                logger.warning(f"No Umwelt initialized for agent {agent_id}")
                return False
            
            # Check for conflicts with GNF before applying updates
            try:
                from .umwelt_conflict_detector import get_umwelt_conflict_detector
                conflict_detector = await get_umwelt_conflict_detector()
                conflicts = await conflict_detector.check_umwelt_conflicts(agent_id, delta, priority)
                
                # Log conflicts but still apply updates (conflicts are handled separately)
                if conflicts:
                    high_severity_conflicts = [c for c in conflicts if c.severity.value in ['high', 'critical']]
                    if high_severity_conflicts:
                        logger.warning(f"High-severity Umwelt conflicts detected for agent {agent_id}: {len(high_severity_conflicts)}")
                    
            except ImportError:
                logger.debug("Umwelt conflict detector not available")
            except Exception as e:
                logger.error(f"Error checking Umwelt conflicts: {e}")
            
            umwelt = self.agent_umwelts[agent_id]
            current_time = datetime.now()
            
            # Process each delta entry
            for key, value in delta.items():
                # Create new entry
                entry = UmweltEntry(
                    key=key,
                    value=value,
                    timestamp=current_time,
                    priority=priority,
                    ttl=300,  # 5 minute default TTL
                    metadata={
                        "source": source or "agent",
                        "update_time": current_time.isoformat()
                    }
                )
                
                umwelt[key] = entry
            
            # Persist to Cognitive Memory
            await self._persist_umwelt(agent_id)
            
            # Check latency requirement
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > 5.0:
                logger.warning(f"Umwelt update for {agent_id} took {elapsed_ms:.1f}ms (>5ms)")
            
            logger.debug(f"Updated Umwelt for agent {agent_id} with {len(delta)} entries in {elapsed_ms:.1f}ms")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Umwelt for agent {agent_id}: {e}")
            return False
    
    async def _persist_umwelt(self, agent_id: str):
        """Persist Umwelt to Cognitive Memory (Firebase)"""
        try:
            umwelt = self.agent_umwelts.get(agent_id, {})
            
            # Convert to serializable format
            umwelt_data = {}
            for key, entry in umwelt.items():
                if not entry.is_expired():
                    umwelt_data[key] = {
                        "value": entry.value,
                        "timestamp": entry.timestamp,
                        "priority": entry.priority.value,
                        "metadata": entry.metadata
                    }
            
            # Store in Firebase under agent/{id}/umwelt
            doc_ref = self.db.collection('agents').document(agent_id).collection('cognitive_memory').document('umwelt')
            
            await asyncio.get_event_loop().run_in_executor(
                None, doc_ref.set, {
                    'umwelt_data': umwelt_data,
                    'last_updated': datetime.now(),
                    'agent_id': agent_id
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to persist Umwelt for agent {agent_id}: {e}")
    
    async def _refresh_agent_umwelt(self, agent_id: str):
        """Refresh an agent's Umwelt from external signals"""
        try:
            if agent_id not in self.agent_signals:
                return
            
            cof = self.agent_cofs.get(agent_id)
            if not cof:
                return
            
            signals = self.agent_signals[agent_id]
            
            # Process signals that need refresh
            current_time = datetime.now()
            tasks = []
            
            for signal in signals:
                if (signal.last_updated is None or 
                    (current_time - signal.last_updated).total_seconds() >= signal.refresh_interval):
                    
                    task = self.signal_processor.process_signal(signal, cof)
                    tasks.append((signal, task))
            
            # Execute signal processing in parallel
            if tasks:
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                
                # Update Umwelt with results
                updates = {}
                for i, (signal, _) in enumerate(tasks):
                    if isinstance(results[i], Exception):
                        logger.error(f"Signal {signal.id} failed: {results[i]}")
                        continue
                    
                    signal_data = results[i]
                    if signal_data:
                        # Prefix keys with signal type
                        for key, value in signal_data.items():
                            prefixed_key = f"{signal.type.value}_{signal.source}_{key}"
                            updates[prefixed_key] = value
                    
                    signal.last_updated = current_time
                
                # Apply updates
                if updates:
                    await self.update_umwelt(agent_id, updates, UpdatePriority.LOW, "system")
            
        except Exception as e:
            logger.error(f"Error refreshing Umwelt for agent {agent_id}: {e}")
    
    async def _background_refresh_loop(self):
        """Background loop for refreshing agent Umwelts"""
        while True:
            try:
                # Refresh all agent Umwelts
                refresh_tasks = []
                for agent_id in list(self.agent_umwelts.keys()):
                    task = self._refresh_agent_umwelt(agent_id)
                    refresh_tasks.append(task)
                
                if refresh_tasks:
                    await asyncio.gather(*refresh_tasks, return_exceptions=True)
                
                # Wait before next refresh cycle
                await asyncio.sleep(60)  # 1 minute refresh cycle
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background refresh loop: {e}")
                await asyncio.sleep(60)
    
    def _trim_umwelt(self, umwelt: Dict[str, Any], max_size: int) -> Dict[str, Any]:
        """Trim Umwelt to fit within size limit"""
        # Convert back to entries to sort by priority
        entries = []
        for key, value in umwelt.items():
            entry = UmweltEntry(key=key, value=value, timestamp=datetime.now())
            entries.append(entry)
        
        # Sort by priority and recency
        entries.sort(key=lambda e: (e.priority.value, e.timestamp), reverse=True)
        
        # Add entries until size limit
        trimmed = {}
        current_size = 0
        
        for entry in entries:
            entry_size = entry.size_bytes()
            if current_size + entry_size <= max_size:
                trimmed[entry.key] = entry.value
                current_size += entry_size
            else:
                break
        
        logger.info(f"Trimmed Umwelt from {len(umwelt)} to {len(trimmed)} entries")
        return trimmed


# Global instance
_umwelt_manager: Optional[UmweltManager] = None


async def get_umwelt_manager() -> UmweltManager:
    """Get the global Umwelt manager instance"""
    global _umwelt_manager
    if _umwelt_manager is None:
        _umwelt_manager = UmweltManager()
    if not _umwelt_manager._initialized:
        await _umwelt_manager.initialize()
    return _umwelt_manager


async def init_umwelt_service() -> UmweltManager:
    """Initialize and return the global Umwelt manager instance"""
    return await get_umwelt_manager()