"""
Query Generation Service for creating context-aware training queries
"""

import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import openai
import structlog

from app.config.settings import get_settings
from app.models import (
    GeneratedQuery, AgentContext, QuerySettings, QueryDifficulty, QueryCategory
)
from app.services.firebase_service import FirebaseService

logger = structlog.get_logger(__name__)


class QueryGenerationService:
    """Service for generating context-aware training queries"""
    
    def __init__(self):
        self.settings = get_settings()
        self.firebase_service = FirebaseService()
        self.openai_client: Optional[openai.AsyncOpenAI] = None
        self._initialized = False
        
        # Query templates for fallback
        self.fallback_templates = {
            QueryCategory.GENERAL: [
                "Hi! I'm new to your service. Can you help me understand what you do?",
                "Hello, I'd like to learn more about your platform.",
                "What services do you offer and how can they help my business?",
                "I'm interested in your solution. Can you give me an overview?",
                "Could you explain how your platform works?",
                "What makes your service different from others?",
                "I'm evaluating different options. Why should I choose you?",
                "Can you walk me through your main features?"
            ],
            QueryCategory.SUPPORT: [
                "I'm having trouble logging into my account. Can you help?",
                "My dashboard isn't loading properly. What should I do?",
                "I forgot my password and the reset isn't working.",
                "I'm getting an error message. How do I fix this?",
                "The app keeps crashing when I try to access my data.",
                "I can't find the feature I need. Where is it located?",
                "Something seems broken on my account. Can you check it?",
                "I need help troubleshooting a technical issue."
            ],
            QueryCategory.PRICING: [
                "What are your pricing plans and what's included?",
                "How much does it cost for a small business like mine?",
                "Do you offer any discounts for annual subscriptions?",
                "What's the difference between your pricing tiers?",
                "Is there a free trial available?",
                "Can I upgrade or downgrade my plan later?",
                "Are there any hidden fees I should know about?",
                "What happens if I exceed my plan limits?"
            ],
            QueryCategory.FEATURES: [
                "Does your platform integrate with Slack?",
                "Can I export my data in different formats?",
                "Do you have an API I can use for custom integrations?",
                "What reporting and analytics features do you offer?",
                "Is there a mobile app available?",
                "Can multiple team members access the same account?",
                "Do you support single sign-on (SSO)?",
                "What automation features are available?"
            ]
        }
    
    async def initialize(self):
        """Initialize the query generation service"""
        if self._initialized:
            return
        
        try:
            # Initialize Firebase service
            await self.firebase_service.initialize()
            
            # Initialize OpenAI client
            if self.settings.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(
                    api_key=self.settings.openai_api_key,
                    organization=self.settings.openai_organization,
                    base_url=self.settings.openai_base_url
                )
            
            self._initialized = True
            logger.info("Query generation service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize query generation service", error=str(e))
            raise
    
    def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            raise RuntimeError("Query generation service not initialized. Call initialize() first.")
    
    async def generate_queries(
        self, 
        agent_context: AgentContext, 
        query_settings: QuerySettings
    ) -> List[GeneratedQuery]:
        """Generate contextual training queries"""
        self._ensure_initialized()
        
        try:
            # Try AI-powered generation first
            if self.openai_client:
                queries = await self._generate_ai_queries(agent_context, query_settings)
            else:
                # Fallback to template-based generation
                queries = self._generate_template_queries(agent_context, query_settings)
            
            logger.info(
                "Generated queries",
                agent_id=agent_context.agent_id,
                count=len(queries),
                method="ai" if self.openai_client else "template"
            )
            
            return queries
            
        except Exception as e:
            logger.error("Query generation failed, using fallback", error=str(e))
            # Always provide fallback queries
            return self._generate_template_queries(agent_context, query_settings)
    
    async def _generate_ai_queries(
        self, 
        agent_context: AgentContext, 
        query_settings: QuerySettings
    ) -> List[GeneratedQuery]:
        """Generate queries using OpenAI"""
        
        # Build context-aware prompt
        system_prompt = self._build_system_prompt(agent_context, query_settings)
        user_prompt = self._build_user_prompt(agent_context, query_settings)
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            queries_data = json.loads(content)
            
            # Convert to GeneratedQuery objects
            queries = []
            for item in queries_data.get("queries", []):
                query = GeneratedQuery(
                    query=item["query"],
                    expected_response_type=item.get("expected_response_type", "informational"),
                    difficulty=QueryDifficulty(item.get("difficulty", "medium")),
                    category=QueryCategory(item.get("category", "general")),
                    context=item.get("context"),
                    metadata={
                        "generation_method": "ai",
                        "confidence": item.get("confidence", 0.8),
                        "generated_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                queries.append(query)
            
            return queries[:query_settings.count]  # Limit to requested count
            
        except Exception as e:
            logger.warning("AI query generation failed", error=str(e))
            raise
    
    def _generate_template_queries(
        self, 
        agent_context: AgentContext, 
        query_settings: QuerySettings
    ) -> List[GeneratedQuery]:
        """Generate queries using templates (fallback method)"""
        
        queries = []
        available_categories = list(self.fallback_templates.keys())
        
        # Filter categories if specified
        if query_settings.categories:
            available_categories = [cat for cat in available_categories if cat in query_settings.categories]
        
        # Generate queries
        for i in range(query_settings.count):
            category = random.choice(available_categories)
            template = random.choice(self.fallback_templates[category])
            
            # Add context-specific variations
            query_text = self._contextualize_template(template, agent_context)
            
            # Determine difficulty
            difficulty = self._determine_difficulty(query_settings.difficulty, i)
            
            query = GeneratedQuery(
                query=query_text,
                expected_response_type="informational",
                difficulty=difficulty,
                category=category,
                context=f"{agent_context.domain or 'general'} - {agent_context.business_type or 'business'}",
                metadata={
                    "generation_method": "template",
                    "template_used": template,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            )
            queries.append(query)
        
        return queries
    
    def _contextualize_template(self, template: str, agent_context: AgentContext) -> str:
        """Add context-specific variations to template"""
        
        # Simple contextualization based on domain
        if agent_context.domain:
            domain_variations = {
                "customer support": "customer service",
                "e-commerce": "online store",
                "healthcare": "medical services",
                "finance": "financial services",
                "education": "learning platform"
            }
            
            # Replace generic terms with domain-specific ones
            for generic, specific in domain_variations.items():
                if agent_context.domain.lower() in generic:
                    template = template.replace("service", specific).replace("platform", specific)
                    break
        
        # Add business context
        if agent_context.business_type:
            if "small business" in template.lower() and agent_context.business_type:
                template = template.replace("small business", agent_context.business_type)
        
        return template
    
    def _determine_difficulty(self, setting: QueryDifficulty, index: int) -> QueryDifficulty:
        """Determine difficulty for a query based on settings"""
        if setting == QueryDifficulty.MIXED:
            # Distribute difficulties evenly
            difficulties = [QueryDifficulty.EASY, QueryDifficulty.MEDIUM, QueryDifficulty.HARD]
            return difficulties[index % len(difficulties)]
        else:
            return setting
    
    def _build_system_prompt(self, agent_context: AgentContext, query_settings: QuerySettings) -> str:
        """Build system prompt for AI query generation"""
        return f"""You are an expert at generating realistic user queries for AI agent training.

Your task is to create {query_settings.count} contextual user queries that would be asked to an AI agent in the {agent_context.domain or 'general business'} domain.

Agent Context:
- Domain: {agent_context.domain or 'General business'}
- Business Type: {agent_context.business_type or 'Various'}
- Target Audience: {agent_context.target_audience or 'General users'}
- Tone: {agent_context.tone}

Query Requirements:
- Difficulty: {query_settings.difficulty.value}
- Categories: {[cat.value for cat in query_settings.categories] if query_settings.categories else 'All categories'}
- Include realistic user context and scenarios
- Vary the complexity and specificity
- Make queries sound natural and conversational

Respond with a JSON object in this format:
{{
  "queries": [
    {{
      "query": "The actual user query text",
      "expected_response_type": "informational|troubleshooting|sales|support",
      "difficulty": "easy|medium|hard",
      "category": "general|support|pricing|features|billing|compliance|urgent|sales",
      "context": "Brief context about the user scenario",
      "confidence": 0.9
    }}
  ]
}}"""
    
    def _build_user_prompt(self, agent_context: AgentContext, query_settings: QuerySettings) -> str:
        """Build user prompt for AI query generation"""
        prompt = f"Generate {query_settings.count} realistic user queries for this AI agent."
        
        if agent_context.knowledge_base_summary:
            prompt += f"\n\nAgent's knowledge base includes: {agent_context.knowledge_base_summary[:500]}"
        
        if agent_context.existing_responses:
            prompt += f"\n\nAgent has previously handled queries like: {', '.join(agent_context.existing_responses[:3])}"
        
        return prompt
    
    async def analyze_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """Analyze an agent to extract context for query generation"""
        self._ensure_initialized()
        
        try:
            # In a real implementation, this would analyze the agent's:
            # - Knowledge base
            # - Previous conversations
            # - Configuration
            # - Performance metrics
            
            # For now, return a basic context
            context = {
                "agent_id": agent_id,
                "domain": "customer support",  # Would be extracted from agent config
                "business_type": "software company",  # Would be inferred
                "target_audience": "business users",
                "tone": "professional and helpful",
                "knowledge_base_summary": "The agent handles customer inquiries about software features, troubleshooting, and account management.",
                "confidence": 0.7,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info("Agent context analyzed", agent_id=agent_id)
            return context
            
        except Exception as e:
            logger.error("Failed to analyze agent context", agent_id=agent_id, error=str(e))
            raise