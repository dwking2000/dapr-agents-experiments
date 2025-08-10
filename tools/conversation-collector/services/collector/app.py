"""ConversationCollector - Dapr service for monitoring agent conversations."""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dapr.clients import DaprClient
import uvicorn

from schemas import (
    ConversationMessage, ConversationSummary, GetConversationsRequest,
    GetConversationsResponse, MessageType
)
from parser import MessageParser


class ConversationCollector:
    """Core service for collecting and managing agent conversations."""
    
    def __init__(self):
        self.app = FastAPI(title="ConversationCollector", version="1.0.0")
        self.parser = MessageParser()
        
        # Storage
        self.state_store_name = "conversationstatestore"
        self.conversations_key = "conversations"
        self.summaries_key = "conversation_summaries"
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        
        # Configure CORS for web clients
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
        self._setup_static_files()
        self._setup_subscriptions()
    
    def _setup_routes(self):
        """Setup REST API routes."""
        
        @self.app.get("/")
        async def root():
            """Serve the main web UI."""
            return FileResponse("clients/web/index.html")
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "service": "ConversationCollector"}
        
        @self.app.get("/conversations", response_model=GetConversationsResponse)
        async def get_conversations(
            workflow_id: Optional[str] = None,
            limit: int = 100,
            offset: int = 0,
            message_type: Optional[str] = None,
            agent_name: Optional[str] = None
        ):
            """Retrieve conversation messages with filtering."""
            try:
                # Get conversations from state store
                with DaprClient() as dapr:
                    result = dapr.get_state(
                        store_name=self.state_store_name,
                        key=self.conversations_key
                    )
                    
                    if not result.data:
                        return GetConversationsResponse(
                            messages=[], total_count=0, has_more=False
                        )
                    
                    all_conversations = json.loads(result.data)
                    messages = [ConversationMessage(**msg) for msg in all_conversations]
                    
                    # Apply filters
                    filtered_messages = self._filter_messages(
                        messages, workflow_id, message_type, agent_name
                    )
                    
                    # Sort by timestamp (newest first)
                    filtered_messages.sort(key=lambda x: x.timestamp, reverse=True)
                    
                    # Apply pagination
                    total_count = len(filtered_messages)
                    paginated_messages = filtered_messages[offset:offset + limit]
                    has_more = offset + limit < total_count
                    
                    return GetConversationsResponse(
                        messages=paginated_messages,
                        total_count=total_count,
                        has_more=has_more
                    )
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/conversations/latest")
        async def get_latest_conversations(limit: int = 10):
            """Get the most recent conversation messages."""
            return await get_conversations(limit=limit, offset=0)
        
        @self.app.get("/conversations/summaries")
        async def get_conversation_summaries():
            """Get summaries of all conversation workflows."""
            try:
                with DaprClient() as dapr:
                    result = dapr.get_state(
                        store_name=self.state_store_name,
                        key=self.summaries_key
                    )
                    
                    if not result.data:
                        return []
                    
                    summaries_data = json.loads(result.data)
                    return [ConversationSummary(**summary) for summary in summaries_data]
                    
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/conversations/live")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time conversation updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                # Send recent messages to new connection
                recent_response = await get_latest_conversations(limit=50)
                await websocket.send_json({
                    "type": "initial_messages",
                    "messages": [msg.dict() for msg in recent_response.messages]
                })
                
                # Keep connection alive
                while True:
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                print(f"WebSocket error: {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    def _setup_static_files(self):
        """Setup static file serving for web UI."""
        # Mount static files (CSS, JS, etc.)
        self.app.mount("/static", StaticFiles(directory="clients/web", html=True), name="static")
    
    def _setup_subscriptions(self):
        """Setup Dapr pub/sub subscriptions for agent topics."""
        
        # Subscribe to all agent topics  
        agent_topics = ["Frodo", "Gandalf", "Legolas"]
        orchestrator_topics = ["RandomOrchestrator", "RoundRobinOrchestrator", "LLMOrchestrator"]
        
        all_topics = agent_topics + orchestrator_topics
        
        # Register subscription endpoints
        for topic in all_topics:
            route_path = f"/handle-{topic.lower()}"
            self.app.post(route_path)(self._create_message_handler(topic))
        
        # Register Dapr subscriptions endpoint
        @self.app.get("/dapr/subscribe")
        async def subscribe():
            """Return subscription configuration for Dapr."""
            subscriptions = []
            for topic in all_topics:
                subscriptions.append({
                    "pubsubname": "messagepubsub",
                    "topic": topic,
                    "route": f"/handle-{topic.lower()}"
                })
            return subscriptions
    
    def _create_message_handler(self, topic: str):
        """Create a message handler for a specific topic."""
        async def handler(request: Request):
            """Handle incoming pub/sub message."""
            try:
                # Get message data from request
                event_data = await request.json()
                print(f"Received message on topic {topic}: {event_data}")
                
                # Extract data from the Dapr event structure
                if "data" in event_data:
                    message_data = event_data["data"]
                else:
                    message_data = event_data
                
                # Parse the message
                parsed_message = self.parser.parse_message(topic, message_data)
                if not parsed_message:
                    print(f"Could not parse message from topic {topic}")
                    return {"status": "ignored"}
                
                # Store the message
                await self._store_message(parsed_message)
                
                # Send to WebSocket clients
                await self._broadcast_to_websockets(parsed_message)
                
                print(f"Processed message: {parsed_message.agent_name}: {parsed_message.content[:100]}...")
                
                return {"status": "success"}
                
            except Exception as e:
                print(f"Error handling message from topic {topic}: {e}")
                return {"status": "error", "message": str(e)}
        
        return handler
    
    async def _store_message(self, message: ConversationMessage):
        """Store a conversation message in the state store."""
        try:
            with DaprClient() as dapr:
                # Get existing conversations
                result = dapr.get_state(
                    store_name=self.state_store_name,
                    key=self.conversations_key
                )
                
                if result.data:
                    conversations = json.loads(result.data)
                else:
                    conversations = []
                
                # Add new message
                conversations.append(message.dict())
                
                # Keep only last 1000 messages to prevent unbounded growth
                if len(conversations) > 1000:
                    conversations = conversations[-1000:]
                
                # Store back
                dapr.save_state(
                    store_name=self.state_store_name,
                    key=self.conversations_key,
                    value=json.dumps(conversations, default=str)
                )
                
                # Update conversation summary
                await self._update_conversation_summary(message)
                
        except Exception as e:
            print(f"Error storing message: {e}")
    
    async def _update_conversation_summary(self, message: ConversationMessage):
        """Update conversation summary statistics."""
        try:
            with DaprClient() as dapr:
                # Get existing summaries
                result = dapr.get_state(
                    store_name=self.state_store_name,
                    key=self.summaries_key
                )
                
                if result.data:
                    summaries_data = json.loads(result.data)
                    summaries = {s["workflow_id"]: s for s in summaries_data}
                else:
                    summaries = {}
                
                # Update or create summary for this workflow
                workflow_id = message.workflow_id
                
                if workflow_id not in summaries:
                    summaries[workflow_id] = {
                        "workflow_id": workflow_id,
                        "start_time": message.timestamp.isoformat(),
                        "end_time": None,
                        "orchestrator_type": message.orchestrator,
                        "agent_names": [],
                        "message_count": 0,
                        "status": "active"
                    }
                
                summary = summaries[workflow_id]
                summary["message_count"] += 1
                
                # Add agent name if new
                if message.agent_name and message.agent_name not in summary["agent_names"]:
                    summary["agent_names"].append(message.agent_name)
                
                # Update end time and status for workflow end messages
                if message.message_type == MessageType.WORKFLOW_END:
                    summary["end_time"] = message.timestamp.isoformat()
                    summary["status"] = "completed"
                
                # Store back
                dapr.save_state(
                    store_name=self.state_store_name,
                    key=self.summaries_key,
                    value=json.dumps(list(summaries.values()), default=str)
                )
                
        except Exception as e:
            print(f"Error updating conversation summary: {e}")
    
    async def _broadcast_to_websockets(self, message: ConversationMessage):
        """Broadcast new message to all WebSocket connections."""
        if not self.websocket_connections:
            return
        
        message_data = {
            "type": "new_message",
            "message": message.dict()
        }
        
        # Send to all connected WebSocket clients
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message_data)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)
    
    def _filter_messages(
        self, 
        messages: List[ConversationMessage],
        workflow_id: Optional[str] = None,
        message_type: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> List[ConversationMessage]:
        """Apply filters to messages."""
        filtered = messages
        
        if workflow_id:
            filtered = [msg for msg in filtered if msg.workflow_id == workflow_id]
        
        if message_type:
            filtered = [msg for msg in filtered if msg.message_type == message_type]
        
        if agent_name:
            filtered = [msg for msg in filtered if msg.agent_name == agent_name]
        
        return filtered


def create_app():
    """Create and configure the ConversationCollector app."""
    collector = ConversationCollector()
    return collector.app


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    app = create_app()
    
    # Run with Dapr sidecar
    port = int(os.getenv("APP_PORT", 8005))
    
    print(f"Starting ConversationCollector on port {port}")
    print("Subscribing to topics: Frodo, Gandalf, Legolas, RandomOrchestrator, RoundRobinOrchestrator, LLMOrchestrator")
    
    uvicorn.run(app, host="0.0.0.0", port=port)