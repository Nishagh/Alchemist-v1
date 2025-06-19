#!/usr/bin/env python3
"""
Universal Agent Configuration Loader

This module dynamically loads agent configuration from Firestore and applies
LLM-based optimizations for any type of agent.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AgentConfigLoader:
    """Loads and optimizes agent configuration dynamically from Firestore."""
    
    def __init__(self):
        """Initialize the configuration loader with Firebase."""
        # Load from .env file first
        load_dotenv()
        
        # Use hardcoded project ID
        self.project_id = "alchemist-e69bb"
        
        self._init_firebase()
        self._optimization_cache = {}
    
    def _init_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            self.firebase_app = firebase_admin.get_app()
            logger.info("Using existing Firebase app")
        except ValueError:
            # Try multiple paths for Firebase credentials
            firebase_creds_paths = [
                'firebase-credentials.json',  # Local directory
                os.getenv('FIREBASE_CREDENTIALS', ''),
                os.getenv('firebase_credentials', ''),
                os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
            ]
            
            firebase_initialized = False
            for creds_path in firebase_creds_paths:
                if creds_path and os.path.exists(creds_path):
                    try:
                        cred = credentials.Certificate(creds_path)
                        self.firebase_app = firebase_admin.initialize_app(
                            cred, 
                            {'projectId': self.project_id}
                        )
                        logger.info(f"Initialized Firebase with credentials: {creds_path}")
                        firebase_initialized = True
                        break
                    except Exception as e:
                        logger.warning(f"Failed to initialize Firebase with {creds_path}: {str(e)}")
                        continue
            
            if not firebase_initialized:
                self.firebase_app = firebase_admin.initialize_app()
                logger.info("Initialized Firebase with Application Default Credentials")
        
        self.db = firestore.client(self.firebase_app)
    
    def load_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """
        Load complete agent configuration from Firestore.
        
        Args:
            agent_id: The agent ID to load
            
        Returns:
            Complete agent configuration with optimizations applied
        """
        try:
            logger.info(f"Loading configuration for agent: {agent_id}")
            
            # Fetch base configuration from Firestore
            agent_ref = self.db.collection('alchemist_agents').document(agent_id)
            agent_doc = agent_ref.get()
            
            if not agent_doc.exists:
                raise ValueError(f"Agent {agent_id} not found in Firestore")
            
            base_config = agent_doc.to_dict()
            logger.info(f"Loaded base config for agent: {agent_id}")
            
            # Add runtime configuration
            base_config.update({
                'agent_id': agent_id,
                'firebase_project_id': self.project_id,
                'openai_api_key': os.getenv('OPENAI_API_KEY') or os.getenv('openai_api_key', ''),
            })
            
            # Extract MCP server URL if available
            if 'api_integration' in base_config and 'service_url' in base_config['api_integration']:
                base_config['mcp_server_url'] = base_config['api_integration']['service_url']
            
            # Apply LLM-based optimizations
            optimized_config = self._apply_llm_optimizations(base_config)
            
            logger.info(f"Configuration loaded and optimized for agent: {agent_id}")
            return optimized_config
            
        except Exception as e:
            logger.error(f"Error loading agent config: {str(e)}")
            raise
    
    def _apply_llm_optimizations(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply LLM-based optimizations to agent configuration.
        
        Args:
            config: Base agent configuration
            
        Returns:
            Optimized configuration
        """
        agent_id = config.get('agent_id')
        
        # Check cache first
        config_hash = self._get_config_hash(config)
        if config_hash in self._optimization_cache:
            logger.info(f"Using cached optimizations for agent {agent_id}")
            cached_optimizations = self._optimization_cache[config_hash]
            return self._merge_optimizations(config, cached_optimizations)
        
        try:
            logger.info(f"Generating LLM optimizations for agent {agent_id}")
            
            # Analyze agent domain and purpose
            domain_analysis = self._analyze_agent_domain(config)
            
            # Generate optimized tool descriptions
            tool_optimizations = self._generate_tool_optimizations(config, domain_analysis)
            
            # Generate optimized system prompt
            prompt_optimizations = self._generate_prompt_optimizations(config, domain_analysis)
            
            # Combine all optimizations
            optimizations = {
                'tool_descriptions': tool_optimizations,
                'system_prompt_enhancements': prompt_optimizations,
                'domain_info': domain_analysis,
                'generated_at': datetime.now().isoformat()
            }
            
            # Cache optimizations
            self._optimization_cache[config_hash] = optimizations
            
            # Apply optimizations to config
            optimized_config = self._merge_optimizations(config, optimizations)
            
            logger.info(f"LLM optimizations applied for agent {agent_id}")
            return optimized_config
            
        except Exception as e:
            logger.warning(f"LLM optimization failed, using base config: {str(e)}")
            return config
    
    def _analyze_agent_domain(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent domain and purpose for targeted optimizations."""
        description = config.get('description', '')
        purpose = config.get('purpose', '')
        system_prompt = config.get('system_prompt', '')
        name = config.get('name', '')
        
        # Simple domain detection based on keywords
        text_to_analyze = f"{name} {description} {purpose} {system_prompt}".lower()
        
        domain_keywords = {
            'banking': ['bank', 'account', 'balance', 'transaction', 'financial', 'payment', 'credit', 'debit'],
            'ecommerce': ['shop', 'product', 'order', 'cart', 'purchase', 'inventory', 'customer', 'store'],
            'support': ['help', 'support', 'ticket', 'issue', 'problem', 'assistance', 'customer service'],
            'healthcare': ['health', 'medical', 'patient', 'doctor', 'treatment', 'medicine', 'clinic'],
            'education': ['learn', 'student', 'course', 'education', 'teach', 'school', 'university'],
            'general': []  # fallback
        }
        
        detected_domain = 'general'
        max_matches = 0
        
        for domain, keywords in domain_keywords.items():
            if domain == 'general':
                continue
            matches = sum(1 for keyword in keywords if keyword in text_to_analyze)
            if matches > max_matches:
                max_matches = matches
                detected_domain = domain
        
        # Get MCP tools info
        mcp_tools = []
        if 'api_integration' in config and 'tools' in config['api_integration']:
            mcp_tools = config['api_integration']['tools']
        
        return {
            'detected_domain': detected_domain,
            'confidence': max_matches,
            'mcp_tools_count': len(mcp_tools),
            'has_knowledge_base': bool(config.get('knowledge_base_url')),
            'has_mcp_server': bool(config.get('mcp_server_url'))
        }
    
    def _generate_tool_optimizations(self, config: Dict[str, Any], domain_info: Dict[str, Any]) -> Dict[str, str]:
        """Generate optimized tool descriptions based on domain analysis."""
        domain = domain_info['detected_domain']
        tool_descriptions = {}
        
        # Get MCP tools if available
        if 'api_integration' in config and 'tools' in config['api_integration']:
            tools = config['api_integration']['tools']
            
            # Apply domain-specific optimizations
            if domain == 'banking':
                tool_descriptions.update(self._get_banking_tool_optimizations(tools))
            elif domain == 'ecommerce':
                tool_descriptions.update(self._get_ecommerce_tool_optimizations(tools))
            elif domain == 'support':
                tool_descriptions.update(self._get_support_tool_optimizations(tools))
            else:
                # General optimizations
                tool_descriptions.update(self._get_general_tool_optimizations(tools))
        
        return tool_descriptions
    
    def _get_banking_tool_optimizations(self, tools: list) -> Dict[str, str]:
        """Generate banking-specific tool optimizations."""
        optimizations = {}
        
        for tool in tools:
            name = tool.get('name', '')
            
            if 'balance' in name.lower():
                optimizations[name] = 'Get balance for a specific account using account ID (UUID). IMPORTANT: Only use this if you need balance for a specific account ID. NOTE: getCustomerInfo already includes balances for all customer accounts, so use that instead for general balance inquiries.'
            elif 'customer' in name.lower() and 'info' in name.lower():
                optimizations[name] = 'Get detailed customer information including ALL account balances, account numbers, and account details. This response includes balance information for all accounts, so you typically do NOT need to call getBalance separately.'
            elif 'account' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Must use valid account IDs (UUIDs) obtained from getCustomerInfo or getAccounts.'
            elif 'transfer' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Must use valid account IDs (UUIDs) obtained from getCustomerInfo or getAccounts. Always verify account ownership before transfers.'
            elif 'transaction' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Must use valid account IDs (UUIDs) obtained from getCustomerInfo or getAccounts.'
        
        return optimizations
    
    def _get_ecommerce_tool_optimizations(self, tools: list) -> Dict[str, str]:
        """Generate e-commerce specific tool optimizations."""
        optimizations = {}
        
        for tool in tools:
            name = tool.get('name', '')
            
            if 'product' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Use this to search and display product information to customers.'
            elif 'order' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Always verify customer identity before accessing order information.'
            elif 'cart' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Handle cart operations for customer shopping experience.'
            elif 'inventory' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Check stock availability before confirming orders.'
        
        return optimizations
    
    def _get_support_tool_optimizations(self, tools: list) -> Dict[str, str]:
        """Generate support-specific tool optimizations."""
        optimizations = {}
        
        for tool in tools:
            name = tool.get('name', '')
            
            if 'ticket' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Use for tracking and managing customer support requests.'
            elif 'knowledge' in name.lower():
                optimizations[name] = f'{tool.get("description", "")} Search internal knowledge base before escalating to human agents.'
        
        return optimizations
    
    def _get_general_tool_optimizations(self, tools: list) -> Dict[str, str]:
        """Generate general tool optimizations."""
        optimizations = {}
        
        for tool in tools:
            name = tool.get('name', '')
            description = tool.get('description', '')
            optimizations[name] = f'{description} Follow proper error handling and validation patterns.'
        
        return optimizations
    
    def _generate_prompt_optimizations(self, config: Dict[str, Any], domain_info: Dict[str, Any]) -> str:
        """Generate domain-specific system prompt enhancements."""
        domain = domain_info['detected_domain']
        base_prompt = config.get('system_prompt', '')
        
        domain_guidelines = {
            'banking': """
IMPORTANT BANKING WORKFLOW GUIDELINES:
1. For balance inquiries, use getCustomerInfo which returns ALL account balances - do NOT call getBalance separately
2. getCustomerInfo provides complete account information including balances, account numbers, and account types
3. Only use getBalance if you need balance for a specific account ID that you already have
4. For transactions or transfers, use getCustomerInfo first to get account information, then use the appropriate tools
5. Never use generic strings like 'customer_id' or 'account_id' as actual parameters
6. If you don't have a customer ID, use getAllCustomers first to find the right customer
7. Always verify account ownership before performing any operations
8. Maintain strict confidentiality and follow banking regulations""",
            
            'ecommerce': """
IMPORTANT E-COMMERCE WORKFLOW GUIDELINES:
1. Always check product availability before confirming orders
2. Verify customer identity before accessing order history
3. Use proper cart management throughout the shopping experience
4. Provide clear product information and pricing
5. Handle payment processing securely
6. Offer helpful recommendations based on customer preferences""",
            
            'support': """
IMPORTANT SUPPORT WORKFLOW GUIDELINES:
1. Search knowledge base thoroughly before escalating to human agents
2. Create and track support tickets for complex issues
3. Provide clear, step-by-step troubleshooting instructions
4. Maintain professional and empathetic communication
5. Document resolution steps for future reference
6. Know when to escalate issues appropriately""",
            
            'general': """
IMPORTANT WORKFLOW GUIDELINES:
1. Use available tools efficiently and in the correct sequence
2. Validate inputs before making tool calls
3. Handle errors gracefully and provide helpful feedback
4. Maintain professional communication at all times"""
        }
        
        return domain_guidelines.get(domain, domain_guidelines['general'])
    
    def _merge_optimizations(self, base_config: Dict[str, Any], optimizations: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LLM optimizations into base configuration."""
        optimized_config = base_config.copy()
        
        # Enhance system prompt
        if 'system_prompt_enhancements' in optimizations:
            current_prompt = optimized_config.get('system_prompt', '')
            enhanced_prompt = current_prompt + '\n\n' + optimizations['system_prompt_enhancements']
            optimized_config['system_prompt'] = enhanced_prompt.strip()
        
        # Store tool optimizations for use by mcp_tool.py
        if 'tool_descriptions' in optimizations:
            optimized_config['_tool_optimizations'] = optimizations['tool_descriptions']
        
        # Store domain info for debugging
        if 'domain_info' in optimizations:
            optimized_config['_domain_info'] = optimizations['domain_info']
        
        return optimized_config
    
    def _get_config_hash(self, config: Dict[str, Any]) -> str:
        """Generate a hash of configuration for caching purposes."""
        import hashlib
        
        # Create a simplified config for hashing (exclude runtime vars)
        hash_config = {
            'description': config.get('description', ''),
            'purpose': config.get('purpose', ''),
            'system_prompt': config.get('system_prompt', ''),
            'mcp_tools': len(config.get('api_integration', {}).get('tools', [])),
            'has_knowledge_base': bool(config.get('knowledge_base_url'))
        }
        
        config_str = json.dumps(hash_config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()


# Global instance for easy import
config_loader = AgentConfigLoader()


def load_agent_config(agent_id: str) -> Dict[str, Any]:
    """
    Convenience function to load agent configuration.
    
    Args:
        agent_id: Agent ID to load
        
    Returns:
        Optimized agent configuration
    """
    return config_loader.load_agent_config(agent_id)