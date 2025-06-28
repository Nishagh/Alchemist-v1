# Story-First Microservices Architecture for Alchemist

## Overview

This architecture maintains the benefits of microservices while ensuring coherent agent life-stories through a centralized "Narrative Spine."

## Architecture Components

### 1. Narrative Spine (Google Cloud Spanner Graph)
**Purpose**: Single source of truth for all agent stories
**Technology**: Google Cloud Spanner Graph with eA³ orchestrator
**Responsibilities**:
- Store complete agent life-stories with CNE (Coherent Narrative Exclusivity)
- Handle RbR (Recursive Belief Revision) when contradictions arise
- Provide GPT-4.1 enhanced narrative coherence analysis
- Maintain causal relationships between events

### 2. Service-Specific Databases (Local State)
**Purpose**: Optimize performance for service-specific operations
**Examples**:
- Agent Engine: Firestore for conversation history
- Knowledge Vault: Firestore for file metadata and embeddings
- Prompt Engine: Firestore for prompt templates and versions

### 3. Story Event Bus (Cloud Pub/Sub)
**Purpose**: Async communication between services and narrative spine
**Flow**:
```
Service → Story Event → Pub/Sub → eA³ Orchestrator → Spanner Graph
```

## Data Flow Patterns

### Pattern 1: Write-Through Story Events
```
1. Service performs operation (e.g., file upload)
2. Service writes to local database
3. Service publishes story event to Pub/Sub
4. eA³ Orchestrator receives event
5. GPT-4.1 enhanced processing creates narrative entry
6. Story event added to Spanner Graph
7. Coherence check triggered if needed
```

### Pattern 2: Read-Through Story Context
```
1. Service needs agent context
2. Check local cache first
3. If cache miss, query Narrative Spine
4. eA³ Orchestrator provides enriched context
5. Cache result locally with TTL
```

### Pattern 3: Conflict Resolution (RbR)
```
1. New event contradicts existing story
2. eA³ Orchestrator detects contradiction
3. GPT-4.1 analyzes entire narrative
4. Recursive Belief Revision triggered
5. All affected services notified
6. Local caches invalidated
7. Services fetch updated context
```

## Service Integration Patterns

### Agent Engine Integration
```python
class ConversationHandler:
    async def process_conversation(self, user_msg, agent_response):
        # 1. Store in local Firestore
        conv_id = await self.store_conversation(user_msg, agent_response)
        
        # 2. Create story event
        story_event = StoryEvent(
            agent_id=self.agent_id,
            event_type="CONVERSATION",
            content=f"Conversation: {user_msg} -> {agent_response}",
            source_service="agent-engine",
            local_reference=conv_id
        )
        
        # 3. Publish to story spine
        await self.story_publisher.publish(story_event)
        
        # 4. Get enhanced context for next interaction
        agent_context = await self.get_story_context()
        return conv_id, agent_context
```

### Knowledge Vault Integration
```python
class FileProcessor:
    async def process_file(self, file, agent_id):
        # 1. Process and store file locally
        file_data = await self.index_file(file, agent_id)
        
        # 2. Generate GPT-4.1 enhanced narrative
        narrative = await self.generate_knowledge_narrative(file_data)
        
        # 3. Create story event
        story_event = StoryEvent(
            agent_id=agent_id,
            event_type="KNOWLEDGE_ACQUISITION",
            content=narrative,
            source_service="knowledge-vault",
            metadata={"file_id": file_data.id, "quality_score": file_data.quality}
        )
        
        # 4. Publish to story spine
        await self.story_publisher.publish(story_event)
```

## Benefits of This Architecture

### ✅ **Maintains Microservices Advantages**
- Services remain independently deployable
- Technology diversity preserved
- Clear service boundaries

### ✅ **Ensures Story Coherence**
- Single source of truth for agent narratives
- GPT-4.1 enhanced coherence checking
- Automatic conflict resolution

### ✅ **Performance Optimized**
- Local caches for frequent operations
- Async story updates don't block operations
- Smart cache invalidation

### ✅ **Scalable & Resilient**
- Pub/Sub handles high event volumes
- Services can operate temporarily without story spine
- Eventual consistency with conflict resolution

## Migration Strategy

### Phase 1: Add Story Spine (Current Implementation)
- ✅ Deploy Spanner Graph database
- ✅ Implement eA³ orchestrator with GPT-4.1
- ✅ Direct integration in agent-engine and knowledge-vault

### Phase 2: Add Event Bus
- Implement Cloud Pub/Sub for story events
- Add async story event publishing to existing services
- Maintain backward compatibility

### Phase 3: Add Local Caching
- Implement story context caching in each service
- Add cache invalidation on story updates
- Performance optimization

### Phase 4: Advanced Features
- Cross-service story queries
- Predictive context pre-loading
- Advanced narrative analytics

## Implementation Guidelines

### Story Event Schema
```python
@dataclass
class StoryEvent:
    agent_id: str
    event_type: StoryEventType
    content: str
    source_service: str
    timestamp: datetime
    confidence: float
    metadata: Dict[str, Any]
    local_reference: Optional[str]  # Reference to local storage
    causal_parents: List[str] = field(default_factory=list)
```

### Service Requirements
1. **Publish story events** for significant agent interactions
2. **Subscribe to story updates** relevant to their domain
3. **Cache story context** locally for performance
4. **Handle cache invalidation** on story changes

### Monitoring & Observability
- Story event volume and latency metrics
- Coherence score trends over time
- Cross-service story correlation
- Cache hit rates and invalidation patterns

## Conclusion

This architecture gives you the best of both worlds:
- **Microservices flexibility** for development and scaling
- **Coherent agent stories** through centralized narrative tracking
- **High performance** through intelligent caching
- **GPT-4.1 enhanced intelligence** for narrative coherence

The key insight is treating agent stories as a **first-class architectural concern** rather than an afterthought.