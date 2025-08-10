"""Message parser for converting raw Dapr pub/sub messages to structured conversation data."""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from schemas import ConversationMessage, MessageType


class MessageParser:
    """Parses raw Dapr pub/sub messages into structured conversation data."""
    
    # Agent emojis for display
    AGENT_EMOJIS = {
        "frodo": "🧙‍♂️",
        "gandalf": "🧙‍♂️", 
        "legolas": "🏹",
        "randomorchestrator": "🎲",
        "roundrobinorchestrator": "🔄",
        "llmorchestrator": "🧠"
    }
    
    def __init__(self):
        self.workflow_sessions = {}  # Track active workflows
    
    def parse_message(self, topic: str, data: Dict[str, Any]) -> Optional[ConversationMessage]:
        """Parse a raw pub/sub message into a ConversationMessage."""
        try:
            # Determine message type from topic and data structure
            message_type = self._determine_message_type(topic, data)
            if not message_type:
                return None
            
            # Extract workflow ID (try multiple possible fields)
            workflow_id = self._extract_workflow_id(data)
            
            # Extract agent information
            agent_name, agent_role = self._extract_agent_info(topic, data)
            
            # Extract orchestrator information
            orchestrator = self._extract_orchestrator(topic, data)
            
            # Extract content
            content = self._extract_content(data, message_type)
            
            # Generate unique message ID
            message_id = str(uuid.uuid4())
            
            # Track turn number for this workflow
            turn_number = self._get_turn_number(workflow_id)
            
            return ConversationMessage(
                id=message_id,
                workflow_id=workflow_id,
                timestamp=datetime.utcnow(),
                message_type=message_type,
                agent_name=agent_name,
                agent_role=agent_role,
                orchestrator=orchestrator,
                content=content,
                turn_number=turn_number,
                topic=topic,
                raw_data=data
            )
            
        except Exception as e:
            print(f"Error parsing message from topic {topic}: {e}")
            return None
    
    def _determine_message_type(self, topic: str, data: Dict[str, Any]) -> Optional[MessageType]:
        """Determine the type of message based on topic and content."""
        topic_lower = topic.lower()
        
        # Check if it's an orchestrator action
        if any(orchestrator in topic_lower for orchestrator in ["random", "roundrobin", "llm"]):
            if "workflow" in str(data).lower():
                return MessageType.WORKFLOW_START
            return MessageType.ORCHESTRATOR_ACTION
        
        # Check for agent messages
        if any(agent in topic_lower for agent in ["frodo", "gandalf", "legolas"]):
            # Look for response indicators
            if "response" in str(data).lower() or "completion" in str(data).lower():
                return MessageType.AGENT_RESPONSE
            else:
                return MessageType.AGENT_REQUEST
        
        # Look for workflow lifecycle events
        if "start" in str(data).lower() or "begin" in str(data).lower():
            return MessageType.WORKFLOW_START
        elif "complete" in str(data).lower() or "end" in str(data).lower():
            return MessageType.WORKFLOW_END
        
        # Default to agent response if we can't determine
        return MessageType.AGENT_RESPONSE
    
    def _extract_workflow_id(self, data: Dict[str, Any]) -> str:
        """Extract workflow ID from message data."""
        # Try common workflow ID fields
        possible_fields = ["workflow_id", "workflowId", "instanceId", "id", "session_id"]
        
        for field in possible_fields:
            if field in data and data[field]:
                return str(data[field])
        
        # Look in nested data structures
        if "data" in data:
            for field in possible_fields:
                if field in data["data"] and data["data"][field]:
                    return str(data["data"][field])
        
        # Generate a default workflow ID based on timestamp
        return f"workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    def _extract_agent_info(self, topic: str, data: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Extract agent name and role from topic and data."""
        topic_lower = topic.lower()
        
        # Map topic names to agent info
        agent_mappings = {
            "frodo": ("Frodo", "Hobbit"),
            "gandalf": ("Gandalf", "Wizard"),
            "legolas": ("Legolas", "Elf")
        }
        
        for agent_key, (name, role) in agent_mappings.items():
            if agent_key in topic_lower:
                return name, role
        
        # Try to extract from message data
        if "agent" in data:
            agent_data = data["agent"]
            if isinstance(agent_data, dict):
                name = agent_data.get("name") or agent_data.get("agent_name")
                role = agent_data.get("role") or agent_data.get("agent_role")
                return name, role
        
        # Check for name/role in top-level data
        name = data.get("name") or data.get("agent_name")
        role = data.get("role") or data.get("agent_role")
        
        return name, role
    
    def _extract_orchestrator(self, topic: str, data: Dict[str, Any]) -> Optional[str]:
        """Extract orchestrator information."""
        topic_lower = topic.lower()
        
        orchestrator_mappings = {
            "random": "RandomOrchestrator",
            "roundrobin": "RoundRobinOrchestrator", 
            "llm": "LLMOrchestrator"
        }
        
        for key, name in orchestrator_mappings.items():
            if key in topic_lower:
                return name
        
        # Check data for orchestrator info
        return data.get("orchestrator") or data.get("orchestrator_name")
    
    def _extract_content(self, data: Dict[str, Any], message_type: MessageType) -> str:
        """Extract the main content/message from the data."""
        # Try common content fields
        content_fields = [
            "content", "message", "text", "response", "request", 
            "task", "action", "description", "prompt"
        ]
        
        for field in content_fields:
            if field in data and data[field]:
                content = data[field]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict):
                    # Try to extract text from nested structure
                    return str(content.get("content", content))
                else:
                    return str(content)
        
        # Look in nested data
        if "data" in data:
            for field in content_fields:
                if field in data["data"] and data["data"][field]:
                    return str(data["data"][field])
        
        # If no content found, create a summary based on message type
        if message_type == MessageType.WORKFLOW_START:
            return "Workflow started"
        elif message_type == MessageType.WORKFLOW_END:
            return "Workflow completed"
        elif message_type == MessageType.ORCHESTRATOR_ACTION:
            return "Orchestrator action"
        else:
            return "Agent message"
    
    def _get_turn_number(self, workflow_id: str) -> int:
        """Get and increment turn number for a workflow."""
        if workflow_id not in self.workflow_sessions:
            self.workflow_sessions[workflow_id] = 0
        
        self.workflow_sessions[workflow_id] += 1
        return self.workflow_sessions[workflow_id]
    
    def get_agent_emoji(self, agent_name: str) -> str:
        """Get emoji for agent display."""
        if not agent_name:
            return "🤖"
        return self.AGENT_EMOJIS.get(agent_name.lower(), "🤖")