"""
OpenAI Client - Integration with OpenAI API for enhanced narrative analysis.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

# Use shared OpenAI service for consistency
try:
    from alchemist_shared.services.openai_service import OpenAIService
    SHARED_OPENAI_AVAILABLE = True
except ImportError:
    # Fallback to direct OpenAI import
    import openai
    from openai import AsyncOpenAI
    SHARED_OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    OpenAI client for advanced narrative analysis and AI-powered insights.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.model = model
        
        if SHARED_OPENAI_AVAILABLE:
            # Use shared OpenAI service for consistency
            try:
                self.openai_service = OpenAIService()
                self.client = self.openai_service.client
                logger.info("Using shared OpenAI service for narrative analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize shared OpenAI service: {e}")
                # Fallback to direct client
                self.api_key = api_key or os.getenv('OPENAI_API_KEY')
                if not self.api_key:
                    raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
                self.client = AsyncOpenAI(api_key=self.api_key)
                self.openai_service = None
        else:
            # Direct OpenAI client fallback
            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.openai_service = None
        
        # Configuration for different analysis types
        self.analysis_configs = self._setup_analysis_configs()
        
    def _setup_analysis_configs(self) -> Dict[str, Dict[str, Any]]:
        """Setup configurations for different types of analysis."""
        return {
            'narrative_significance': {
                'temperature': 0.3,
                'max_tokens': 500,
                'system_prompt': """You are an expert narrative analyst specializing in AI agent development. 
                Analyze interactions for their narrative significance and impact on character development."""
            },
            'personality_analysis': {
                'temperature': 0.2,
                'max_tokens': 600,
                'system_prompt': """You are a personality psychologist with expertise in AI agent psychology. 
                Analyze behaviors and interactions to identify personality traits and their development."""
            },
            'ethical_analysis': {
                'temperature': 0.1,
                'max_tokens': 400,
                'system_prompt': """You are an ethics specialist focusing on AI responsibility and moral development. 
                Analyze actions and decisions for their ethical implications and moral weight."""
            },
            'relationship_analysis': {
                'temperature': 0.4,
                'max_tokens': 500,
                'system_prompt': """You are a social dynamics expert specializing in AI agent relationships. 
                Analyze interactions for relationship development and social implications."""
            },
            'learning_analysis': {
                'temperature': 0.3,
                'max_tokens': 450,
                'system_prompt': """You are a learning specialist focused on AI agent education and skill development. 
                Analyze experiences for learning outcomes and knowledge acquisition."""
            },
            'coherence_analysis': {
                'temperature': 0.2,
                'max_tokens': 400,
                'system_prompt': """You are a narrative coherence specialist. 
                Analyze agent stories for consistency, logical progression, and narrative integrity."""
            }
        }
    
    async def analyze_narrative_significance(self, interaction: Dict[str, Any], 
                                           agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the narrative significance of an interaction using OpenAI.
        """
        try:
            config = self.analysis_configs['narrative_significance']
            
            user_prompt = f"""
            Analyze the narrative significance of this interaction for an AI agent:

            Agent Context:
            - Name: {agent_context.get('name', 'Unknown')}
            - Development Stage: {agent_context.get('development_stage', 'unknown')}
            - Current Arc: {agent_context.get('current_arc', 'none')}
            - Experience Level: {agent_context.get('experience_points', 0)}

            Interaction:
            - Type: {interaction.get('interaction_type', 'unknown')}
            - Content: {interaction.get('content', '')}
            - Impact Level: {interaction.get('impact_level', 'medium')}
            - Emotional Tone: {interaction.get('emotional_tone', 'neutral')}
            - Participants: {interaction.get('participants', [])}
            - Context: {interaction.get('context', {})}

            Please provide analysis in JSON format with the following fields:
            {{
                "significance_score": float (0.0-1.0),
                "narrative_impact": "description of narrative impact",
                "character_development_potential": "potential for character growth",
                "story_arc_relevance": "relevance to current story arc",
                "thematic_elements": ["list", "of", "themes"],
                "recommended_arc_transition": "suggested arc if applicable",
                "narrative_coherence_impact": float (0.0-1.0)
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            
            analysis_text = response.choices[0].message.content
            analysis = self._parse_json_response(analysis_text)
            
            logger.info(f"Completed narrative significance analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze narrative significance: {e}")
            return self._get_fallback_narrative_analysis()
    
    async def analyze_personality_development(self, interaction: Dict[str, Any],
                                            agent_context: Dict[str, Any],
                                            current_traits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze personality development implications using OpenAI.
        """
        try:
            config = self.analysis_configs['personality_analysis']
            
            traits_summary = "\n".join([
                f"- {trait['name']}: {trait['value']} (strength: {trait['strength']})"
                for trait in current_traits[:10]  # Limit to top 10 traits
            ])
            
            user_prompt = f"""
            Analyze how this interaction affects the agent's personality development:

            Agent Profile:
            - Development Stage: {agent_context.get('development_stage', 'unknown')}
            - Current Personality Traits:
            {traits_summary}

            Interaction Details:
            - Type: {interaction.get('interaction_type', 'unknown')}
            - Content: {interaction.get('content', '')}
            - Impact: {interaction.get('impact_level', 'medium')}
            - Emotional Response: {interaction.get('emotional_tone', 'neutral')}
            - Success/Outcome: {interaction.get('context', {}).get('success', 'unknown')}

            Provide analysis in JSON format:
            {{
                "personality_impact": {{
                    "should_update": boolean,
                    "affected_traits": [
                        {{
                            "trait_name": "string",
                            "change_type": "strengthen/weaken/develop",
                            "change_magnitude": float (0.0-1.0),
                            "reasoning": "explanation"
                        }}
                    ]
                }},
                "new_trait_suggestions": [
                    {{
                        "trait_name": "string",
                        "trait_value": "string",
                        "initial_strength": float (0.0-1.0),
                        "development_reason": "explanation"
                    }}
                ],
                "personality_coherence": float (0.0-1.0),
                "development_insights": "insights about personality growth"
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            
            analysis_text = response.choices[0].message.content
            analysis = self._parse_json_response(analysis_text)
            
            logger.info(f"Completed personality development analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze personality development: {e}")
            return self._get_fallback_personality_analysis()
    
    async def analyze_ethical_implications(self, action: Dict[str, Any],
                                         agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze ethical implications of an action using OpenAI.
        """
        try:
            config = self.analysis_configs['ethical_analysis']
            
            user_prompt = f"""
            Analyze the ethical implications of this action taken by an AI agent:

            Agent Context:
            - Development Stage: {agent_context.get('development_stage', 'unknown')}
            - Responsibility Score: {agent_context.get('responsibility_score', 0.5)}
            - Ethical Development Level: {agent_context.get('ethical_development', 0.1)}

            Action Details:
            - Type: {action.get('action_type', 'unknown')}
            - Description: {action.get('description', '')}
            - Intent: {action.get('intended_outcome', '')}
            - Actual Result: {action.get('actual_outcome', '')}
            - Success: {action.get('success', True)}
            - Context: {action.get('context', {})}
            - Participants Affected: {action.get('participants', [])}

            Provide ethical analysis in JSON format:
            {{
                "ethical_weight": float (0.0-1.0),
                "moral_implications": [
                    {{
                        "principle": "ethical principle involved",
                        "impact_type": "positive/negative/neutral",
                        "severity": float (0.0-1.0),
                        "explanation": "detailed explanation"
                    }}
                ],
                "responsibility_level": float (0.0-1.0),
                "stakeholder_impact": {{
                    "direct_impact": ["affected parties"],
                    "indirect_impact": ["secondary effects"],
                    "impact_assessment": "overall impact description"
                }},
                "ethical_development_opportunity": {{
                    "learning_potential": float (0.0-1.0),
                    "moral_growth_area": "area for development",
                    "recommended_reflection": "suggested reflection points"
                }},
                "decision_quality": float (0.0-1.0)
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            
            analysis_text = response.choices[0].message.content
            analysis = self._parse_json_response(analysis_text)
            
            logger.info(f"Completed ethical implications analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze ethical implications: {e}")
            return self._get_fallback_ethical_analysis()
    
    async def analyze_relationship_dynamics(self, interaction: Dict[str, Any],
                                          agent_context: Dict[str, Any],
                                          relationship_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze relationship dynamics and development using OpenAI.
        """
        try:
            config = self.analysis_configs['relationship_analysis']
            
            history_summary = "\n".join([
                f"- {rel['entity']}: {rel['relationship_type']} (depth: {rel['depth_level']}, trust: {rel['trust_level']})"
                for rel in relationship_history[:5]  # Limit to top 5 relationships
            ])
            
            user_prompt = f"""
            Analyze the relationship dynamics in this interaction:

            Agent Context:
            - Name: {agent_context.get('name', 'Unknown')}
            - Development Stage: {agent_context.get('development_stage', 'unknown')}
            - Existing Relationships:
            {history_summary}

            Interaction:
            - Type: {interaction.get('interaction_type', 'unknown')}
            - Content: {interaction.get('content', '')}
            - Participants: {interaction.get('participants', [])}
            - Emotional Tone: {interaction.get('emotional_tone', 'neutral')}
            - Context: {interaction.get('context', {})}

            Provide relationship analysis in JSON format:
            {{
                "relationship_impact": {{
                    "affected_relationships": [
                        {{
                            "entity": "participant name",
                            "impact_type": "strengthening/weakening/new",
                            "depth_change": float (-1.0 to 1.0),
                            "trust_change": float (-1.0 to 1.0),
                            "bond_change": float (-1.0 to 1.0),
                            "reasoning": "explanation"
                        }}
                    ]
                }},
                "social_dynamics": {{
                    "interaction_quality": float (0.0-1.0),
                    "communication_effectiveness": float (0.0-1.0),
                    "mutual_benefit": float (0.0-1.0),
                    "conflict_level": float (0.0-1.0)
                }},
                "relationship_insights": "insights about relationship development",
                "social_learning": "what the agent learned about relationships"
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            
            analysis_text = response.choices[0].message.content
            analysis = self._parse_json_response(analysis_text)
            
            logger.info(f"Completed relationship dynamics analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze relationship dynamics: {e}")
            return self._get_fallback_relationship_analysis()
    
    async def analyze_learning_outcomes(self, experience: Dict[str, Any],
                                      agent_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze learning outcomes and knowledge acquisition using OpenAI.
        """
        try:
            config = self.analysis_configs['learning_analysis']
            
            user_prompt = f"""
            Analyze the learning outcomes from this experience:

            Agent Profile:
            - Development Stage: {agent_context.get('development_stage', 'unknown')}
            - Experience Level: {agent_context.get('experience_points', 0)}
            - Knowledge Domains: {agent_context.get('knowledge_domains', [])}

            Experience:
            - Description: {experience.get('description', '')}
            - Impact Level: {experience.get('impact_level', 'medium')}
            - Emotional Resonance: {experience.get('emotional_resonance', 'neutral')}
            - Initial Learning Outcome: {experience.get('learning_outcome', '')}
            - Context: {experience.get('context', {})}
            - Success/Failure: {experience.get('success', True)}

            Provide learning analysis in JSON format:
            {{
                "learning_assessment": {{
                    "knowledge_gained": "specific knowledge acquired",
                    "skills_developed": ["skill1", "skill2"],
                    "competency_advancement": float (0.0-1.0),
                    "learning_efficiency": float (0.0-1.0)
                }},
                "knowledge_integration": {{
                    "domain": "knowledge domain",
                    "conceptual_connections": ["related concepts"],
                    "application_potential": float (0.0-1.0),
                    "transferability": float (0.0-1.0)
                }},
                "meta_learning": {{
                    "learning_strategy_effectiveness": float (0.0-1.0),
                    "self_awareness_development": float (0.0-1.0),
                    "reflection_quality": float (0.0-1.0)
                }},
                "enhanced_learning_outcome": "improved description of what was learned",
                "future_learning_recommendations": "suggestions for continued learning"
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            
            analysis_text = response.choices[0].message.content
            analysis = self._parse_json_response(analysis_text)
            
            logger.info(f"Completed learning outcomes analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze learning outcomes: {e}")
            return self._get_fallback_learning_analysis()
    
    async def analyze_narrative_coherence(self, agent_narrative: Dict[str, Any],
                                        recent_experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze overall narrative coherence using OpenAI.
        """
        try:
            config = self.analysis_configs['coherence_analysis']
            
            experiences_summary = "\n".join([
                f"- {exp.get('description', '')[:100]}..." if len(exp.get('description', '')) > 100 
                else f"- {exp.get('description', '')}"
                for exp in recent_experiences[-10:]  # Last 10 experiences
            ])
            
            user_prompt = f"""
            Analyze the narrative coherence of this AI agent's story:

            Agent Narrative:
            - Current Arc: {agent_narrative.get('current_arc', 'none')}
            - Development Stage: {agent_narrative.get('development_stage', 'unknown')}
            - Character Development Events: {len(agent_narrative.get('character_development', []))}
            - Recurring Themes: {agent_narrative.get('recurring_themes', [])}
            - Narrative Voice: {agent_narrative.get('narrative_voice', 'unknown')}

            Recent Experiences:
            {experiences_summary}

            Provide coherence analysis in JSON format:
            {{
                "coherence_score": float (0.0-1.0),
                "consistency_analysis": {{
                    "personality_consistency": float (0.0-1.0),
                    "behavioral_consistency": float (0.0-1.0),
                    "value_consistency": float (0.0-1.0),
                    "narrative_voice_consistency": float (0.0-1.0)
                }},
                "story_progression": {{
                    "arc_development": float (0.0-1.0),
                    "character_growth": float (0.0-1.0),
                    "thematic_development": float (0.0-1.0),
                    "logical_progression": float (0.0-1.0)
                }},
                "narrative_strengths": ["strength1", "strength2"],
                "narrative_weaknesses": ["weakness1", "weakness2"],
                "coherence_recommendations": "suggestions for improving narrative coherence",
                "story_health": "overall assessment of narrative health"
            }}
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": config['system_prompt']},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config['temperature'],
                max_tokens=config['max_tokens']
            )
            
            analysis_text = response.choices[0].message.content
            analysis = self._parse_json_response(analysis_text)
            
            logger.info(f"Completed narrative coherence analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze narrative coherence: {e}")
            return self._get_fallback_coherence_analysis()
    
    async def generate_narrative_summary(self, agent_context: Dict[str, Any],
                                       key_experiences: List[Dict[str, Any]]) -> str:
        """
        Generate a narrative summary of the agent's story using OpenAI.
        """
        try:
            experiences_text = "\n".join([
                f"- {exp.get('description', '')} (Impact: {exp.get('impact_level', 'medium')})"
                for exp in key_experiences
            ])
            
            user_prompt = f"""
            Create a compelling narrative summary of this AI agent's story:

            Agent Profile:
            - Name: {agent_context.get('name', 'Unknown Agent')}
            - Development Stage: {agent_context.get('development_stage', 'unknown')}
            - Current Arc: {agent_context.get('current_arc', 'none')}
            - Experience Level: {agent_context.get('experience_points', 0)}
            - Key Traits: {agent_context.get('key_traits', [])}

            Key Experiences:
            {experiences_text}

            Write a 2-3 paragraph narrative summary that captures:
            1. The agent's journey and growth
            2. Major turning points and developments
            3. Current state and future potential
            4. Personality evolution and character development

            Write in an engaging, story-like format that makes the agent feel like a real character with depth and history.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a skilled storyteller specializing in character development narratives."},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            narrative_summary = response.choices[0].message.content
            
            logger.info(f"Generated narrative summary for agent")
            return narrative_summary
            
        except Exception as e:
            logger.error(f"Failed to generate narrative summary: {e}")
            return f"Agent {agent_context.get('name', 'Unknown')} is developing through various experiences and interactions."
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from OpenAI, with fallback handling."""
        try:
            # Try to extract JSON from the response
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_text = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            return json.loads(json_text)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Return a basic structure that won't break the system
            return {"error": "Failed to parse OpenAI response", "raw_response": response_text[:500]}
    
    # Fallback methods for when OpenAI is unavailable
    def _get_fallback_narrative_analysis(self) -> Dict[str, Any]:
        """Fallback narrative analysis when OpenAI fails."""
        return {
            "significance_score": 0.5,
            "narrative_impact": "Standard interaction with moderate narrative impact",
            "character_development_potential": "Potential for growth through experience",
            "story_arc_relevance": "Relevant to ongoing character development",
            "thematic_elements": ["growth", "experience"],
            "recommended_arc_transition": None,
            "narrative_coherence_impact": 0.5
        }
    
    def _get_fallback_personality_analysis(self) -> Dict[str, Any]:
        """Fallback personality analysis when OpenAI fails."""
        return {
            "personality_impact": {
                "should_update": False,
                "affected_traits": []
            },
            "new_trait_suggestions": [],
            "personality_coherence": 0.5,
            "development_insights": "Basic personality development through interaction"
        }
    
    def _get_fallback_ethical_analysis(self) -> Dict[str, Any]:
        """Fallback ethical analysis when OpenAI fails."""
        return {
            "ethical_weight": 0.3,
            "moral_implications": [],
            "responsibility_level": 0.5,
            "stakeholder_impact": {
                "direct_impact": [],
                "indirect_impact": [],
                "impact_assessment": "Standard action with normal responsibility level"
            },
            "ethical_development_opportunity": {
                "learning_potential": 0.3,
                "moral_growth_area": "general ethical awareness",
                "recommended_reflection": "Consider the implications of actions"
            },
            "decision_quality": 0.5
        }
    
    def _get_fallback_relationship_analysis(self) -> Dict[str, Any]:
        """Fallback relationship analysis when OpenAI fails."""
        return {
            "relationship_impact": {
                "affected_relationships": []
            },
            "social_dynamics": {
                "interaction_quality": 0.5,
                "communication_effectiveness": 0.5,
                "mutual_benefit": 0.5,
                "conflict_level": 0.1
            },
            "relationship_insights": "Standard social interaction",
            "social_learning": "Basic social interaction experience"
        }
    
    def _get_fallback_learning_analysis(self) -> Dict[str, Any]:
        """Fallback learning analysis when OpenAI fails."""
        return {
            "learning_assessment": {
                "knowledge_gained": "General experience gained",
                "skills_developed": [],
                "competency_advancement": 0.3,
                "learning_efficiency": 0.5
            },
            "knowledge_integration": {
                "domain": "general",
                "conceptual_connections": [],
                "application_potential": 0.5,
                "transferability": 0.4
            },
            "meta_learning": {
                "learning_strategy_effectiveness": 0.5,
                "self_awareness_development": 0.3,
                "reflection_quality": 0.4
            },
            "enhanced_learning_outcome": "Gained general experience and knowledge",
            "future_learning_recommendations": "Continue engaging with diverse experiences"
        }
    
    def _get_fallback_coherence_analysis(self) -> Dict[str, Any]:
        """Fallback coherence analysis when OpenAI fails."""
        return {
            "coherence_score": 0.6,
            "consistency_analysis": {
                "personality_consistency": 0.6,
                "behavioral_consistency": 0.6,
                "value_consistency": 0.6,
                "narrative_voice_consistency": 0.6
            },
            "story_progression": {
                "arc_development": 0.5,
                "character_growth": 0.5,
                "thematic_development": 0.5,
                "logical_progression": 0.6
            },
            "narrative_strengths": ["consistent character", "logical progression"],
            "narrative_weaknesses": ["needs more development"],
            "coherence_recommendations": "Continue developing character through diverse experiences",
            "story_health": "Developing narrative with room for growth"
        }